from abc import ABC
from dataclasses import dataclass, field
import re
from typing import List, Set, Tuple
import xml.etree.ElementTree as ET

import util.logger
logger = util.logger.get_logger(__name__)

class SourceSink(ABC):
    def source_count(self):
        pass
    def sink_count(self):
        pass

    def remove_sources(self):
        pass 

    def write_to_file(self, target_file_path: str):
        pass

    # def from_file(self, target_file_path: str):
    #     pass

    @classmethod
    def source_sink_signatures_from_txt(file_path: str) -> Tuple[List['MethodSignature'], List['MethodSignature']]:
        
        source_signatures: List['MethodSignature'] = []
        sink_signatures: List['MethodSignature'] = []

        with open(file_path, 'r') as file:
            lines = file.readlines()
            sink_signatures: List[MethodSignature] = []
            for line in lines:
                """
    Example line: 
    <javax.servlet.ServletRequest: java.lang.String getParameter(java.lang.String)> -> _SOURCE_
                """
                if line.startswith('%'):
                    # '%' are used as comments
                    continue

                elif line.strip().endswith("-> _SINK_"):
                    line = line.strip()
                    line = line.replace("-> _SINK_", "")

                    # Weird case in FD default Source/Sink list
                    if line.strip().endswith(" android.permission.SEND_SMS"):
                        line = line.strip()
                        line = line.replace(" android.permission.SEND_SMS", "")

                    sink_signatures.append(MethodSignature.from_java_style_signature(line))

                elif line.strip().endswith("-> _SOURCE_"):
                    line = line.strip()
                    line = line.replace("-> _SOURCE_", "")
                    line = line.strip()
                    source_signatures.append(MethodSignature.from_java_style_signature(line))

        return source_signatures, sink_signatures

@dataclass
class SourceSinkSignatures(SourceSink):
    source_signatures: Set['MethodSignature'] = field(default_factory=set)
    sink_signatures: Set['MethodSignature'] = field(default_factory=set)

    def source_count(self):
        return len(self.source_signatures)
    
    def sink_count(self):
        return len(self.sink_signatures)
    
    def write_to_file(self, target_file_path: str):
        sources = [str(signature) for signature in self.source_signatures]
        sinks = [str(signature) for signature in self.sink_signatures]
        source_sink_formatted = format_source_sinks(sources, sinks)

        with open(target_file_path, 'w') as file:
            file.write(source_sink_formatted)
        

    @classmethod
    def from_file(file_path: str) -> 'SourceSinkSignatures':
        # def add_sinks_from_file(self, file_path):
        result = SourceSinkSignatures()

        source_list, sink_list = SourceSink.source_sink_signatures_from_txt(file_path)
        result.source_signatures, result.sink_signatures = set(source_list), set(sink_list)
        return result

    def set_minus(self, other_source_sink: 'SourceSinkSignatures'):
        self.source_signatures - other_source_sink.source_signatures
        self.sink_signatures - other_source_sink.sink_signatures

    def union(self, other_source_sink: 'SourceSinkSignatures'):
        self.source_signatures = self.source_signatures.union(other_source_sink.source_signatures)
        self.sink_signatures = self.sink_signatures.union(other_source_sink.sink_signatures)
        


        

