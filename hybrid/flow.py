# Copyright 2020 Austin Mordahl
# Forked  in 2024 by Calix Barrus

from typing import Dict, List
import logging
#logging.basicConfig(level=logging.DEBUG)
import os
import re
import xml.etree.ElementTree as ET

import pandas as pd

import util.logger
logger = util.logger.get_logger(__name__)

class Flow:
    """
    Class that represents a flow returned by AQL.
    """

    register_regex = re.compile(r"\$[a-z]\d+")

    def __init__(self, element):
        self.element = element
        # self.update_file()
    
    def get_file(self) -> str:
        f = self.element.find("reference").findall("app")[0].findall("file")[0].text
        return f

    # def update_file(self):
    #     for e in self.element:
    #         if e.tag == "reference":
    #             f = e.find("app").find("file").text
    #             e.find("app").find("file").text = os.path.basename(f)
                
    # @classmethod
    # def clean(cls, stmt: str) -> str:
    #     c = Flow.register_regex.sub("", stmt)
    #     c = re.sub(r"_ds_method_clone_[\d]*", "", c)
    #     logging.debug(f"Before clean: {stmt}\nAfter clean: {c}")
    #     return c.strip()
    
    def get_source_and_sink(self) -> Dict[str, str]:
        result = dict()
        references = self.element.findall("reference")
        source = [r for r in references if r.get("type") == "from"][0]
        sink = [r for r in references if r.get("type") == "to"][0]

        # def get_statement_full(a: ET.Element) -> str:
        #     return a.find("statement").find("statementfull").text

        

        def get_statementgeneric(a: ET.Element) -> str:
            return a.find("statement").find("statementgeneric").text

        # debug
        # logger.debug(source)
        # write_element(source, os.path.join("data", "temp", "temp.xml"))
        # end debug

        result["source_statementgeneric"] = get_statementgeneric(source)

        result["source_method"] = self.get_method_text(source)
        result["source_classname"] = source.find("classname").text
        result["sink_statementgeneric"] = get_statementgeneric(sink)
        result["sink_method"] = self.get_method_text(sink)
        result["sink_classname"] = sink.find("classname").text
        return result
    
    def get_method_text(self, statement_element: ET.Element):
        # Some gpbench cases don't report method, and so there is no method element
        method_element = statement_element.find("method")
        if method_element is not None:
            return method_element.text
        else:
            return ""
    
    def get_source_statementgeneric(self) -> str:
        references = self.element.findall("reference")
        source = [r for r in references if r.get("type") == "from"][0]
        return source.find("statement").find("statementgeneric").text
    
    def get_sink_statementgeneric(self) -> str:
        references = self.element.findall("reference")
        source = [r for r in references if r.get("type") == "to"][0]
        return source.find("statement").find("statementgeneric").text
    
    def get_ground_truth_attribute(self) -> str:
        attributes = self.element.find("attributes").findall("attribute")
        for attribute in attributes:
            if attribute.find("name").text == "ground_truth":
                return attribute.find("value").text
            
        print(self.get_file())
        assert False

    def __str__(self):
        # return f"from: {self.get_source_statementgeneric()}; to: {self.get_sink_statementgeneric()}"
        return str(self.get_source_and_sink())
    

    def __eq__(self, other):
        """
        Return true if two flows are equal
            
        Criteria:
        1. Same apk.
        2. Same source and sink.
        3. Same method and class.
        """

        if not isinstance(other, Flow):
            return False
        else:
            if not self.get_file() == other.get_file():
                return False
            
            self_ss_dict = self.get_source_and_sink()
            other_ss_dict = other.get_source_and_sink()

            for key in ["source_classname", "sink_classname"]:
                if self_ss_dict[key] != other_ss_dict[key]:
                    return False
            
            # In some cases the ground truth does not report a method.
            for key in ["source_method",  "sink_method"]:
                # If neither method is "" and they don't match
                if not (self_ss_dict[key] == "" and other_ss_dict[key] == "") and (self_ss_dict[key] != other_ss_dict[key]):
                    return False

            if self_ss_dict["source_statementgeneric"] == other_ss_dict["source_statementgeneric"] and self_ss_dict["sink_statementgeneric"] == other_ss_dict["sink_statementgeneric"]:
                return True

            # if class in either Flow's statementgeneric matches the class of the Flow, then it might have been incorrectly inferred. 
            # In this case, do not consider the class names when comparing statementgeneric.

            # Pick out the the class in the statement generic. If there is a match, update the dict that will be compared so the class name in the statementgenerics are not considered.
            # statementgeneric string is expected to be of the form
            # <anupam.acrylic.Splash$1: void run()>
            pattern = r"(.+)(: .+\))"
            if not self_ss_dict["source_statementgeneric"] == other_ss_dict["source_statementgeneric"]:
                match = re.search(pattern, self_ss_dict["source_statementgeneric"])
                self_source_classname, self_source_rest_of_statement = match.group(1), match.group(2)
                match = re.search(pattern, other_ss_dict["source_statementgeneric"])
                other_source_classname, other_source_rest_of_statement = match.group(1), match.group(2)
                if self_source_rest_of_statement != other_source_rest_of_statement:
                    return False
                if self_source_classname == self_ss_dict["source_classname"] or other_source_classname == other_ss_dict["source_classname"]:
                    logger.warn(f"Exceptional comparison case between statementgeneric's {self_ss_dict["source_statementgeneric"]} and {other_ss_dict["source_statementgeneric"]}")
                    self_ss_dict["source_statementgeneric"] = self_source_rest_of_statement
                    other_ss_dict["source_statementgeneric"] = other_source_rest_of_statement
                
            if not self_ss_dict["sink_statementgeneric"] == other_ss_dict["sink_statementgeneric"]:
                match = re.search(pattern, self_ss_dict["sink_statementgeneric"])
                self_sink_classname, self_sink_rest_of_statement = match.group(1), match.group(2)
                match = re.search(pattern, other_ss_dict["sink_statementgeneric"])
                other_sink_classname, other_sink_rest_of_statement = match.group(1), match.group(2)
                if self_sink_rest_of_statement != other_sink_rest_of_statement:
                    return False
                if self_sink_classname == self_ss_dict["sink_classname"] or other_sink_classname == other_ss_dict["sink_classname"]:
                    logger.warn(f"Exceptional comparison case between statementgeneric's {self_ss_dict["sink_statementgeneric"]} and {other_ss_dict["sink_statementgeneric"]}")
                    self_ss_dict["sink_statementgeneric"] = self_sink_rest_of_statement
                    other_ss_dict["sink_statementgeneric"] = other_sink_rest_of_statement
            
            
            return self_ss_dict["source_statementgeneric"] == other_ss_dict["source_statementgeneric"] and self_ss_dict["sink_statementgeneric"] == other_ss_dict["sink_statementgeneric"]
        
    def __hash__(self):
        sas = self.get_source_and_sink()
        return hash((self.get_file(), frozenset(sas.items())))

    def __gt__(self, other):
        """ Sort by file, then by sink, class, then by sink method, then by sink statement, then by source."""
        if not isinstance(other, Flow):
            raise TypeError(f"{other} is not of type Flow")

        if self.get_file() != other.get_file():
            return self.get_file() > other.get_file()
        else:
            d1 = self.get_source_and_sink()
            d2 = other.get_source_and_sink()
            if d1['sink_classname'] != d2['sink_classname']:
                return d1['sink_classname'] > d2['sink_classname']
            elif d1['sink_method'] != d2['sink_method']:
                return d1['sink_method'] != d2['sink_method']
            elif d1['sink_statementgeneric'] != d2['sink_statementgeneric']:
                return d1['sink_statementgeneric'] != d2['sink_statementgeneric']
            elif d1['source_classname'] != d2['source_classname']:
                return d1['source_classname'] > d2['source_classname']
            elif d1['source_method'] != d2['source_method']:
                return d1['source_method'] != d2['source_method']
            elif d1['source_statementgeneric'] != d2['source_statementgeneric']:
                return d1['source_statementgeneric'] != d2['source_statementgeneric']
            else: # completely equal in every way
                return False

    def __lt__(self, other):
        return not(self == other) and not(self > other)

    def __le__(self, other):
        return self == other or self < other

    def __ge__(self, other):
        return self == other or self > other
    

