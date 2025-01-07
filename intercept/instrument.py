from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import os
import re
import shutil
from typing import Callable, List, Tuple, Union

import pandas as pd

from experiment.paths import StepInfoInterface
from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path
from hybrid.source_sink import MethodSignature
from intercept.InstrumentationReport import InstrumentationReport
from util.input import ApkModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

SMALI_STRING_CLASS_NAME: str = "Ljava/lang/String;"

# TODO: instrumentation manager. Registers an ordered list of strategies. For each file, Code insertion models are collected from each strategy and then inserted. 
# insertions at the same target line will be done in the order that the strategies were registered, so do read strategies before write strategies. 

class SmaliInstrumentationStrategy(ABC):

    @abstractmethod
    def instrument_file(self, smali_file: 'SmaliFile') -> List['CodeInsertionModel']:
        """Hook gets called on each SmaliFile model in a given DecodedApkModel"""
        raise NotImplementedError("Interface not implemented")

    @abstractmethod
    def needs_to_insert_directory(self) -> bool:
        """
        :return: Whether this instrumenter requires additional
        smali directories to be dropped into the apk.
        """
        raise NotImplementedError("Interface not implemented")

    @abstractmethod
    def path_to_directory(self) -> str:
        """
        This method shouldn't be called unless
        needs_to_insert_directory() returns true.
        :return: Path to root of smali directories that need to be dropped
        into a smali_classes file.
        """
        raise NotImplementedError("Interface not implemented")
    
def instrumentation_strategy_factory_wrapper(**kwargs) -> List[SmaliInstrumentationStrategy]:
    # TODO: harness sources strategy in theory needs app specific information on which sources to harness (login vs. spyware scenario)
    # This method should contain the logic called inside an experiment for creating the dependency for instrumentation that will be injected.

    instrumentation_strategies = kwargs["instrumentation_strategy"]
    if not isinstance(instrumentation_strategies, list):
        instrumentation_strategies = [instrumentation_strategies]

    instrumenters: List[SmaliInstrumentationStrategy] = []
    for strategy_name in instrumentation_strategies:
        if "HarnessSources" == strategy_name:
            instrumenters.append(instrumentation_strategy_factory(strategy_name, kwargs["harness_sources"]))
        else:
            instrumenters.append(instrumentation_strategy_factory(strategy_name))

    return instrumenters



def instrumentation_strategy_factory(
        strategy_name: str, sources_to_harness_path: str = "") -> \
        'SmaliInstrumentationStrategy':
    
    if strategy_name == \
            "LogStringReturnInstrumentationStrategy":
        return LogStringReturnInstrumentationStrategy()
    elif strategy_name == \
            "StringReturnInstrumentationStrategy":
        return StringReturnInstrumentationStrategy()
    elif strategy_name == \
            "StringReturnValuesInstrumentationStrategy":
        return StringReturnValuesInstrumentationStrategy()
    elif strategy_name == \
            "StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy":
        # TODO: this should be controlled by experiment inputs & visible to experiment setup procedure 
        do_instrument_args = False
        
        logger.info(f"do_instrument_args = {do_instrument_args}")
        return StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy(do_instrument_args)
    elif strategy_name == "HarnessSources":
        assert sources_to_harness_path != ""
        signatures = sources_to_harness(sources_to_harness_path)
        logger.info(f"Harnessing sources on list of {len(signatures)} method signatures")
        return HarnessSources(signatures)
    elif strategy_name == "HarnessObservations":
        # needs to point to where observations will be
        return HarnessObservations()
    else:
        raise ValueError(f"Invalid instrumentation strategy:"
                         f" {strategy_name}")

class InstrumentSmali(StepInfoInterface):
    observations_column: str = "Observations Lists"
    strategies: List['SmaliInstrumentationStrategy']
    _concise_params: str
    def __init__(self, strategy_names: List[str]) -> None:
        self.strategies = []
        
        self._concise_params = ""
        for strategy_name in strategy_names:
            self.strategies.append(instrumentation_strategy_factory(strategy_name))

            if strategy_name is "HarnessSources":
                self._concise_params += "source-substitution"
            # TODO: fill out more of these cases

            

    @property
    def step_name(self) -> str:
        return "instrument"

    @property
    def version(self) -> Tuple[int]:
        return (0, 1, 0)

    @property
    def concise_params(self) -> List[str]:
        return self._concise_params

    def execute(self, input_df: pd.DataFrame, output_path_column: str=""):
        # Input: df with columns "Decompiled Path", ["{output_path}", "Observations Lists"]
        # Output: in-place on "Decompiled Path" or changes are made to copies at a path in the indicated column name.
        # observations columns should be provided if HarnessObservations is used as a strategy.
        

        smali_paths: pd.Series = pd.Series()
        if output_path_column == "":
            smali_path_column = "Decompiled Path"
        else: 
            # copy smalis into new dirs
            for i in input_df.index:
                # dirs_exist_ok -> Overwrite files & directories if they are already there.
                shutil.copytree(input_df.loc[i, "Decompiled Path"], input_df.loc[i, output_path_column],
                        dirs_exist_ok=True)

            smali_path_column = output_path_column

        # handle observations_column optional parameter
        if not self.observations_column in input_df.columns:
            input_df.loc[self.observations_column] = None

        for i in smali_paths.index:

            smali_path = input_df.at[i, smali_path_column]
            context = input_df.at[i, self.observations_column]
            
            decoded_apk_model = DecodedApkModel(smali_path)
            decoded_apk_model.instrument(self.strategies, observation_context=context)
            return decoded_apk_model


# def instrument_batch(config: HybridAnalysisConfig, apks: List[ApkModel]):
def instrument_batch(decoded_apks_directory_path: str, instrumentation_strategy: List[SmaliInstrumentationStrategy], apks: List[ApkModel]):

    # Read in and parse decoded apks
    decoded_apk_models: List[DecodedApkModel] = []
    for apk in apks:
        decoded_apk_models.append(instrument_apk(decoded_apks_directory_path, instrumentation_strategy, apk))

    # We may later decide to save the decoded_apk_models for use in interpreting dynamic analysis results

# def instrument_apk(config: HybridAnalysisConfig, apk: ApkModel) -> 'DecodedApkModel':
def instrument_apk(decoded_apks_directory_path: str, instrumenters: List[SmaliInstrumentationStrategy], apk: ApkModel) -> 'DecodedApkModel':

    # TODO: in theory, this factory should get called after the start of the experiment, but outside of the business layer, so it can be transparent via experiment args how this is being constructed exactly.
    # instrumenters: List[SmaliInstrumentationStrategy] = [instrumentation_strategy_factory(instrumentation_strategy) for instrumentation_strategy in instrumentation_strategies]
    # decoded_apks_directory_path = config._decoded_apks_path

    decoded_apk_path = decoded_apk_path(decoded_apks_directory_path, apk)

    decoded_apk_model = DecodedApkModel(decoded_apk_path)
    decoded_apk_model.instrument(instrumenters)
    return decoded_apk_model

### Begin Model Classes ###
# Model classes store lexing and parsing logic. The constructors should leave the model
# ready for instrumentation by any of the instrumentation strategies.