class SourceSinkXML(SourceSink):
    """
    Class representing Flowdroid's new source/sink xml format.
    """

    tree: ET.ElementTree
    source_count: int
    sink_count: int

    def __init__(self):
        root = ET.Element("sinkSources", attrib={})
        self.tree = ET.ElementTree(element=root)

        self.category_element = ET.Element("category", attrib={"id": "NO_CATEGORY"})
        root.append(self.category_element)

        self.source_count = 0
        self.sink_count = 0

    # TODO: this different flavours of return/arg/base sources shouldn't be exposed to clients of SourceSink or smthng

    def add_return_source(self, signature: 'MethodSignature'):
        method_element = self._get_matching_method(signature)

        return_element = self._get_return_child(signature, method_element)

        self._add_starred_access_path(return_element, is_source=True)

    def add_arg_source(self, signature: 'MethodSignature', arg_index: int):
        method_element = self._get_matching_method(signature)

        param_element = self._get_param_child(signature, method_element, arg_index)

        self._add_starred_access_path(param_element, is_source=True)

    def add_base_source(self, signature: 'MethodSignature'):
        method_element = self._get_matching_method(signature)

        base_element = self._get_base_child(signature, method_element)

        self._add_starred_access_path(base_element, is_source=True)

    def add_arg_sink(self, signature: 'MethodSignature', arg_index: int):
        method_element = self._get_matching_method(signature)

        param_element = self._get_param_child(signature, method_element, arg_index)

        self._add_starred_access_path(param_element, is_sink=True)
        self.sink_count += 1

    def remove_return_sources(self, signatures: List['MethodSignature']):
        for signature in signatures:
            self.remove_return_source(signature)

    def remove_return_source(self, signature: 'MethodSignature'):
        if not self._has_matching_method(signature):
            return

        method_element = self._get_matching_method(signature)
        if not self._has_return_child(method_element):
            return

        return_element = self._get_return_child(signature, method_element)

        access_paths = self._get_access_paths(return_element)
        for access_path in access_paths:
            if not access_path.attrib["isSource"] == "true":
                continue

            if access_path.attrib["isSink"] == "true":
                access_path.attrib["isSource"] = "false"
            else:
                return_element.remove(access_path)
            self.source_count -= 1

        # If we removed the last access path in the return, remove the return element
        access_paths = self._get_access_paths(return_element)
        if len(access_paths) == 0:
            method_element.remove(return_element)

        # If we removed the last child of the method, remove the method
        children = method_element.findall("./*")
        if len(children) is None:
            self.category_element.remove(method_element)

    def add_sinks_from_file(self, file_path):
        _, sink_signatures = SourceSink.source_sink_signatures_from_txt(file_path)

        for sink_signature in sink_signatures:
            for index in range(len(sink_signature.arg_types)):
                self.add_arg_sink(sink_signature, index)

    def write_to_file(self, target_file_path: str):
        self.tree.write(target_file_path)

    def _has_matching_method(self, signature: 'MethodSignature') -> bool:
        # Sometimes signatures include single quotes, which messes up the query system.
        signature_string = signature.signature
        if signature_string.__contains__("'"):
            signature_string.replace("'", "")

        method_element = self.category_element.find(
            f"./method[@signature='{signature_string}']")
        return method_element is not None

    def _get_matching_method(self, signature: 'MethodSignature') -> ET.Element:
        """
        Find a method from the direct children of category_element whose signature
        matches the input exactly. If no such child exists, create and add one.
        """

        # Sometimes signatures include single quotes, which messes up the query system.
        signature_string = signature.signature
        if signature_string.__contains__("'"):
            signature_string.replace("'", "")

        method_element = self.category_element.find(
            f"./method[@signature='{signature_string}']")
        if method_element is None:
            method_element = ET.Element("method",
                                        attrib={"signature": signature_string})
            self.category_element.append(method_element)

        return method_element

    def _has_return_child(self, method_element: ET.Element):
        return_element = method_element.find("./return")
        return not return_element is None

    def _get_return_child(self, signature: 'MethodSignature', method_element: ET.Element) -> 'ET.Element':
        """
        Find the return Element from the direct children of the method_element input.
        If no such child exists, create one and add it as a child.
        """
        return_element = method_element.find("./return")
        if return_element is None:
            return_element = ET.Element("return", attrib={"type": signature.return_type})
            method_element.append(return_element)

        return return_element

    def _get_base_child(self, signature: 'MethodSignature',
                        method_element: ET.Element) -> ET.Element:
        """
        Find the base Element from the direct children of the method_element input.
        If no such child exists, create one and add it as a child.
        """
        base_element = method_element.find("./base")
        if base_element is None:
            base_element = ET.Element("base", attrib={"type": signature.base_type})
            method_element.append(base_element)

        return base_element

    def _get_param_child(self, signature: 'MethodSignature',
                         method_element: ET.Element, arg_index: int) -> ET.Element:
        """
        Find a param Element from the direct children of the method_element input whose index
        matches the input. If no such child exists, create one and add it as a child.
        """
        param_element = method_element.find(f"./param[@index='{str(arg_index)}']")
        if param_element is None:
            param_element = ET.Element("param",
                                       attrib={"index": str(arg_index),
                                               "type": signature.arg_types[arg_index]})
            method_element.append(param_element)

        return param_element

    def _get_access_paths(self, element: ET.Element) -> List[ET.Element]:
        access_path_elements = element.findall("./accessPath")
        if access_path_elements is None:
            return []
        else:
            return access_path_elements

    def _add_starred_access_path(self, element: ET.Element, is_source=False,
                                 is_sink=False):
        """
        Modify the accessPath children of the given element such that there is 1
        empty accessPath element for the starred source and/or sink.
        """
        if not is_source and not is_sink:
            # No need to add any accessPaths in this case
            return

        # todo: when there are actual access paths with path elements, this should
        #  remove any access_paths that are subsumed by the one being added. This should update the # of
        #  sources/sinks as well

        access_path_elements = element.findall("./accessPath")
        if len(access_path_elements) > 1:
            raise AssertionError("Not expecting multiple access paths in an element "
                                 "yet.")
        elif len(access_path_elements) == 1:
            access_path_element = access_path_elements[0]
        else:  # there are no access path element children
            access_path_element = ET.Element("accessPath",
                                             attrib={"isSource": "false",
                                                     "isSink": "false"})
            element.append(access_path_element)

        if is_source:
            if access_path_element.attrib['isSource'] != "true":
                access_path_element.attrib['isSource'] = "true"
                self.source_count += 1

        if is_sink:
            if access_path_element.attrib['isSink'] != "true":
                access_path_element.attrib['isSink'] = "true"
                self.sink_count += 1