def compare_flows(detected_flows: List[Flow], ground_truth_flows_df: pd.DataFrame, apk_name: str) -> List[int]:
    apk_name_mask = ground_truth_flows_df['APK Name'] == apk_name
    
    # Keep track of specific flows since I'll probably need to look at them specifically later.
    tp_flows = []
    fp_flows = []
    # Flows not in ground truth, or annotated in ground truth as UNKNOWN or MISMATCH
    inconclusive_flows = []

    tn_flows = []
    fn_flows = []
    has_flow_been_detected = pd.Series([False] * len(ground_truth_flows_df[apk_name_mask]), index=ground_truth_flows_df[apk_name_mask].index)
    for detected_flow in detected_flows:
        # does it match a ground truth flow?
        detected_flow_mask = ground_truth_flows_df[apk_name_mask]['Flow'] == detected_flow
        if sum(detected_flow_mask) == 0:
            # Flow is not in ground_truth
            inconclusive_flows.append(detected_flow)
        elif sum(detected_flow_mask) == 1:
            detected_flow_row = ground_truth_flows_df[apk_name_mask][detected_flow_mask].iloc[0]
            has_flow_been_detected[detected_flow_row.name] = True #TODO test to see if name actually pulls the index of the row
            ground_truth_value = detected_flow_row['Ground Truth Value']
            if ground_truth_value == "TRUE":
                tp_flows.append(detected_flow)
            elif ground_truth_value == "FALSE": 
                fp_flows.append(detected_flow)
            else: 
                # Value must have been UNKNOWN or MISMATCH or NATIVE
                inconclusive_flows.append(detected_flow)
        else: 
            raise AssertionError("Detected flow is not expected to match with more than 1 ground truth flow.")

    # count the known flows that were not hit to get TN/FN, Unknown Negative
    for i in has_flow_been_detected[has_flow_been_detected == False].index:
        # These flows were NOT hit, so if ground truth is FALSE -> true negative, and vice versa
        if ground_truth_flows_df.loc[i, 'Ground Truth Value'] == 'FALSE':
            tn_flows.append(ground_truth_flows_df.loc[i, 'Flow'])
        elif ground_truth_flows_df.loc[i, 'Ground Truth Value'] == 'TRUE':
            fn_flows.append(ground_truth_flows_df.loc[i, 'Flow'])
        else: 
            # We don't really care if uncategorized flows are detected or not.
            pass


    # Debug
    # ground_truth_flows_df[apk_name_mask].to_csv(os.path.join("/home/calix/programming/ConDySta/data/temp", "app_flows.csv"))

    # # tree = ET.ElementTree(inconclusive_flows[0].element)
    # # ET.indent(tree) # Pretty print the result, requires python 3.9
    # # tree.write(os.path.join("/home/calix/programming/ConDySta/data/temp", "detected_leak.xml"))
    # for flow in inconclusive_flows:
    #     logger.debug(str(flow))
        

    # element = inconclusive_flows[0].element
    # references = element.findall("reference")
    # logger.debug(references)
    # source = [r for r in references if r.get("type") == "to"][0]
    # logger.debug(source)
    # for child in source:
    #     logger.debug(child)
    #     logger.debug(child.text)
    #     logger.debug(len(child))
    # logger.debug(source.find("statement").find("statementgeneric").text)
    
    # End Debug

    return len(tp_flows), len(fp_flows), len(tn_flows), len(fn_flows), len(inconclusive_flows) # type: ignore