class DecodedApkModel:
    """
    Representation of a decoded apk's files for the purposes of instrumentation
    """
    apk_root_path: str
    project_smali_directory_paths: List[str]
    smali_directories: List[List['SmaliFile']] # TODO: this doesn't need to be a list of lists, this could just be a list of SmaliFiles (as long as the directory's are being kept track of separate)
    # is_instrumented: bool TODO: this is a good idea, but right now DecodedApkModels are constructed when they are needed and then deleted; this kind of state wouldn't get cached anywhwere

    def __init__(self, decoded_apk_root_path: str):
        """
        Parse all the smali directories and files for later instrumentation.
        :param decoded_apk_root_path: Path to the root directory of a single apk
        decoded by apktool.
        """
        if not os.path.isdir(decoded_apk_root_path):
            raise AssertionError(f"Path {decoded_apk_root_path} expected to be directory")

        self.apk_root_path = decoded_apk_root_path

        # self.project_smali_directory_names = []
        # for item in os.listdir(self.apk_root_path):
        #     if (os.path.isdir(os.path.join(self.apk_root_path, item)) and
        #             item.startswith("smali")):
        #         assert (item == "smali"
        #                 or item.startswith("smali_classes")
        #                 or item.startswith("smali_assets"))
        #         self.project_smali_directory_names.append(item)

        # # Sort the folder names so indexing into the list is consistent with
        # # the file names.
        # self.project_smali_directory_names.sort()
        # assert self.project_smali_directory_names[0] == "smali"

        # # Go through each folder smali_classes folder and parse all the smali
        # # files.
        # project_smali_directory_paths = map(os.path.join,
        #                                     [decoded_apk_root_path] * len(
        #                                         self.project_smali_directory_names),
        #                                     self.project_smali_directory_names)

        self.project_smali_directory_paths = DecodedApkModel.get_project_smali_directory_paths(self.apk_root_path)
        
        self.smali_directories: List[List[SmaliFile]] = []
        for smali_dir_path in self.project_smali_directory_paths:
            smali_paths = DecodedApkModel.scan_for_smali_file_paths(smali_dir_path)
            # self.smali_directories.append(
            #     self.scan_for_smali_files(path, ""))
            self.smali_directories.append([SmaliFile(smali_file_path) for smali_file_path in smali_paths])

        # self.is_instrumented = False

    @staticmethod
    def get_project_smali_directory_paths(decoded_apk_root_path: str) -> List[str]:
        project_smali_directory_names = []
        for item in os.listdir(decoded_apk_root_path):
            if (os.path.isdir(os.path.join(decoded_apk_root_path, item)) and
                    item.startswith("smali")):
                assert (item == "smali"
                        or item.startswith("smali_classes")
                        or item.startswith("smali_assets"))
                project_smali_directory_names.append(item)

        # Sort the folder names so indexing into the list is consistent with
        # the file names.
        project_smali_directory_names.sort()
        assert project_smali_directory_names[0] == "smali"

        project_smali_directory_paths = list(map(os.path.join,
                                            [decoded_apk_root_path] * len(
                                                project_smali_directory_names),
                                            project_smali_directory_names))
        
        return project_smali_directory_paths
    

    @staticmethod
    def scan_for_smali_file_paths(project_smali_folder_path: str, _class_path: str="") -> List[str]:
        """
        Recursively traverse the subdirectories of
        project_smali_folder_path, getting the methods in each smali file.
        :param project_smali_folder_path: path to the "smali" or
        "smali_classes[n]" directory.
        :param _class_path: relative path referring to the subdirectories
        traversed so far, used for recursion.
        :return: List of SmaliFile objects containing data about each file in the apk
        """
    
        assert os.path.basename(project_smali_folder_path).startswith("smali")

        result_smali_file_paths: List[str] = []
        # result_smali_files: List[SmaliFile] = []
        for item in os.listdir(os.path.join(project_smali_folder_path,
                                            _class_path)):
            item_path = os.path.join(project_smali_folder_path, _class_path,
                                     item)
            if os.path.isdir(item_path):
                result_smali_file_paths += DecodedApkModel.scan_for_smali_file_paths(
                    project_smali_folder_path,
                    os.path.join(_class_path, item))

            elif item.endswith(".smali"):
                # result_smali_files.append(SmaliFile(
                #     project_smali_folder_path, _class_path, item))
                result_smali_file_paths.append(os.path.join(project_smali_folder_path, _class_path, item))

        return result_smali_file_paths

    def instrument(self, instrumenters: List[SmaliInstrumentationStrategy], observation_context: List[Tuple[InstrumentationReport, str, str]]=None):
        for instrumenter in instrumenters:
            if instrumenter.needs_to_insert_directory():
                self.insert_smali_directory(instrumenter.path_to_directory())

        insertions_count = [0] * len(instrumenters)
        for smali_directory in self.smali_directories:
            for smali_file in smali_directory:

                # Apply each instrumentation strategy
                insertions = []
                for index, instrumenter in enumerate(instrumenters):

                    if isinstance(instrumenter, HarnessObservations):
                        new_insertions = instrumenter.instrument_file(smali_file, observation_context)
                    else:
                        new_insertions = instrumenter.instrument_file(smali_file)

                    insertions_count[index] += len(new_insertions)
                    insertions += new_insertions

                
                smali_file.insert_code(insertions)

        # start debug
        # logger.debug(f"Instrumenters performed {",".join([str(count) for count in insertions_count])} code insertions, respectively on apk {os.path.basename(self.apk_root_path)}")
        # end debug

        self.is_instrumented = True

    def insert_smali_directory(self, smali_source_directory_path: str):
        # TODO this could get called twice for two different instrumentation strategies

        if not os.path.isdir(smali_source_directory_path):
            raise ValueError(
                "Directory " + smali_source_directory_path + " does not exist.")

        # Use the last directory; it hopefully has the fewest methods, so we don't put too many methods into the same smali directory
        destination_directory_path = self.project_smali_directory_paths[-1]
        if not os.path.isdir(destination_directory_path):
            raise ValueError(
                "Directory " + destination_directory_path + " does not exist.")

        shutil.copytree(smali_source_directory_path, destination_directory_path,
                        dirs_exist_ok=True)


