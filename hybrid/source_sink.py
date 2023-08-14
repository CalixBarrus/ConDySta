import re
from typing import List
import xml.etree.ElementTree as ET

from util import logger

logger = logger.get_logger('hybrid', 'source_sink')


class SourceSinkXML:
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

    def add_return_source(self, signature: 'MethodSignature'):
        method_element = self._get_matching_method(signature)

        return_element = ET.Element("return",
                                    attrib={"type": signature.return_type})
        method_element.append(return_element)

        self._add_starred_access_path(return_element, is_source=True)
        self.source_count += 1


    def add_arg_source(self, signature: 'MethodSignature', arg_index: int):
        method_element = self._get_matching_method(signature)

        return_element = ET.Element("return",
                                    attrib={"type": signature.return_type})
        method_element.append(return_element)

        param_element = self._get_matching_param(signature, method_element, arg_index)

        self._add_starred_access_path(param_element, is_source=True)
        self.source_count += 1



    def add_arg_sink(self, signature: 'MethodSignature', arg_index: int):
        method_element = self._get_matching_method(signature)

        param_element = self._get_matching_param(signature, method_element, arg_index)

        self._add_starred_access_path(param_element, is_sink=True)
        self.sink_count += 1


    def remove_return_sources(self, signatures: List['MethodSignature']):
        for signature in signatures:
            self.remove_return_source(signature)

    def remove_return_source(self, signature: 'MethodSignature'):
        if not self._has_matching_method(signature):
            return

        method_element = self._get_matching_method(signature)
        if not self._has_return(method_element):
            return

        return_element = self._get_return(signature, method_element)

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
                if line.strip().endswith("-> _SINK_"):
                    line = line.strip()
                    line = line.replace("-> _SINK_", "")
                    if line.strip().endswith(" android.permission.SEND_SMS"):
                        line = line.strip()
                        line = line.replace(" android.permission.SEND_SMS", "")
                    sink_signatures.append(MethodSignature.from_signature_string(line))

        for sink_signature in sink_signatures:
            for index in range(len(sink_signature.arg_types)):
                self.add_arg_sink(sink_signature, index)

    def write_to_file(self, target_file_path):
        self.tree.write(target_file_path)

    def _has_matching_method(self, signature: 'MethodSignature') -> bool:
        method_element = self.category_element.find(
            f"./method[@signature='{signature.signature}']")
        return method_element is not None

    def _get_matching_method(self, signature: 'MethodSignature') -> ET.Element:
        """
        Find a method from the direct children of category_element whose signature
        matches the input exactly. If no such child exists, create and add one.
        """

        method_element = self.category_element.find(
            f"./method[@signature='{signature.signature}']")
        if method_element is None:
            method_element = ET.Element("method",
                                        attrib={"signature": signature.signature})
            self.category_element.append(method_element)

        return method_element

    def _get_return(self, signature: 'MethodSignature', method_element: ET.Element) -> 'ET.Element':
        return_element = method_element.find("./return")
        if return_element is None:
            return_element = ET.Element("return", attrib={"type": signature.return_type})
            method_element.append(return_element)

        return return_element

    def _has_return(self, method_element: ET.Element):
        return_element = method_element.find("./return")
        return not return_element is None

    def _get_matching_param(self, signature: 'MethodSignature',
                            method_element: ET.Element, arg_index: int) -> ET.Element:
        """
        Find a param Element from the direct children of category_element whose index
        matches the input. If no such child exists, create one.
        """
        param_element = method_element.find(f"./param[@index='{str(arg_index)}']")
        if param_element is None:
            param_element = ET.Element("param",
                                       attrib={"index": str(arg_index),
                                               "type": signature.arg_types[arg_index]})
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
        #  remove any access_paths that are subsumed by the one being added.

        access_path_elements = element.findall("./accessPath")
        if len(access_path_elements) > 1:
            raise AssertionError("Not expecting multiple access paths in an element "
                                 "yet.")
        elif len(access_path_elements) == 1:
            access_path_element = access_path_elements[0]
        else:
            access_path_element = ET.Element("accessPath",
                                             attrib={"isSource": "false",
                                                     "isSink": "false"})
            element.append(access_path_element)

        if is_source:
            if access_path_element.attrib['isSource'] != "true":
                access_path_element.attrib['isSource'] = "true"
        if is_sink:
            if access_path_element.attrib['isSink'] != "true":
                access_path_element.attrib['isSink'] = "true"


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
    # Stores a string of the form
    # <[full package name]: [return type] [method name]([arg types,])> -> _SOURCE_
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

    def get_source_string(self):
        # Assumes string should be of the form
        # <[full package name]: [return type] [method name]([arg types,])> -> _SOURCE_
        return f"<{self.base_type}: {self.return_type} " \
               f"{self.method_name}({','.join(self.arg_types)})> -> _SOURCE_\n"

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

        return cls.from_signature_string(signature)
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
    def from_signature_string(cls, signature: str) -> 'MethodSignature':
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


def test_single_source_sink():
    source_sinks = SourceSinkXML()

    source = MethodSignature.from_signature_string(
        "<android.os.Bundle: java.lang.String getString(java.lang.String)>")
    sink = MethodSignature.from_signature_string(
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