# class MethodSignature:
#     """Model class for a Flowdroid Method signature of the style of the old
#     Source/Sink text file."""
#
#     signature: str
#     base_type: str
#     return_type: str
#     method_name: str
#     params: List[str]
#
#     @staticmethod
#     def from_signature(signature: str) -> 'MethodSignature':


class MethodSignature:
    # TODO: chagne name to JavaStyleMethodSignature?
    # Stores a string of the form
    # <[full package name]: [return type] [method name]([arg types,])>
    signature: str
    base_type: str
    return_type: str
    method_name: str
    arg_types: List[str]

    def __init__(self):
        self.signature = ""
        self.base_type = ""
        self.return_type = ""
        self.method_name = ""
        self.arg_types = []

    def __eq__(self, other):
        if not isinstance(other, MethodSignature):
            return False

        if len(self.arg_types) != len(other.arg_types):
            return False

        return (all([self.arg_types[i] == other.arg_types[i]
                     for i in range(len(self.arg_types))])
                and self.base_type == other.base_type
                and self.return_type == other.return_type
                and self.method_name == other.method_name
                and self.signature == other.signature)

    def __hash__(self):
        arg_types_hash_sum = sum([hash(item) for item in self.arg_types])
        return hash((self.base_type, self.return_type, self.method_name,
                     arg_types_hash_sum))
    
    def __str__(self) -> str:
        return f"<{self.base_type}: {self.return_type} {self.method_name}({",".join(self.arg_types)})>"

    # def get_source_string(self):
    #     # Assumes string should be of the form
    #     # <[full package name]: [return type] [method name]([arg types,])> -> _SOURCE_
    #     return f"<{self.base_type}: {self.return_type} " \
    #            f"{self.method_name}({','.join(self.arg_types)})> -> _SOURCE_\n"

    @classmethod
    def from_source_string(cls, line: str) -> "MethodSignature":
        """
        Parse the given string into a Source Model Object, and return the
        model object.
        :param line: String from sources/sinks file containing source
        :return: FlowdroidSourceModel
        """
        # Assumes string should be of the form
        # <[full package name]: [return type] [method name]([arg types,])> -> _SOURCE_
        # Example:
        # <javax.servlet.ServletRequest: java.lang.String getParameter(java.lang.String)> -> _SOURCE_

        line = line.strip()
        line_chunks = line.split(" -> ")
        assert len(line_chunks) == 2
        assert line_chunks[1] == "_SOURCE_"

        signature = line_chunks[0]
        # a small handful of lines break the above pattern. Example:
        # <android.telephony.TelephonyManager: java.lang.String getDeviceId()> android.permission.READ_PHONE_STATE -> _SOURCE_
        if signature.strip().endswith(
                "android.permission.READ_PHONE_STATE"):
            # TODO: need to look into flowdroid to see why this case comes up/if it
            #  has important semantics.
            function_chunks = signature.strip()[:-len(
                "android.permission.READ_PHONE_STATE")].strip()

        return cls.from_java_style_signature(signature)
        # signature = line_chunks[0]
        #
        # # a small handful of lines break the above pattern. Example:
        # # <android.telephony.TelephonyManager: java.lang.String getDeviceId()> android.permission.READ_PHONE_STATE -> _SOURCE_
        # if signature.strip().endswith(
        #         "android.permission.READ_PHONE_STATE"):
        #     # TODO: need to look into flowdroid to see why this case comes up/if it
        #     #  has important semantics.
        #     signature = signature.strip()[:-len(
        #         "android.permission.READ_PHONE_STATE")].strip()
        # signature = signature[
        #                   1:-1]  # take off the enclosing '<' and '>'
        # base_type, return_type, signature = signature.split()
        # base_type = base_type[
        #                     :-1]  # take off the ':' at the end
        # method_name = signature.split(')')[0]
        # # get the string after the '(' and take off the ')' at the end
        # if '(' in signature:
        #     signature_args = signature.split('(')[1]
        #     if signature_args.endswith(')'):
        #         signature_args = signature_args[:-1]
        #     signature_args = signature_args.split(',')
        # else:
        #     # Case where function name just has ')' after, but no '()'
        #     # this may be a bug from flowdroid? If there are semantics associated
        #     # with this case, they are not capture here.
        #     signature_args = []
        #
        # # put results in model object
        # result = FlowdroidSourceModel()
        # result.base_type = base_type
        # result.return_type = return_type
        # result.method_name = method_name
        # result.arg_types = signature_args
        #
        # return result

    @classmethod
    def from_java_style_signature(cls, signature: str) -> 'MethodSignature':
        # Example:
        # "<android.content.Context: void sendBroadcast(android.content.Intent)>"
        re_result = re.search(r"<(.+): (.+) (.+)\((.*)\)>", signature)
        if re_result is None:
            # Sometimes sources are missing the left paren
            re_result = re.search(r"<(.+): (.+) (.+)\)>", signature)
            if re_result is None:
                raise AssertionError("Signature did not parse correctly: " + signature)
            base_type, return_type, method_name, arg_types_string = re_result.group(
                1), re_result.group(2), re_result.group(3), ""
        else:
            base_type, return_type, method_name, arg_types_string = re_result.group(
                1), re_result.group(2), re_result.group(3), re_result.group(4)

        if arg_types_string == '':
            arg_types = []
        else:
            arg_types = arg_types_string.split(',')

        # put results in model object
        result = MethodSignature()
        result.signature = signature
        result.base_type = base_type
        result.return_type = return_type
        result.method_name = method_name
        result.arg_types = arg_types

        return result