class SmaliFile:
    """
    Class representing a single smali text file.

    Most parsing and modification logic for smali files should be contained in this
    class. Contained classes should focus on being model classes, and should have
    limited parsing/update logic.
    """
    file_path: str
    class_name: str
    class_keywords: List[str]
    methods: List['SmaliMethod']

    def __init__(self, smali_file_path):
        self.file_path = smali_file_path
        self.methods = []

        with open(self.file_path, 'r') as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            if line.startswith(".class"):
                # for example, 
                # .class public Lanupam/acrylic/AboutActivity;
                split_class_header = line.strip().split()
                _ = split_class_header[0] # ".class"
                self.class_name = split_class_header[-1]
                if len(split_class_header) > 2:
                    self.class_keywords = split_class_header[1:-1]
                else: 
                    self.class_keywords = []

            if line.startswith(".method"):
                self.methods.append(self.parse_smali_method(lines, i, self.class_name))
        
        """
        Example of header of normal class
.class public Lanupam/acrylic/AboutActivity;
.super Landroid/app/Activity;
.source "AboutActivity.java"

        Example of header of inner class
.class Lanupam/acrylic/EasyPaint$MyView$MultiLinePathManager;
.super Ljava/lang/Object;
.source "EasyPaint.java"

# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lanupam/acrylic/EasyPaint$MyView;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x2
    name = "MultiLinePathManager"
.end annotation

        Example of header of anonymous class
.class Lanupam/acrylic/EasyPaint$1;
.super Ljava/lang/Object;
.source "EasyPaint.java"

# interfaces
.implements Landroid/content/DialogInterface$OnClickListener;

# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lanupam/acrylic/EasyPaint;->onCreate(Landroid/os/Bundle;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation
        """

    def parse_smali_method(self, lines: List[str], function_start_index: int, enclosing_class_name: str) -> 'SmaliMethod':
        # TODO: This should prolly get moved to Smali Method

        result_method: SmaliMethod = SmaliMethod()
        result_method.start_line_number = function_start_index
        result_method.enclosing_class_name = enclosing_class_name

        self.parse_method_signature(result_method, lines[function_start_index])


        for i in range(function_start_index, len(lines)):
            line = lines[i]
            line = line.strip()
            if line == (".end method"):
                result_method.end_line_number = i
                break
            elif line.startswith(".locals"):
                # Line will be of form
                # .locals [n]
                # where n is the number of locals used in the method
                result_method.locals_line_number = i
                result_method.number_of_locals = int(line.split(" ")[1])
            elif line.startswith("return"):
                result_method.return_line_numbers.append(i)
                if line != "return-void":
                    # if not void return, line is expected to be
                    # "return v[n]" where n is the number of the return register
                    result_method.return_registers.append(line.split(" ")[1])
            elif SmaliMethodInvocation.is_invocation(line):
                new_invocation = SmaliMethodInvocation.parse_invocation_line(i, line)
                result_method.invocation_statements.append(new_invocation)
            elif SmaliMethodInvocation.is_move_result(line):
                # Move result always occurs after a method invoke or a filled-new-array instruction. We want to ignore move_results due to filled-new-array instructions
                j, prev_instr_line = SmaliMethodInvocation.get_prev_instruction(i, lines)
                if not SmaliMethodInvocation.is_filled_new_array(prev_instr_line):
                    self.parse_move_result(
                        result_method.invocation_statements[-1], i, line)


        # debug
        assert result_method.start_line_number < result_method.end_line_number
        # end debug

        return result_method

    def parse_method_signature(self, method: 'SmaliMethod', signature: str) -> None:
        # Signature should be of the form
        # .method <keywords> <function_name>(<types>)<return_type>
        #
        # Notably, keywords preceding the name and args of the function are
        # all separated by spaces.

        split_signature = signature.strip().split(" ")
        split_signature = list(map(lambda s: s.strip(), split_signature))

        # Check for the "static" keyword
        if "static" in split_signature:
            method.is_static = True
        else:
            method.is_static = False

        if "abstract" in split_signature:
            method.is_abstract = True
        else:
            method.is_abstract = False

        if "native" in split_signature:
            # Treat the method as abstract if it is marked as native
            method.is_abstract = True

        # The last entry should be the identifier, formals, and return type
        signature_end = split_signature[-1]

        method.method_name = signature_end.split("(")[0]

        method_args = signature_end.split("(")[1].split(")")[0]
        method.args = self.parse_method_signature_args(method_args)

        method.return_type = signature_end.split(")")[1]

    def parse_method_signature_args(self, method_args: str) -> List[str]:
        """
        method_args: String, expected to be the string between the
        left and right parentheses of a smali method signature
        return: List of strings, each string being the type of each formal
        argument, and the length of the list being the number of arguments of the method.
        """
        # Each argument is either a primitive (Z, B, S, C, I, J, F, D) or an
        # object (L<class-name>;). Each argument is not separated by spaces.
        args = []
        current_arg = ""
        currently_parsing_object_type = False

        for char in method_args:
            if currently_parsing_object_type:
                if char == ";":
                    current_arg += char
                    args.append(current_arg)
                    current_arg = ""
                    currently_parsing_object_type = False
                else:
                    current_arg += char
            elif char in ["Z", "B", "S", "C", "I", "J", "F", "D"]:
                current_arg += char
                args.append(current_arg)
                current_arg = ""
            elif char == "L":
                currently_parsing_object_type = True
                current_arg += char
            elif char == "[":
                current_arg += char
            else:
                raise ValueError(
                    "Unexpected character " + char + " while parsing arguments string \"" + method_args + "\"")

        # Check if there was an unterminated object type
        if currently_parsing_object_type is True:
            raise ValueError(
                f"Expected semicolon at the end of the string {method_args}")

        return args


    def parse_move_result(self, prev_method_invocation: 'SmaliMethodInvocation',
                          line_number: int, move_result_line: str):
        """
        Parse a statement containing a move-result instruction and update the
        associated SmaliMethodInvocation with the parsed information.

        Note that move-result instructions must/will always have an associated invoke
        statement.
        :return: Void. Fields of passed prev_method_invocation are modified.
        """

        prev_method_invocation.move_result_line_number = line_number
        # line is expected to of the form "[move-result-[kind]] [register]"
        split_line = move_result_line.strip().split()
        prev_method_invocation.move_result_kind = split_line[0]
        prev_method_invocation.move_result_register = split_line[1]        

    def get_registers(self, method_number, requested_register_count: int) -> \
            List[str]:
        """
        Returns registers to be used by code that will be inserted.

        Relevant discussion on registers: https://groups.google.com/g/apktool/c/Elvhn32HvJQ?pli=1

        If the # of currently used registers + the requested registers is <= 16,
        return the next few registers, and note that the # of locals will need
        to be updated by the "insert code" function.

        The case for using > 16 registers is nontrivial to implement. Would
        involve sticking move instructions into all uses of parameters?

        :param method_number: Method in which the registers are being requested
        :param requested_register_count: The number of registers being requested
        :return: List of names of registers
        """
        method: SmaliMethod = self.methods[method_number]
        if method.register_count() + requested_register_count > 16:
            raise ValueError("Requesting too many registers")

        if requested_register_count == 1:
            return ["v" + str(method.number_of_locals)]
        elif requested_register_count == 2:
            return ["v" + str(method.number_of_locals), "v" + str(method.number_of_locals + 1)]
        else:
            raise NotImplementedError()

    # TODO: This is used by two instrumentation strategies, both of whom need to get compeletely refactored to use the same ideas as more recent instrumentation approaches. 
    def insert_code_into_method(self, code,
                                method_number, destination_line_number,
                                used_registers):
        with open(self.file_path, 'r') as file:
            contents = file.readlines()

        # insert code
        code_lines = code.splitlines(keepends=True)
        contents[destination_line_number:destination_line_number] = code_lines

        # Write changes
        with open(self.file_path, 'w') as file:
            file.writelines(contents)

        # update model of code
        # Parse the modified method again
        self.methods[method_number] = self.parse_smali_method(contents,
                                                              self.methods[
                                                                  method_number].start_line_number)
        # increment line numbers in all the methods after the modified method
        for method in self.methods[method_number + 1:]:
            method.increment_line_numbers(len(code_lines))

    def update_method_preamble(self, contents, method_number: int,
                               num_used_registers: int):
        if num_used_registers > 0:
            # adjust # of locals
            contents[self.methods[
                method_number].locals_line_number] = f"    .locals {self.methods[method_number].number_of_locals + num_used_registers}\n"

    def insert_code(self, code_insertions: List['CodeInsertionModel']):


        with open(self.file_path, 'r') as file:
            contents = file.readlines()

        # Sort insertions by reverse line number so after each insertion, the line
        # numbers of subsequent insertions are still valid.
        # TODO: If two or more insertion models have the same line number, they MUST stay in that relative order. Need to verify that this is the case!
        code_insertions.sort(key=lambda c: c.line_number, reverse=True)

        additional_registers_used = 0
        cur_method = len(self.methods) + 1

        for code_insertion in code_insertions:

            # If the code insertion belongs to a new method, update the method
            # preamble of the previous method, and reset the relevant locals.
            if code_insertion.method_index < cur_method:
                self.update_method_preamble(contents, cur_method, additional_registers_used)
                cur_method = code_insertion.method_index
                additional_registers_used = 0

            additional_registers_used = max(additional_registers_used, len(code_insertion.registers))

            # insert code
            code_lines = code_insertion.code_to_insert.splitlines(keepends=True)
            contents[code_insertion.line_number:code_insertion.line_number] = code_lines

        # Update the preamble of the last instrumented method
        self.update_method_preamble(contents, cur_method, additional_registers_used)

        with open(self.file_path, 'w') as file:
            file.writelines(contents)

        # Update the model of the code
        # - No need to for now, as this batch code insertion should be the last thing
        # the code model is used for


class CodeInsertionModel:
    """
    Bare bones model class containing necessary information for a given code insertion
    """
    code_to_insert: str
    method_index: int
    line_number: int
    registers: List[str]

    def __init__(self, code_to_insert, method_index, line_number, registers):
        self.code_to_insert = code_to_insert
        self.method_index = method_index
        self.line_number = line_number
        self.registers = registers


