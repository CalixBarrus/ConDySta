# Copyright 2020 Austin Mordahl
# Forked  in 2024 by Calix Barrus

from typing import Dict
import logging
#logging.basicConfig(level=logging.DEBUG)
import os
import re
import xml.etree.ElementTree as ET

from util import logger
logger = logger.get_logger_revised(__name__)

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

        result["source_statementgeneric"] = get_statementgeneric(source)
        result["source_method"] = source.find("method").text
        result["source_classname"] = source.find("classname").text
        result["sink_statementgeneric"] = get_statementgeneric(sink)
        result["sink_method"] = sink.find("method").text
        result["sink_classname"] = sink.find("classname").text
        return result
    
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

            for key in ["source_method", "source_classname", "sink_method", "sink_classname"]:
                if self_ss_dict[key] != other_ss_dict[key]:
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
    