def format_source_sink_signatures(source_signatures: List[MethodSignature], sink_signatures: List[MethodSignature]):
    sources = [signature.get_source_string() for signature in source_signatures]

def format_source_sinks(sources: List[str], sinks: List[str]) -> str:
    """
    Format lists of source/sink signatures into a string, ready to be written to a file. Mimic old style FlowDroid .txt source/sink files.

        Sample for flowdroid default sources and sinks
        <org.apache.xalan.xsltc.runtime.BasisLibrary: java.lang.String replace(java.lang.String,java.lang.String,java.lang.String[])> -> _SINK_
        <org.springframework.mock.web.portlet.MockPortletRequest: void setParameters(java.util.Map)> -> _SINK_
    """

    result = ""
    for source in sources:
        result += f"{source} -> _SOURCE_\n"

    for sink in sinks:
        result += f"{sink} -> _SINK_\n"

    return result


def test_single_source_sink():
    source_sinks = SourceSinkXML()

    source = MethodSignature.from_java_style_signature(
        "<android.os.Bundle: java.lang.String getString(java.lang.String)>")
    sink = MethodSignature.from_java_style_signature(
        "<android.telephony.SmsManager: void sendTextMessage(java.lang.String,java.lang.String,java.lang.String,android.app.PendingIntent,android.app.PendingIntent)>")

    source_sinks.add_return_source(source)
    source_sinks.add_arg_sink(sink, 2)

    result_file = "data/sources-and-sinks/OnlyTelephony-xml-automated-test.xml"

    source_sinks.write_to_file(result_file)