class SmaliMethod:
    """
    Class to contain important information about a method in a
    smali file. This class is intended to capture information that needs to
    be referenced and modified during instrumentation. It is the user's
    responsibility to ensure that modifications to the file are updated in
    this object and vice versa.
    """
    enclosing_class_name: str
    method_name: str
    is_static: bool
    is_abstract: bool
    start_line_number: int
    locals_line_number: int
    invocation_statements: List['SmaliMethodInvocation']
    return_line_numbers: List[int]
    end_line_number: int
    number_of_locals: int
    args: List[str]
    return_type: str
    return_registers: List[str]

    def __init__(self):
        self.invocation_statements = []
        self.return_line_numbers = []
        self.args = []
        self.return_registers = []

        self.locals_line_number = -1

    def register_count(self):
        return len(self._register_names())
        
    def _register_names(self) -> List[str]:
        register_names = []

        for i in range(self.number_of_locals):
            register_names.append(f"v{str(i)}")

        param_registers_count = len(self.args)
        param_registers_count += sum([1 if data_type == "J" else 0 for data_type in self.args])
        param_registers_count += sum([1 if data_type == "D" else 0 for data_type in self.args])

        # Implicit param register for "this" pointer
        if not self.is_static:
            param_registers_count += 1

        for i in range(param_registers_count):
            register_names.append(f"p{str(i)}") 

        # Aliases for these registers are:
        # for i in range(self.number_of_locals, self.number_of_locals + param_registers_count):
        #     register_names.append(f"v{str(i)}") 


        return register_names
        
    def get_next_register(self, register: str) -> str:
        register_names: List[str] = self._register_names()
        if not register in register_names:
            raise AssertionError(f"register {register} is not in {register_names}")

        next_register_index = register_names.index(register) + 1
        if next_register_index < len(register_names):
            return register_names[next_register_index]
        else:
            return ""

    def increment_line_numbers(self, increment):
        self.start_line_number += increment

        # abstract methods may not have locals
        if self.locals_line_number != -1:
            self.locals_line_number += increment
        for i in range(len(self.return_line_numbers)):
            self.return_line_numbers[i] += increment
        self.end_line_number += increment

        for invocation_statement in self.invocation_statements:
            invocation_statement.increment_line_number(increment)

    