def create_flows_elements(sink_statement_full, sink_method, sink_class_name, source_tuples, apk_path):
    # TODO: this method of making flows isn't consistent with Flowdroid's semantics (its fine for the granularity of the fossdroid ground truth though)

    sink_reference_element = make_sink_reference_element(sink_statement_full, sink_method, sink_class_name, apk_path)
    source_reference_elements = []
    for tuple in source_tuples:
        source_reference_elements.append(make_source_reference_element(tuple[0], tuple[1], tuple[2], apk_path))

    assert len(source_reference_elements) >= 1

    # assemble flow elements
    flows = []
    
    for source_reference_element in source_reference_elements:
        flow_element = ET.Element('flow') #TODO: add some experiment ID info?

        flow_element.append(source_reference_element) 
        flow_element.append(sink_reference_element) #TODO: does sink ref element need to be deep copied?

        flows.append(Flow(flow_element))
    
    return flows

def make_sink_reference_element(statement_full: str, method: str, classname: str, apk_path: str):
    return make_reference_element(statement_full, method, classname, apk_path, "to")

def make_source_reference_element(statement_full: str, method: str, classname: str, apk_path: str):
    return make_reference_element(statement_full, method, classname, apk_path, "from")

def make_reference_element(statement_full: str, method: str, classname: str, apk_path: str, type: str):
    assert type == "to" or type == "from"

    reference_element = ET.Element("reference", attrib={'type':type})

    reference_element.append(make_statement_element(statement_full))

    temp_element = ET.Element('method')
    temp_element.text = method
    reference_element.append(temp_element)
    temp_element = ET.Element('classname')
    temp_element.text = classname
    reference_element.append(temp_element)

    reference_element.append(make_app_element(apk_path))
    return reference_element