def test_adding_sinks_from_file():
    default_source_sink_file_path = "data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"

    source_sinks = SourceSinkXML()

    source_sinks.add_sinks_from_file(default_source_sink_file_path)

    result_file = "data/sources-and-sinks/default-sinks-xml-automated-test.xml"
    source_sinks.write_to_file(result_file)


if __name__ == '__main__':
    test_adding_sinks_from_file()


def source_sink_file_ssgpl_string() -> str:
    # TODO: this should probably be in the Data folder with a README
    sources = ["android.widget.EditText: android.text.Editable getText()"]
    sinks = ["com.squareup.okhttp.Call: com.squareup.okhttp.Response execute()",
             "cz.msebera.android.httpclient.client.HttpClient: cz.msebera.android.httpclient.HttpResponse execute (cz.msebera.android.httpclient.client.methods.HttpUriRequest)",
             "java.io.OutputStreamWriter: void write(java.lang.String)",
             "java.io.PrintWriter: void write(java.lang.String)",
             "java.net.HttpURLConnection: int getResponseCode()",
             "java.util.zip.GZIPOutputStream: void write(byte[])",
             "okhttp3.Call: okhttp3.Response execute()",
             "okhttp3.Call: void enqueue(okhttp3.Callback)",
             "org.apache.http.client.HttpClient: org.apache.http.HttpResponse execute(org.apache.http.client.methods.HttpUriRequest)",
             "org.apache.http.client.HttpClient: org.apache.http.HttpResponse execute(org.apache.http.client.methods.HttpUriRequest, org.apache.http.protocol.HttpContext)",
             "org.apache.http.impl.client.DefaultHttpClient: org.apache.http.HttpResponse execute(org.apache.http.client. methods.HttpUriRequest)"
             ]
    
    sources = [f"<{item}>" for item in sources]
    sinks = [f"<{item}>" for item in sinks]
        

    return format_source_sinks(sources, sinks)


def create_source_sink_file_ssgpl(file_path):
    contents = source_sink_file_ssgpl_string()
    with open(file_path, 'w') as file:
        file.write(contents)


def source_sink_file_ssbench_string() -> str:
    # TODO: This should probably be in the Data folder with a README
    sources = ["android.telephony.TelephonyManager: java.lang.String getDeviceId()",
               "android.telephony.TelephonyManager: java.lang.String getSimSerialNumber()",
               "android.location.Location: double getLatitude()",
               "android.location.Location: double getLongitude()",
               "android.telephony.TelephonyManager: java.lang.String getSubscriberId()"
               ]

    sinks = ["android.telephony.SmsManager: void sendTextMessage(java.lang.String,java.lang.String,java.lang.String, android.app.PendingIntent,android.app.PendingIntent)",
             "android.util.Log: int i(java.lang.String,java.lang.String)",
             "android.util.Log: int e(java.lang.String,java.lang.String)",
             "android.util.Log: int v(java.lang.String,java.lang.String)",
             "android.util.Log: int d(java.lang.String,java.lang.String)",
             "java.lang.ProcessBuilder: java.lang.Process start()",
             "android.app.Activity: void startActivityForResult(android.content.Intent,int)",
             "android.app.Activity: void setResult(int,android.content.Intent)",
             "android.app.Activity: void startActivity(android.content.Intent)",
             "java.net.URL: java.net.URLConnection openConnection()",
             "android.content.ContextWrapper: void sendBroadcast(android.content.Intent)",
             ]

    sources = [f"<{item}>" for item in sources]
    sinks = [f"<{item}>" for item in sinks]

    return format_source_sinks(sources, sinks)


def create_source_sink_file_ssbench(file_path):
    contents = source_sink_file_ssbench_string()
    with open(file_path, 'w') as file:
        file.write(contents)