@dataclass
class SmaliMethodInvocation:
    """
    Class representing a single line of smali code containing a method invocation.

    This class is intended to capture information that needs to
    be referenced and modified during instrumentation. It is the user's
    responsibility to ensure that modifications to the file are updated in
    this object and vice versa.
    """
    invoke_line_number: int = -1
    invoke_kind: str = ""           # TODO: could be an enum
    is_range_kind: bool = False
    argument_registers: List[str] = field(default_factory=list)
    class_name: str = ""
    method_name: str = ""
    argument_register_types_pre: List[str] = field(default_factory=list)
    return_type: str = ""

    move_result_line_number: int = -1
    move_result_kind: str = ""
    move_result_register: str = ""

    # def __init__(self,
    #              invoke_line_number: int,
    #              invoke_kind: str,
    #              is_range_kind: bool,
    #              argument_registers: List[str],
    #              class_name: str,
    #              method_name: str,
    #              argument_register_types_pre: List[str],
    #              return_type: str,
    #              move_result_line_number: int,
    #              move_result_kind: str,
    #              move_result_register: str,
    #              ):
    #     self.invoke_line_number = invoke_line_number
    #     self.invoke_kind = invoke_kind
    #     self.is_range_kind = is_range_kind
    #     self.argument_registers = argument_registers
    #     self.class_name = class_name
    #     self.method_name = method_name
    #     self.argument_register_types_pre = argument_register_types_pre
    #     self.return_type = return_type
    #     self.move_result_line_number = move_result_line_number
    #     self.move_result_kind = move_result_kind
    #     self.move_result_register = move_result_register

    # def __repr__(self):
    #     return f"SmaliMethodInvocation(invoke_line_number={repr(self.invoke_line_number)}," \
    #             f"invoke_kind={repr(self.invoke_kind)}," \
    #             f"is_range_kind={repr(self.is_range_kind)}," \
    #             f"arg_registers={repr(self.arg_registers)}," \
    #             f"class_name={repr(self.class_name)},method_name={repr(self.method_name)}," \
    #             f"arg_types_pre={repr(self.arg_types_pre)}," \
    #             f"return_type={repr(self.return_type)}," \
    #             f"move_result_line_number={repr(self.move_result_line_number)},move_result_kind={repr(self.move_result_kind)},move_result_register={repr(self.move_result_register)},)"

    @staticmethod
    def get_empty_object() -> 'SmaliMethodInvocation':
        return SmaliMethodInvocation()
        # return SmaliMethodInvocation(-1, "", False, [], "", "", [], "", -1, "", "")

    @staticmethod
    def is_invocation(line: str) -> bool:
        return line.strip().startswith("invoke")

    @staticmethod
    def is_move_result(line):
        return line.strip().startswith("move-result")
    
    @staticmethod
    def is_filled_new_array(line):
        return line.strip().startswith("filled-new-array")

    # def is_primitive_register(self, register_index):
    #     return self._is_type_primitive(self.register_type(register_index))

    def is_return_primitive(self):
        return self._is_type_primitive(self.return_type)

    def _is_type_primitive(self, type: str):
        return not type.startswith("L")

    def get_java_style_signature(self) -> str:
        # TODO: move this method to source_sink.py

        method_name = self.method_name
        java_style_class_name = self.smali_type_to_java_type(self.class_name)
        java_style_return_type = self.smali_type_to_java_type(self.return_type)
        listed_argument_types = self.explicit_argument_types_to_listed_argument_types()
        java_style_listed_argument_types = [self.smali_type_to_java_type(arg_type) for arg_type in listed_argument_types]

        # Return Method Invocation in the style found in Flowdroid source/sink lists and Flowdroid log output
        # Example
        # <[full package name]: [return type] [method name]([arg types,])>
        
        # Note the change from smali types to flowdroid types.
        listed_argument_types = []
        # TODO: self.arg_types_pre won't match up precisely with the function's signature!!
        return f"<{java_style_class_name}: " \
               f"{java_style_return_type}" \
               f" {method_name}({','.join(java_style_listed_argument_types)})>"
    
    def explicit_argument_types_to_listed_argument_types(self) -> List[str]:
        smali_argument_register_types: List[str] = self.argument_register_types_pre
        is_static: bool = self.is_static_invoke()

        # Change wide types to take 1 register instead of two
        result_types = smali_argument_register_types.copy()
        i = 0
        current_length = len(result_types)
        while i < current_length:
            if SmaliMethodInvocation.is_wide_datatype(result_types[i]):
                result_types.pop(i + 1)
                current_length = len(result_types)
            i += 1

        # Pull off the first type if the the invocation wasn't static (*this* type is not listed)
        if not is_static:
            result_types.pop(0)

        return result_types



    @staticmethod
    def register_index_to_arg_index(is_static, register_index, signature_arg_types):
        """
        Return the function arg index to which the given register index corresponds. Return None if register
        corresponds to the "this" object.
        """
        if not is_static and register_index == 0:
            return None

        skip_next = False
        cur_arg_index = 0

        # Skip the first register_index if the invoke was static
        register_indices = range(register_index+1) if is_static else range(1, register_index+1)

        for cur_register_index in register_indices:
            if skip_next:
                skip_next = False
                # In this branch, do not update cur_arg_index
                continue

            if signature_arg_types[cur_arg_index] == 'J' or signature_arg_types[cur_arg_index] == 'D':
                if register_index == cur_register_index or register_index == cur_register_index + 1:
                    return cur_arg_index
                else:
                    skip_next = True

            if cur_register_index == register_index:
                return cur_arg_index

            cur_arg_index += 1

        raise AssertionError("Should have used one of the returns in the loop")

    def increment_line_number(self, increment: int):
        self.invoke_line_number += increment

        if self.move_result_line_number != -1:
            self.move_result_line_number += increment

    @staticmethod
    def smali_type_to_java_type(smali_type: str):
        if smali_type.startswith("L"):
            if smali_type[-1] != ";":
                raise AssertionError("Smali type not formatted as expected: " + smali_type)

            smali_type = smali_type.replace("/", ".")
            # Trim leading "L" and trailing ";"
            return smali_type[1:-1]

        elif smali_type.startswith("["):  # array
            # handle this case recursively
            return smali_type[1:] + "[]"

        else:  # primitive type
            if len(smali_type) != 1:
                raise AssertionError("Smali type not formatted as expected: " + smali_type)

            if smali_type == "V":
                return "void"
            elif smali_type == "Z":
                return "boolean"
            elif smali_type == "B":
                return "byte"
            elif smali_type == "S":
                return "short"
            elif smali_type == "C":
                return "char"
            elif smali_type == "I":
                return "int"
            elif smali_type == "J":  # 64 bit
                return "long"
            elif smali_type == "F":
                return "float"
            elif smali_type == "D":  # 64 bit
                return "double"
            else:
                raise AssertionError("Unexpected primitive type: " + smali_type)

    @staticmethod        
    def is_wide_datatype(smali_type: str) -> bool:
        return smali_type == "J" or smali_type == "D"

    @staticmethod        
    def is_object_datatype(smali_type: str) -> bool:
        return smali_type.startswith("L")


    def is_static_invoke(self):
        return "static" in self.invoke_kind
    
    @staticmethod
    def get_prev_instruction(i: int, lines: List[str]) -> Tuple[int, str]: 
        # Look backwards from the instruction before i, looking for the previous instruction. 
        # Ignore lines that start with ".", unless the line starts with ".method", in which case return ""
        # Ignore lines that start with ":", since these are like goto Locations
        for j in range(i-1, -1, -1):
            line = lines[j].strip()
            
            if line == "":
                continue
            if line.startswith(".method"):
                return None, ""
            if line.startswith("."):
                continue
            if line.startswith(":"):
                continue
            if line[0].isalnum():
                return j, line
            
        assert False

    def args_overriden_by_return(self, parent_method: SmaliMethod) -> List[bool]:
        # return list matching dimension of self.arg_registers stating if register is over written by move-result
        result = [False] * len(self.argument_registers)
        
        if self.move_result_line_number == -1:
            return result
        
        if self.move_result_register in self.argument_registers:
            # Register can be used more than once in argument registers
            matches = [i for i in range(len(self.argument_registers)) if self.argument_registers[i] == self.move_result_register]
            for i in matches:
                result[i] = True
        
        if SmaliMethodInvocation.is_wide_datatype(self.return_type):
            next_register = parent_method.get_next_register(self.move_result_register)
            if next_register in self.argument_registers:
                result[self.argument_registers.index(next_register)] = True

        return result
    
    @staticmethod
    def parse_argument_registers(argument_registers: str) -> List[str]:
        if argument_registers.__contains__(" .. "):
            # Range case
            # "v0 .. v9" or "p0 .. p9"
            if argument_registers.startswith("v"):
                prefix = "v"
                regex_result = re.search(r"v(\d+) \.\. v(\d+)",
                                         argument_registers)
            elif argument_registers.startswith("p"):
                prefix = "p"
                regex_result = re.search(r"p(\d+) \.\. p(\d+)",
                                         argument_registers)
            else:
                raise AssertionError(
                    "Range registers did not parse as expected: " +
                    argument_registers)

            if regex_result is None:
                raise AssertionError(
                    "Range registers did not parse as expected: " +
                    argument_registers)
            
            arg_start = int(regex_result.group(1))
            arg_end = int(regex_result.group(2))
            arg_registers = [prefix + str(i) for i in
                             range(arg_start, arg_end + 1)]
        else:
            arg_registers = argument_registers.split(", ")

        return arg_registers

    @staticmethod
    def parse_smali_argument_types(smali_argument_types: str) -> List[str]:
        if smali_argument_types == "":
            return []
        elif smali_argument_types[0] in ['Z', 'B', 'S', 'C', 'I', 'F']:
            return [smali_argument_types[0]] + SmaliMethodInvocation.parse_smali_argument_types(smali_argument_types[1:])
        elif smali_argument_types[0] in ['J','D']:
            # Long or Double type are 64 bits, these take up two registers
            return [smali_argument_types[0]] + [smali_argument_types[0]] + SmaliMethodInvocation.parse_smali_argument_types(smali_argument_types[1:])
        elif smali_argument_types[0] == '[':
            result = SmaliMethodInvocation.parse_smali_argument_types(smali_argument_types[1:])
            if len(result) == 0:
                raise AssertionError("Array with no type: " + smali_argument_types)
            if result[0] in ['J', 'D']:
                # There will be two of these in a row, but array pointers only take 1 register. Truncate the extra type entry.
                result[1] = '[' + result[1]
                return result[1:]
            else: 
                result[0] = '[' + result[0]
                return result
        elif smali_argument_types[0] == 'L':
            # Find the first semicolon, and split the string up accordingly
            semicolon_index = smali_argument_types.find(';')
            if semicolon_index == -1:
                raise AssertionError("Object type has no ending semicolon: " + smali_argument_types)
            return [smali_argument_types[:semicolon_index + 1]] + SmaliMethodInvocation.parse_smali_argument_types(
                smali_argument_types[semicolon_index + 1:])
        else:
            raise AssertionError("Unexpected case when parsing arg types string: " + smali_argument_types)
        
    @staticmethod
    def parse_invocation_line(line_number: int, line: str) -> 'SmaliMethodInvocation':
        # TODO: this should probably be moved to SmaliMethodInvocation

        """
        Examples: 
        invoke-super {p0, p1, p2, p3, p4}, Landroid/widget/TextView;->onSizeChanged(IIII)V
        invoke-virtual/range {v0 .. v5}, Landroid/graphics/Canvas;->drawArc(Landroid/graphics/RectF;FFZLandroid/graphics/Paint;)V
        invoke-static/range {v0 .. v5}, Lrx/Observable;->interval(JJLjava/util/concurrent/TimeUnit;Lrx/Scheduler;)Lrx/Observable;
        """
        result_invocation = SmaliMethodInvocation.get_empty_object()

        result_invocation.invoke_line_number = line_number

        # First word is invoke-[kind]
        result_invocation.invoke_kind = line.split()[0]
        if result_invocation.invoke_kind.find("range") >= 0:
            result_invocation.is_range_kind = True
        else:
            result_invocation.is_range_kind = False

        # find and capture the contents of matched curly braces
        argument_registers: str = re.search(r"\{(.*)\}", line).group(1)
        result_invocation.argument_registers = SmaliMethodInvocation.parse_argument_registers(argument_registers)
        # "invoke-virtual {v0, v1, p1, v2}, Leu/kanade/tachiyomi/util/LocaleHelper;->updateConfiguration(Landroid/app/Application;Landroid/content/res/Configuration;Z)V"
        # Note that the first register here is *this* iff the invoke is not static

        if len(result_invocation.argument_registers) == 1 and result_invocation.argument_registers[0].strip() == '':
            result_invocation.argument_registers = []

        # find and capture the class name and method name which are between "},
        # " and "->"; and "->" and "(", respectively
        match = re.search(r"\}, (.*)->(.*)\(", line)
        result_invocation.class_name = match.group(1)
        result_invocation.method_name = match.group(2)

        # find and capture the arg types,
        # between a left and right paren
        smali_argument_types: str = re.search(r"\((.*)\)", line).group(1)
        result_invocation.argument_register_types_pre = SmaliMethodInvocation.parse_smali_argument_types(smali_argument_types)
        if not result_invocation.is_static_invoke():
            # Type of first argument is implicit
            result_invocation.argument_register_types_pre = [result_invocation.class_name] + result_invocation.argument_register_types_pre

        assert len(result_invocation.argument_register_types_pre) == len(result_invocation.argument_registers)

        
        # find and capture the return type, between a right paren and the end of the
        # string.
        result_invocation.return_type = re.search(r"\)(.*)$", line).group(1).strip()

        return result_invocation


### Begin Instrumentation Strategy Classes