def make_statement_element(statement_full):

    statement_generic = re.search(r"<(.+)>", statement_full).group(1)
    
    # First parse parameters
    pattern = r"\((.*)\)"
    matches = re.findall(pattern, statement_generic)
    assert len(matches) == 1
    param_types = matches[0].split(',')

    # pattern = r"&gt;\((.*)\)"
    pattern = r">\((.*)\)"
    matches = re.findall(pattern, statement_full)
    assert len(matches) == 1
    param_values = matches[0].split(',')

    # Splitting an empty string produces a list with one element
    if matches[0] == "":
        param_types = []
        param_values = []

    assert len(param_types) == len(param_values)
    parameters_element = ET.Element("parameters")
    for i in range(len(param_types)):
        parameter_element = ET.Element("parameter")

        temp_element = ET.Element("type")
        temp_element.text = param_types[i]
        parameter_element.append(temp_element)
        temp_element = ET.Element("value")
        temp_element.text = param_values[i]
        parameter_element.append(temp_element)
        
        parameters_element.append(parameter_element)

    statement_element = ET.Element("statement")
    temp_element = ET.Element("statementfull")
    temp_element.text = statement_full
    statement_element.append(temp_element)
    temp_element = ET.Element("statementgeneric")
    temp_element.text = statement_generic
    statement_element.append(temp_element)

    statement_element.append(parameters_element)

    return statement_element


def make_app_element(apk_path):
    #TODO: make sure path exists, add in hashes

    app_element = ET.Element("app")
    temp_element = ET.Element("file")
    temp_element.text = os.path.basename(apk_path)
    app_element.append(temp_element)
    ET.SubElement(app_element, "hashes")
    return app_element

def attributes_ground_truth(value):
    attributes_element = ET.Element("attributes")
    attribute_element = ET.Element("attribute")
    temp_element = ET.Element("name")
    temp_element.text = "ground_truth"
    attribute_element.append(temp_element)
    temp_element = ET.Element("value")
    temp_element.text = value
    attribute_element.append(temp_element)
    attributes_element.append(attribute_element)
    return attribute_element

def write_element(element: ET.Element, output_path: str):
    tree = ET.ElementTree(element)
    ET.indent(tree) # Pretty print the result, requires python 3.9
    tree.write(output_path)