class StringReturnInstrumentationStrategy(SmaliInstrumentationStrategy):
    def instrument(self, contents: List[str]) -> List[str]:
        """Print out stack traces right before
        the return statement of all functions that return strings"""
        is_reading_method = False
        method_start_index = 0
        new_contents = None
        method_number = 1
        i = 0
        while i < len(contents):
            line = contents[i].rstrip()

            # Start method collection for any string return functions that are
            # not abstract, contructors, or native.
            if ".method" in line and "abstract" in line:
                i += 1
                continue

            elif ".method" in line and "constructor" in line:
                i += 1
                continue

            elif ".method" in line and "native" in line:
                i += 1
                continue

            elif ".method" in line and ")Ljava/lang/String;" in line:  # method return string
                method = []
                is_reading_method = True
                method_start_index = i
                method.append(line)
                i += 1
                continue

            # When an appropriate string return method is detected, collect all
            # the code until ".end method" into the "method" variable. When
            # ".end method" gets hit, pass it to "instrument" and begin scanning
            # for more methods.
            if is_reading_method == True:
                if ".end method" in line:
                    is_reading_method = False
                    new_contents = self._instrument_method(contents,
                                                           method_start_index,
                                                           i,
                                                           method_number)
                    method_number += 1

            i += 1

        if new_contents is None:
            return contents
        else:
            return new_contents

    def _instrument_method(self, contents, method_start_index,
                           method_end_index, method_number):
        localsNumber = 0
        locals_index = 0
        parameterCount = 0
        paraNumberList = []
        paraRegList = []

        for i in range(method_start_index, method_end_index + 1):
            # get number of locals
            line = contents[i]
            if ".locals" in line:
                locals_index = i
                localsNumber = int(line.split()[1])

            paraRegList = paraRegList + re.findall(r'p\d+', line)

        for item in paraRegList:
            number = re.findall(r'\d+', item)
            paraNumberList.append(int(number[0]))

        if len(paraNumberList) > 0:
            parameterCount = max(paraNumberList) + 1

        # Most dalvik opcodes can only use first 16 registers
        # Distinction between local registers and parameter registers (vX and
        # pX) is virtual. In reality there is only one set of registers and
        # locals are first, then parameters
        if (16 - localsNumber - parameterCount) >= 1:
            # Overwrite locals declaration to reflect the additional local
            # used by the inserted code
            contents[locals_index] = "    .locals " + str(localsNumber + 1)
            v1 = "v" + str(localsNumber)
        else:
            # Don't instrument method if not enough locals for us to use
            # TODO: modify function to stick required local into a local
            #  register
            return contents

        return_statement_number = 1

        i = method_start_index
        while i < method_end_index:
            # for i in range(method_start_index, method_end_index + 1):
            line = contents[i]

            if "return-object" in line:
                # line will be "return-object v[#]"
                returnVar = line.split()[1]
                text_to_insert = [log_string_value_with_stacktrace(returnVar, v1,
                                                                   method_number,
                                                                   return_statement_number)]

                # insert text_to_insert before the "return-object" line
                return_statement_number += 1

                contents[i:i] = text_to_insert

                # increment relevant loop indices
                i += 1
                method_end_index += 1

            i += 1

        return contents


class LogStringReturnInstrumentationStrategy(SmaliInstrumentationStrategy):

    def instrument_file(self, smali_file: 'SmaliFile'):
        # TODO: This needs to be refactored to return code insertion models!!

        # Note: the smali file object and the text it models will be changing
        # between iterations in these loops
        # Number of methods is not expected to change.
        for method_number in range(len(smali_file.methods)):
            registers = []

            if smali_file.methods[method_number].return_type == \
                    SMALI_STRING_CLASS_NAME:
                # Number of return registers is not expected to change
                for i in range(len(smali_file.methods[method_number].return_registers)):
                    assert len(
                        smali_file.methods[method_number].return_registers) == len(
                        smali_file.methods[method_number].return_line_numbers)

                    return_register = \
                        smali_file.methods[method_number].return_registers[i]

                    if registers is not []:
                        try:
                            registers = smali_file.get_registers(method_number, 1)
                        except ValueError:
                            # If the method has too many registers used,
                            # don't instrument it
                            continue

                    code = log_string_value_with_stacktrace(return_register,
                                                            registers[0],
                                                            method_number, i)

                    # This value will be change for future iterations after
                    # the current iteration makes its changes. The fields of
                    # smali_file should already be updated, and method_number
                    # and i will still be valid.
                    destination_line_number = \
                        smali_file.methods[method_number].return_line_numbers[i]

                    smali_file.insert_code_into_method(code, method_number,
                                                       destination_line_number,
                                                       registers)

            smali_file.update_method_preamble(method_number, registers)

    def needs_to_insert_directory(self) -> bool:
        return False

    def path_to_directory(self) -> str:
        raise AssertionError("Instrumenter does not need to insert any "
                             "directories.")


class StringReturnValuesInstrumentationStrategy(
    SmaliInstrumentationStrategy):

    def instrument_file(self, smali_file: 'SmaliFile') -> List[CodeInsertionModel]:
        # Scan through the file and note all of the code that must be inserted.


        code_insertions: List[CodeInsertionModel] = []

        instrumentation_id = 0
        for method_index, method in enumerate(smali_file.methods):

            if method.is_abstract:
                continue

            try:
                method_instr_registers = smali_file.get_registers(
                    method_index, 2)
            except ValueError:
                # If the method has too many registers used,
                # don't instrument it
                continue

            for invocation_statement in method.invocation_statements:

                # if a method is invoked that returns a string and the result is saved
                # to a register
                if invocation_statement.return_type == SMALI_STRING_CLASS_NAME and \
                        invocation_statement.move_result_line_number != -1:
                    # Insert code just after move-result statement
                    target_line_number = invocation_statement.move_result_line_number + 1

                    target_code = log_invocation_string_return_with_stacktrace(
                        invocation_statement.move_result_register,
                        method_instr_registers[0],
                        method_instr_registers[1],
                        method_index,
                        invocation_statement,
                        instrumentation_id)
                    instrumentation_id += 1

                    code_insertions.append(CodeInsertionModel(target_code, method_index,
                                                              target_line_number,
                                                              method_instr_registers))
                    # code_insertions.append((target_code, method_index,
                    #                         target_line_number,
                    #                         [method_instr_registers[0]]))

            # smali_file.update_method_preamble(method_index, method_instr_registers)
        return code_insertions
        # smali_file.insert_code(code_insertions)
        # for code, method_index, line_number, registers in code_insertions.__reversed__():
        #     smali_file.insert_code_into_method(code, method_index,
        #                                        line_number,
        #                                        registers)

    def needs_to_insert_directory(self) -> bool:
        return False

    def path_to_directory(self) -> str:
        raise AssertionError("Instrumenter does not need to insert any "
                             "directories.")


class StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy(SmaliInstrumentationStrategy):

    static_function_signature = "Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPII(Ljava/lang/Object;Ljava/lang/String;)I"

    def __init__(self, do_instrument_args):
        self.invocation_id = -1

        self.do_instrument_args = do_instrument_args

    def instrument_file(self, smali_file: 'SmaliFile') -> List[CodeInsertionModel]:
        code_insertions = instrument_by_invocation(smali_file, self._instrument_invocation_statement)
        return code_insertions

    def _instrument_invocation_statement(self, method_index: int, method: SmaliMethod, method_instrumentation_registers: List[str], invocation_statement: SmaliMethodInvocation) -> List[CodeInsertionModel]:
        self.invocation_id += 1
        invocation_id = self.invocation_id
        code_insertions: List[CodeInsertionModel] = []

        # If arg type is an object before, it can be instrumented
        # If arg type is still an object after, it can be instrumented
        # "this" register cannot be instrumented if method is constructor (<init>)
        # some instrumentation schemes will not want to instrument an arg before if it can't be instrumented after,
        # some instrumentation schemes would want to save the 1 or 2 arg registers that could become unavailable due to a return
        # some instr schemes wouldn't bother instrumenting an arg before if it can't be accessed after. 
        # some instrumentation schemes will want to do complex type checking for if a register should be instrumented

        # instrumentation report requirements
        # able to interface  with the corresponding SmaliFile/SmaliMethod/SmaliMethodInvocation from static analysis time
        # OR include all the relevant information (sad, current impl)
        # these requirement will prolly need to be tweaked -> refactor current impl so it can be modified in ~ 1 place
        
        args_overriden_by_return = invocation_statement.args_overriden_by_return(method)

        # TODO add enclosing method, class, & original line number to the Instr report
        report = InstrumentationReport(
                invocation_java_signature=invocation_statement.get_java_style_signature(), 
                invoke_id=invocation_id,
                enclosing_method_name=method.method_name,
                enclosing_class_name=method.enclosing_class_name,
                is_arg_register=True, # Needs tweaked
                is_return_register=False, # Needs tweaked
                invocation_argument_register_index=-1, # Needs tweaked
                is_before_invoke=True, # Needs tweaked
                invocation_argument_register_name="", # Needs tweaked
                invocation_argument_register_type="", # Needs tweaked
                is_static=invocation_statement.is_static_invoke(), 
            )
        
        def build_code_insertion(cur_report, cur_register) -> CodeInsertionModel:
            code = invoke_static_function(repr(cur_report),
                                                        cur_register,
                                                        method_instrumentation_registers[0],
                                                        self.static_function_signature)

            # Place code after move_result if there is one, otherwise place code after invoke
            target_line_number = invocation_statement.invoke_line_number + 1 if invocation_statement.move_result_line_number == -1 else invocation_statement.move_result_line_number + 1

            return CodeInsertionModel(code, method_index,
                                                        target_line_number,
                                                        method_instrumentation_registers) 

        if self.do_instrument_args:
            # consider invocation argument registers
            for register_index, register in enumerate(invocation_statement.argument_registers):

                ### Begin Checks
                skip_instr_before = False
                skip_instr_after = False

                # Skip Primitive types
                
                if not SmaliMethodInvocation.is_object_datatype(invocation_statement.argument_register_types_pre[register_index]):
                    continue

                # If it's a constructor, the first register will be unallocated before the invocation
                if invocation_statement.method_name == "<init>" and register_index == 0:
                    skip_instr_before = True


                # Don't instrument a register (as an argument register) after the call if it's overwritten by the move result
                if args_overriden_by_return[register_index]:
                    skip_instr_after = True
                    # TODO: in the future, we may want to use an extra variable(s) to store the up to two overwritten variables to check them after
                    

                ### End checks
                if not skip_instr_before:
                    report.invocation_argument_register_index = register_index
                    report.is_before_invoke = True
                    report.invocation_argument_register_name = register
                    report.invocation_argument_register_type = invocation_statement.argument_register_types_pre[register_index]
                    code = invoke_static_function(repr(report),
                                                            register,
                                                            method_instrumentation_registers[0],
                                                            self.static_function_signature)

                    code_insertions.append(CodeInsertionModel(code, method_index,
                                                            invocation_statement.invoke_line_number,
                                                            method_instrumentation_registers))

                if not skip_instr_after:
                    report.invocation_argument_register_index = register_index
                    report.is_before_invoke=False
                    report.invocation_argument_register_name = register
                    report.invocation_argument_register_type = invocation_statement.argument_register_types_pre[register_index]

                    code_insertions.append(build_code_insertion(report, register))
                
                
        # Next, consider the return register
        if invocation_statement.move_result_line_number > -1 and SmaliMethodInvocation.is_object_datatype(invocation_statement.return_type):
            report = InstrumentationReport(
                    invocation_java_signature=invocation_statement.get_java_style_signature(),
                    invoke_id=invocation_id,
                    enclosing_method_name=method.method_name,
                    enclosing_class_name=method.enclosing_class_name,
                    is_arg_register=False,
                    is_return_register=True,
                    invocation_argument_register_index=-1,
                    is_before_invoke=False,
                    invocation_argument_register_name=invocation_statement.move_result_register,
                    invocation_argument_register_type=invocation_statement.return_type,
                    is_static=invocation_statement.is_static_invoke(),
                )
            code_insertions.append(build_code_insertion(report, invocation_statement.move_result_register))

        return code_insertions

    def needs_to_insert_directory(self) -> bool:
        return True

    def path_to_directory(self) -> str:
        # target_directory_suffix = "edu/utsa/sefm/heapsnapshot"
        # files = ["Snapshot.smali", "Snapshot$FieldInfo.smali"]
        dest = os.path.join("data/intercept/smali-files/heap-snapshot")
        return dest

# TODO this is used by two Instrumentation Strategies. It should probably fit in the class somehow.
def instrument_by_invocation(smali_file: SmaliFile, instrument_invocation: Callable[[int, SmaliMethod, List[str], SmaliMethodInvocation], List[CodeInsertionModel]]) -> List[CodeInsertionModel]:
    code_insertions: List[CodeInsertionModel] = []

    for method_index, method in enumerate(smali_file.methods):

        # Skip abstract methods
        if method.is_abstract:
            continue

        try:
            method_instrumentation_registers = smali_file.get_registers(
                method_index, 1)
        except ValueError:
            # If the method has too many registers used,
            # don't instrument it
            continue

        for invocation_statement in method.invocation_statements:

            code_insertions += instrument_invocation(method_index, method, method_instrumentation_registers, invocation_statement)

    return code_insertions
    

class ObserveSourceSinks(SmaliInstrumentationStrategy):
    # Do sources / sink get hit during the dynamic run? 
    # What do sources produce? What to sinks receive?
    def __init__(self, sources, sinks):
        pass

    # Before specific methods are hit, print a simple message. (no need for java code)

    # At sources, if they have a return register, examine it. 
    # At sinks, if they have arg registers, examine them.
    # This examination can use recursive field checking. The printing of this message is NOT conditional on if the string is tainted or not.


class HarnessSources(SmaliInstrumentationStrategy):
    # Overwrite the returns of the following sources (who return strings) with traceable strings that can be picked up by other instrumentation strategies. 
    sources_to_instrument: List[MethodSignature]
    invocation_id: int

    def __init__(self, sources: List[MethodSignature]):
        self.sources_to_instrument = sources
        self.invocation_id = -1

        # TODO This setting needs to be moved out to be visible for experiments
        self.overwrite_return = True



        # identify smali invocations on source method. 
        # check if invocation has return
        # if so, 
        # Use temp register to send log that method has returned, and it's register is being overwritten with the value. 
        # after return, place string in temp register. Overwrite return register with temp register.
        # For now, don't send message if method is called but the source string isn't used.

        # make sure other instrumentation strategies are printing out what the private value was. 

    def instrument_file(self, smali_file: 'SmaliFile') -> List[CodeInsertionModel]:

        code_insertions = instrument_by_invocation(smali_file, self._instrument_invocation_statement)

        # start debug
        if len(code_insertions) > 0:
            logger.debug(f"Code insertions on file {smali_file.file_path} on lines {",".join([str(insertion.line_number) for insertion in code_insertions])}")
        # end debug

        return code_insertions


    def _instrument_invocation_statement(self, method_index: int, method: SmaliMethod, method_instrumentation_registers: List[str], invocation_statement: SmaliMethodInvocation) -> List[CodeInsertionModel]:
        self.invocation_id += 1
        invocation_id = self.invocation_id



        # Is the method being invoked on our list of sources? 

        invocation_matches_source_to_instrument = False
        for source in self.sources_to_instrument:
            if self._compare_invocation_and_signature(invocation_statement, source):
                invocation_matches_source_to_instrument = True

        if not invocation_matches_source_to_instrument:
            return []
        
        # Don't instrument if the result isn't put in a register
        # TODO: I'd like to send a message if the source gets called, even if it doesn't have a return
        if invocation_statement.move_result_line_number == -1:
            logger.debug(f"Method {invocation_statement.method_name} is called but return isn't used. Not instrumenting.")
            return []
        
        if self.overwrite_return:
            # create harnessed private string

            # Is the method being invoked returning a string? (assert True)
            assert invocation_statement.return_type == SMALI_STRING_CLASS_NAME

            harness_id = invocation_id
            harness_value = f"***{harness_id:012d}***"
            report = f"Source Method {invocation_statement.class_name + " " + invocation_statement.method_name} called in class and method <{method.enclosing_class_name + " " + method.method_name}>. Return is being replaced with {harness_value}. Previous value was:"
        else:
            report = f"Source Method {invocation_statement.class_name + " " + invocation_statement.method_name} called in class and method <{method.enclosing_class_name + " " + method.method_name}>. Return value was:"
        # Java code will append ";" + contents of return register 
        return_register = invocation_statement.move_result_register
        empty_register = method_instrumentation_registers[0]

        # TODO: in theory, we could save in the python code what harness_id's correspond to what source methods, but in *theory*, the harnessed values should only come up if the harnessed code gets hit, so we don't need to. We should be able to pull all the relevant information from the logs.
    
        # code insertion to put log message in register and print it to log
        code_insertions = []
        signature = "Ledu/utsa/sefm/heapsnapshot/Snapshot;->logHarnessedSource(Ljava/lang/Object;Ljava/lang/String;)V"
        code = invoke_static_function(report, return_register, empty_register, signature)
        target_line_number = invocation_statement.move_result_line_number + 1
        assert invocation_statement.move_result_line_number != 0
        code_insertion_log_report = CodeInsertionModel(code, method_index,
                                                        target_line_number,
                                                        method_instrumentation_registers)
        code_insertions.append(code_insertion_log_report)

        if self.overwrite_return:
            # code insertion to overwrite string
            code = overwrite_object_register_with_value(return_register, empty_register, harness_value)
            code_insertion_overwrite_result = CodeInsertionModel(code, method_index,
                                                            target_line_number,
                                                            method_instrumentation_registers)
            # TODO: the ordering here is working the opposite the way i thought it should!!!
            code_insertions = [code_insertion_overwrite_result] + code_insertions
            # code_insertions.append(code_insertion_overwrite_result)
                      
        return code_insertions
    
    @staticmethod
    def _compare_invocation_and_signature(invocation: SmaliMethodInvocation, signature: MethodSignature):

        # debug
        # if invocation.method_name == signature.method_name:
        #     if SmaliMethodInvocation.smali_type_to_java_type(invocation.class_name) == signature.base_type:
        #         logger.debug(f"Comparison should return true for {signature.method_name}")
            # else: 
                # logger.debug(f"Comparison same method name, but different class names {SmaliMethodInvocation.smali_type_to_java_type(invocation.class_name)} and {signature.base_type}")
        # end debug

        if (SmaliMethodInvocation.smali_type_to_java_type(invocation.class_name) != signature.base_type 
                or invocation.method_name != signature.method_name):
            return False

        if invocation.get_java_style_signature() != str(signature):
            # Not sure how problematic this tbh
            logger.warning(f"Treating smali method invocation {invocation.get_java_style_signature()} as equivalent to source signature {str(signature)}.")
        
        return True

    def needs_to_insert_directory(self) -> bool:
        # This strategy DOES rely on decompiled code, but right now it's paired with StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy, and that strategy should get all the relevant code inserted. 
        return False
    
class HarnessObservations(SmaliInstrumentationStrategy):
    pass

    

    def instrument_file(self, smali_file: 'SmaliFile', observations: List[Tuple[InstrumentationReport, str, str]]):
        pass

    def needs_to_insert_directory(self):
        raise False

    


def log_string_value_with_stacktrace(string_value_register: str, empty_register_1: str,
                                     method_number: int, instrumentation_id: int):
    v1 = empty_register_1

    # Debug
    if v1 == "v16":
        raise AssertionError()
    # End Debug

    return f"""
if-eqz {string_value_register}, :cond_returnStringDetection{str(method_number)}_{
    str(instrumentation_id)}
    new-instance {v1}, Ljava/lang/Exception;
    invoke-direct {{{v1}, {string_value_register}}}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V
    invoke-virtual {{{v1}}}, Ljava/lang/Exception;->printStackTrace()V
:cond_returnStringDetection{str(method_number)}_{str(instrumentation_id)}

"""


def log_invocation_string_return_with_stacktrace(string_value_register: str,
                                                 empty_register_1: str,
                                                 empty_register_2: str,
                                                 method_number: int,
                                                 invocation_model: SmaliMethodInvocation,
                                                 instrumentation_id: int):
    v1 = empty_register_1
    v2 = empty_register_2

    return f"""
if-eqz {string_value_register}, :cond_returnStringDetection{str(method_number)}_{str(instrumentation_id)}
    new-instance {v2} ,Ljava/lang/StringBuilder;
    invoke-direct {{{v2}}}, Ljava/lang/StringBuilder;-><init>()V
    const-string {v1}, "At method {str(invocation_model)} value returned: "
    invoke-virtual {{{v2},{v1}}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {{{v2}, {string_value_register}}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {{{v2}}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object {v2}
    new-instance {v1}, Ljava/lang/Exception;
    invoke-direct {{{v1}, {v2}}}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V
    invoke-virtual {{{v1}}}, Ljava/lang/Exception;->printStackTrace()V
:cond_returnStringDetection{str(method_number)}_{str(instrumentation_id)}

"""


def log_string_return_and_stacktrace(return_register, empty_register_1,
                                     empty_register_2, method_number,
                                     return_statement_number):
    """
    :param return_register: str
    :param empty_register_1: str
    :param empty_register_2: str
    :param method_number: str
    :param return_statement_number: str
    :return: smali code to be inserted
    """
    v1 = empty_register_1
    v2 = empty_register_2
    return f"""
# if return is a null string, skip the inserted code
if-eqz {return_register}, :cond_returnStringDetection_{method_number}_{return_statement_number}

# Create logging message with return value
new-instance {v2} ,Ljava/lang/StringBuilder;
invoke-direct {{{v2}}}, Ljava/lang/StringBuilder;-><init>()V

const-string {v1}, "ReturnValue:"

invoke-virtual {{{v2},{v1}}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

invoke-virtual {{{v2}, {return_register}}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

invoke-virtual {{{v2}}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

move-result-object {v2}

const-string {v1}, "DySta-Instrumentation"

# Log return value with a tag
invoke-static {{{v1},{v2}}}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

const-string {v2},"StackTrace:"

invoke-static {{{v1},{v2}}}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

new-instance {v2}, Ljava/lang/Exception;

invoke-direct {{{v2}}}, Ljava/lang/Exception;-><init>()V

invoke-virtual {{{v2}}}, Ljava/lang/Exception;->printStackTrace()V

:cond_returnStringDetection_{method_number}_{return_statement_number}

"""


def invoke_static_function(report: str, register_to_analyze: str, empty_register: str, static_function_signature: str):
    # static_function_signature = "Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPII(Ljava/lang/Object;Ljava/lang/String;)I"
    # "Ledu/utsa/sefm/heapsnapshot/Snapshot;->logHarnessedSource(Ljava/lang/Object;Ljava/lang/String;)V"
    return f"""
    const-string {empty_register}, "{report}"
    invoke-static {{{register_to_analyze}, {empty_register}}}, {static_function_signature}
"""

def overwrite_object_register_with_value(dest_register: str, source_register: str, value: str) -> str:
    return f"""
    const-string {source_register}, "{value}"
    move-object {dest_register}, {source_register}
"""
#     return f"""
#     const-string {source_register}, "{value}"
#     move-object {source_register}, {dest_register}
# """


def sources_to_harness(sources_list: str) -> List[MethodSignature]:

    with open(sources_list, "r") as file:
        sources_text = file.read()
    signatures = [MethodSignature.from_source_string(line.strip()) for line in sources_text.splitlines()]
    return signatures

    

if __name__ == '__main__':
    pass


