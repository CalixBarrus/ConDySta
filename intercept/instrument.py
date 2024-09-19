import os
import re
import shutil
from typing import List, Tuple

from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path
from util.input import ApkModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

class InformalInstrumentationStrategyInterface:
    def instrument_file(self, smali_file: 'SmaliFile'):
        """Hook gets called on each SmaliFile model in a given DecodedApkModel"""
        raise NotImplementedError("Interface not implemented")

    def needs_to_insert_directory(self) -> bool:
        """
        :return: Whether this instrumenter requires additional
        smali directories to be dropped into the apk.
        """
        raise NotImplementedError("Interface not implemented")

    def path_to_directory(self) -> str:
        """
        This method shouldn't be called unless
        needs_to_insert_directory() returns true.
        :return: Path to root of smali directories that need to be dropped
        into a smali_classes file.
        """
        raise NotImplementedError("Interface not implemented")

def instrument_batch(config: HybridAnalysisConfig, apks: List[ApkModel]):

    # Read in and parse decoded apks
    decoded_apk_models: List[DecodedApkModel] = []
    for apk in apks:
        decoded_apk_models.append(instrument_apk(config, apk))

    # We may later decide to save the decoded_apk_models for use in interpreting dynamic analysis results

def instrument_apk(config: HybridAnalysisConfig, apk: ApkModel) -> 'DecodedApkModel':
    instrumentation_strategy: InformalInstrumentationStrategyInterface = instr_strategy_from_strategy_name(config.instrumentation_strategy)

    decoded_apk_model = DecodedApkModel(decoded_apk_path(config._decoded_apks_path, apk))

    decoded_apk_model.instrument(instrumentation_strategy)

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


    # def scan_for_smali_files(self, project_smali_folder_path: str,
    #                          class_path: str) -> "SmaliFile":
    #     # """
    #     # Recursively traverse the subdirectories of
    #     # project_smali_folder_path, getting the methods in each smali file.
    #     # :param project_smali_folder_path: path to the "smali" or
    #     # "smali_classes[n]" directory.
    #     # :param class_path: relative path referring to the subdirectories
    #     # traversed so far.
    #     # :return: List of SmaliFile objects containing data about each file in the apk
    #     # """
    #     # result_smali_files: List[SmaliFile] = []
    #     # for item in os.listdir(os.path.join(project_smali_folder_path,
    #     #                                     class_path)):
    #     #     item_path = os.path.join(project_smali_folder_path, class_path,
    #     #                              item)
    #     #     if os.path.isdir(item_path):
    #     #         result_smali_files += self.scan_for_smali_files(
    #     #             project_smali_folder_path,
    #     #             os.path.join(class_path, item))

    #     #     elif item.endswith(".smali"):
    #     #         result_smali_files.append(SmaliFile(
    #     #             project_smali_folder_path, class_path, item))

    #     return result_smali_files

    def instrument(self, instrumenter: InformalInstrumentationStrategyInterface):
        if instrumenter.needs_to_insert_directory():
            self.insert_smali_directory(instrumenter.path_to_directory())

        for smali_directory in self.smali_directories:
            for smali_file in smali_directory:
                instrumenter.instrument_file(smali_file)

        self.is_instrumented = True

    def insert_smali_directory(self, smali_source_directory_path):
        """
        :param smali_source_directory_path: path to smali code that will be inserted
        (copied) into the apk
        """
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
    methods: List['SmaliMethod']

    def __init__(self, smali_file_path):
        self.file_path = smali_file_path
        self.methods = []

        with open(self.file_path, 'r') as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            if line.startswith(".method"):
                self.methods.append(self.parse_smali_method(lines, i, self.file_path))

    def parse_smali_method(self, lines, function_start_index, parent_file_path) -> 'SmaliMethod':
        result_method = SmaliMethod()
        result_method.start_line_number = function_start_index
        result_method.parent_file_path = parent_file_path

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
                result_method.invocation_statements.append(
                    self.parse_invocation_line(i, line))
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

    def parse_method_signature_args(self, method_args):
        """
        :param method_args: String, expected to be the string between the
        left and right parentheses of a smali method signature
        :return: List of strings, each string being the type of each formal
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

    def parse_invocation_line(self, line_number: int,
                              line: str) -> 'SmaliMethodInvocation':

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
        arg_registers_string = re.search(r"\{(.*)\}", line).group(1)
        result_invocation.arg_registers = self.parse_arg_registers_str(arg_registers_string)
        # Note that the first register here is *this* iff the invoke is not static

        if len(result_invocation.arg_registers) == 1 and result_invocation.arg_registers[0].strip() == '':
            result_invocation.arg_registers = []

        # find and capture the class name and method name which are between "},
        # " and "->"; and "->" and "(", respectively
        match = re.search(r"\}, (.*)->(.*)\(", line)
        result_invocation.class_name = match.group(1)
        result_invocation.method_name = match.group(2)

        # find and capture the arg types,
        # between a left and right paren
        arg_types_str = re.search(r"\((.*)\)", line).group(1)
        result_invocation.arg_types_pre = self.parse_arg_types_str(arg_types_str)
        if not result_invocation.is_static_invoke():
            # Type of first argument is implicit
            result_invocation.arg_types_pre = [result_invocation.class_name] + result_invocation.arg_types_pre

        assert len(result_invocation.arg_types_pre) == len(result_invocation.arg_registers)

        # This needs to be checked and maybe updated when move-results are parsed TODO
        result_invocation.arg_types_post = result_invocation.arg_types_pre
        
        # find and capture the return type, between a right paren and the end of the
        # string.
        result_invocation.return_type = re.search(r"\)(.*)$", line).group(1).strip()

        return result_invocation

    def parse_arg_types_str(self, arg_types_str: str) -> List[str]:
        if arg_types_str == "":
            return []
        elif arg_types_str[0] in ['Z', 'B', 'S', 'C', 'I', 'F']:
            return [arg_types_str[0]] + self.parse_arg_types_str(arg_types_str[1:])
        elif arg_types_str[0] in ['J','D']:
            # Long or Double type are 64 bits, these take up two registers
            return [arg_types_str[0]] + [arg_types_str[0]] + self.parse_arg_types_str(arg_types_str[1:])
        elif arg_types_str[0] == '[':
            result = self.parse_arg_types_str(arg_types_str[1:])
            if len(result) == 0:
                raise AssertionError("Array with no type: " + arg_types_str)
            result[0] = '[' + result[0]
            return result
        elif arg_types_str[0] == 'L':
            # Find the first semicolon, and split the string up accordingly
            semicolon_index = arg_types_str.find(';')
            if semicolon_index == -1:
                raise AssertionError("Object type has no ending semicolon: " + arg_types_str)
            return [arg_types_str[:semicolon_index + 1]] + self.parse_arg_types_str(
                arg_types_str[semicolon_index + 1:])
        else:
            raise AssertionError("Unexpected case when parsing arg types string: " + arg_types_str)
        
    def parse_arg_registers_str(arg_registers_string):
        if arg_registers_string.__contains__(" .. "):
            # Range case
            # "v0 .. v9" or "p0 .. p9"
            if arg_registers_string.startswith("v"):
                prefix = "v"
                regex_result = re.search(r"v(\d+) \.\. v(\d+)",
                                         arg_registers_string)
            elif arg_registers_string.startswith("p"):
                prefix = "p"
                regex_result = re.search(r"p(\d+) \.\. p(\d+)",
                                         arg_registers_string)
            else:
                raise AssertionError(
                    "Range registers did not parse as expected: " +
                    arg_registers_string)

            if regex_result is None:
                raise AssertionError(
                    "Range registers did not parse as expected: " +
                    arg_registers_string)
            
            arg_start = int(regex_result.group(1))
            arg_end = int(regex_result.group(2))
            arg_registers = [prefix + str(i) for i in
                             range(arg_start, arg_end + 1)]
        else:
            arg_registers = arg_registers_string.split(", ")

        return arg_registers

    def parse_move_result(self, prev_method_invocation: 'SmaliMethodInvocation',
                          line_number: int, move_result_line: str, method: 'SmaliMethod'):
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

        # Check if the invocation arg_types_post need updating
        # Update the type if the arg register is being overwritten by the move result
        if prev_method_invocation.move_result_register in prev_method_invocation.arg_registers:
            prev_method_invocation.arg_types_post[prev_method_invocation.arg_registers.index(prev_method_invocation.move_result_register)] = prev_method_invocation.return_type

        # Update the type if there is an arg register after the move result register and the return is of a wide data type
        if SmaliMethodInvocation.is_wide_datatype(prev_method_invocation.return_type):
            register_after_result_register = method.get_next_register(prev_method_invocation.move_result_register)
            if register_after_result_register in prev_method_invocation.arg_registers:
                prev_method_invocation.arg_types_post[prev_method_invocation.arg_registers.index(register_after_result_register)] = prev_method_invocation.return_type
        

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
    smali_file_path: str
    method_name: str
    is_static: bool
    is_abstract: bool
    start_line_number: int
    locals_line_number: int
    invocation_statements: List['SmaliMethodInvocation']
    return_line_numbers: List[int]
    end_line_number: int
    name: str
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

    


class SmaliMethodInvocation:
    """
    Class representing a single line of smali code containing a method invocation.

    This class is intended to capture information that needs to
    be referenced and modified during instrumentation. It is the user's
    responsibility to ensure that modifications to the file are updated in
    this object and vice versa.
    """
    invoke_line_number: int
    invoke_kind: str  # could be an enum
    is_range_kind: bool
    arg_registers: List[str]
    class_name: str
    method_name: str
    arg_types_pre: List[str]
    return_type: str
    move_result_line_number: int
    move_result_kind: str
    move_result_register: str

    def __init__(self,
                 invoke_line_number: int,
                 invoke_kind: str,
                 is_range_kind: bool,
                 arg_registers: List[str],
                 class_name: str,
                 method_name: str,
                 arg_types_pre: List[str],
                 arg_types_post: List[str],
                 return_type: str,
                 move_result_line_number: int,
                 move_result_kind: str,
                 move_result_register: str,
                 ):
        self.invoke_line_number = invoke_line_number
        self.invoke_kind = invoke_kind
        self.is_range_kind = is_range_kind
        self.arg_registers = arg_registers
        self.class_name = class_name
        self.method_name = method_name
        self.arg_types_pre = arg_types_pre
        self.arg_types_post = arg_types_post
        self.return_type = return_type
        self.move_result_line_number = move_result_line_number
        self.move_result_kind = move_result_kind
        self.move_result_register = move_result_register

    def __repr__(self):
        return f"SmaliMethodInvocation(invoke_line_number={repr(self.invoke_line_number)}," \
                f"invoke_kind={repr(self.invoke_kind)}," \
                f"is_range_kind={repr(self.is_range_kind)}," \
                f"arg_registers={repr(self.arg_registers)}," \
                f"class_name={repr(self.class_name)},method_name={repr(self.method_name)}," \
                f"arg_types_pre={repr(self.arg_types_pre)}," \
                f"arg_types_post={repr(self.arg_types_post)}," \
                f"return_type={repr(self.return_type)}," \
                f"move_result_line_number={repr(self.move_result_line_number)},move_result_kind={repr(self.move_result_kind)},move_result_register={repr(self.move_result_register)},)"

    @staticmethod
    def get_empty_object() -> 'SmaliMethodInvocation':
        return SmaliMethodInvocation(-1, "", False, [], "", "", [], [], "", -1, "", "")

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

    def get_signature(self) -> str:
        # TODO: move this method to source_sink.py
        # Example
        # <[full package name]: [return type] [method name]([arg types,])>
        #
        # Note the change from smali types to flowdroid types.
        # TODO: self.arg_types_pre won't match up precisely with the function's signature!!
        return f"<{self.smali_type_to_flowdroid_type(self.class_name)}: " \
               f"{self.smali_type_to_flowdroid_type(self.return_type)}" \
               f" {self.method_name}({','.join([self.smali_type_to_flowdroid_type(arg_type) for arg_type in self.arg_types_pre])})>"

    # def register_type(self, register_index):
    #     # is_static = self.invoke_kind.startswith("invoke-static")
    #     # base_type = self.class_name
    #     # signature_arg_types = self.arg_types_pre

    #     return self.arg_types_pre[register_index]

        # return self.register_index_to_type(is_static, register_index, base_type, signature_arg_types)

        # arg_type_index = self.arg_type_register_index_map()[register_index]
        # if arg_type_index is None:
        #     register_type: str = self.class_name
        # else:
        #     register_type: str = self.arg_types[arg_type_index]
        #
        # return register_type

    # def arg_register_index_to_arg_index(self, arg_register_index):
    #     arg_type_index = self.arg_type_register_index_map()[arg_register_index]
    #     if arg_type_index is None:
    #         raise AssertionError("Expected arg register")
    #     return arg_type_index

    # def arg_type_register_index_map(self) -> List[int]:
    #     # arg_type = arg_types[map[arg_register_index]]
    #     map = []
    #     if not self.invoke_kind.startswith("invoke-static"):
    #         map = [None]
    #     for arg_type_index, arg_type in enumerate(self.arg_types):
    #         if arg_type == 'J' or arg_type == 'D':
    #             # J (Long) and D (Double) take up two registers
    #             map.append(arg_type_index)
    #             map.append(arg_type_index)
    #         else:
    #             map.append(arg_type_index)
    #
    #     return map

    # @staticmethod
    # def register_index_to_type(is_static, register_index, base_type, signature_arg_types):
    #     arg_index = SmaliMethodInvocation.register_index_to_arg_index(is_static, register_index, signature_arg_types)
    #     if arg_index is None:
    #         return base_type
    #     else:
    #         return signature_arg_types[arg_index]

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
    
    def register_types_pre() -> List[str]:
        pass

    def register_types_post() -> List[str]:
        pass


    def increment_line_number(self, increment: int):
        self.invoke_line_number += increment

        if self.move_result_line_number != -1:
            self.move_result_line_number += increment

    @staticmethod
    def smali_type_to_flowdroid_type(smali_type: str):
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
        result = [False] * len(self.arg_registers)
        
        if self.move_result_line_number == -1:
            return result
        
        if self.move_result_register in self.arg_registers:
            result[self.arg_registers.index(self.move_result_register)] = True
        
        if SmaliMethodInvocation.is_wide_datatype(self.return_type):
            next_register = parent_method.get_next_register(self.move_result_register)
            if next_register in self.arg_registers:
                result[self.arg_registers.index(next_register)] = True

        return result



class InstrumentationReport:
    """ This model class is intended to contain information that will be left 
    in hard coded strings in the instrumented code, to be later recovered and reconstructed by a log analysis."""
    invoke_signature: str
    invoke_id: int
    is_arg_register: bool
    is_return_register: bool
    register_index: int
    is_before_invoke: bool
    register_name: str
    register_type: str
    is_static: bool

    def __init__(self,
                 invoke_signature: str,
                 invoke_id: int,
                 is_arg_register: bool,
                 is_return_register: bool,
                 register_index: int,
                 is_before_invoke: bool,
                 register_name: str,
                 register_type: str,
                 is_static: bool,
                 ):
        self.invoke_signature = invoke_signature
        self.invoke_id = invoke_id
        self.is_arg_register = is_arg_register
        self.is_return_register = is_return_register
        self.register_index = register_index
        self.is_before_invoke = is_before_invoke
        self.register_name = register_name
        self.register_type = register_type
        self.is_static = is_static

    def __repr__(self):
        return f"InstrumentationReport(invoke_signature={repr(self.invoke_signature)},invoke_id={repr(self.invoke_id)},is_arg_register={repr(self.is_arg_register)},is_return_register={repr(self.is_return_register)},register_index={repr(self.register_index)},is_before_invoke={repr(self.is_before_invoke)},register_name={repr(self.register_name)},register_type={repr(self.register_type)},is_static={repr(self.is_static)})"

### End Model Classes

### Begin Instrumentation Strategy Classes




class StringReturnInstrumentationStrategy(InformalInstrumentationStrategyInterface):
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


class LogStringReturnInstrumentationStrategy(InformalInstrumentationStrategyInterface):

    def instrument_file(self, smali_file: 'SmaliFile'):
        SMALI_STRING_CLASS_NAME = "Ljava/lang/String;"

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
    InformalInstrumentationStrategyInterface):

    def instrument_file(self, smali_file: 'SmaliFile'):
        SMALI_STRING_CLASS_NAME = "Ljava/lang/String;"

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

        smali_file.insert_code(code_insertions)
        # for code, method_index, line_number, registers in code_insertions.__reversed__():
        #     smali_file.insert_code_into_method(code, method_index,
        #                                        line_number,
        #                                        registers)

    def needs_to_insert_directory(self) -> bool:
        return False

    def path_to_directory(self) -> str:
        raise AssertionError("Instrumenter does not need to insert any "
                             "directories.")


class StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy(
    InformalInstrumentationStrategyInterface):

    static_function_signature = "Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPII(Ljava/lang/Object;Ljava/lang/String;)I"

    def __init__(self):
        self.invocation_id = -1

    def instrument_file(self, smali_file: 'SmaliFile'):
        code_insertions: List[CodeInsertionModel] = []

        for method_index, method in enumerate(smali_file.methods):

            # Skip abstract methods
            if method.is_abstract:
                continue

            try:
                method_instr_registers = smali_file.get_registers(
                    method_index, 1)
            except ValueError:
                # If the method has too many registers used,
                # don't instrument it
                continue

            for invocation_statement in method.invocation_statements:
                self.invocation_id += 1

                code_insertions += self._instrument_invocation_statement(method_index, method, method_instr_registers, invocation_statement, self.invocation_id)

        smali_file.insert_code(code_insertions)

    def _instrument_invocation_statement(self, method_index: int, method: SmaliMethod, method_instr_registers: List[str], invocation_statement: SmaliMethodInvocation, invocation_id: int) -> List[CodeInsertionModel]:
        code_insertions: List[CodeInsertionModel] = []



        # registers = arg_registers.copy()
        # if invocation_statement.move_result_register != "" and not invocation_statement.move_result_register in arg_registers:
        #     registers.append(invocation_statement.move_result_register)

        # invocation_statement.arg_types_pre

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
        invocation_statement.arg_types_pre
        invocation_statement.arg_types_post

        report = InstrumentationReport(
                invoke_signature=invocation_statement.get_signature(), 
                invoke_id=invocation_id,
                is_arg_register=True, # Needs tweaked
                is_return_register=False, # Needs tweaked
                register_index=register_index, # Needs tweaked
                is_before_invoke=True, # Needs tweaked
                register_name=register, # Needs tweaked
                register_type=invocation_statement.arg_types_pre[register_index], # Needs tweaked
                is_static=invocation_statement.is_static_invoke(), 
            )
        
        def add_code_insertion(cur_report, cur_register):
            code = invoke_static_heapsnapshot_function(cur_report,
                                                        cur_register,
                                                        method_instr_registers[0],
                                                        self.static_function_signature)

            # Place code after move_result if there is one, otherwise place code after invoke
            target_line_number = invocation_statement.invoke_line_number + 1 if invocation_statement.move_result_line_number == -1 else invocation_statement.move_result_line_number + 1

            code_insertions.append(CodeInsertionModel(code, method_index,
                                                        target_line_number,
                                                        method_instr_registers))

        # First consider invocation argument registers
        is_arg_register = True
        for register_index, register in enumerate(invocation_statement.arg_registers):

            ### Begin Checks
            # skip_instr_before = False
            skip_instr_after = False

            # Skip Primitive types
            if not invocation_statement.arg_types_pre[register_index].startswith("L"):
                True


            # If it's a constructor, the first register will be unallocated before the invocation
            if invocation_statement.method_name == "<init>" and register_index == 0:
                skip_instr_before = True


            # Sometimes the after type will be different if an arg and return use the same register
            if args_overriden_by_return[register_index]:
                # Only instrument a register before the call if it's overwritten by the move result
                skip_instr_after = True
                # TODO: in the future, we may want to use an extra variable(s) to store the up to two overwritten variables to check them after


                


            # if is_arg_register:
            #     register_type_before = invocation_statement.arg_types_pre(register_index)
            #     if is_return_register:
            #         register_type_after = invocation_statement.return_type
            #     else:
            #         register_type_after = register_type_before
            # else:
            #     # If not an argument, then it's a return register that wasn't used as an argument
            #     skip_instr_before = True
            #     register_type_before = ""
            #     register_type_after = invocation_statement.return_type

            # If the invocation move-result is moving a wide data type, the register after the return register will change type
            # if invocation_statement.move_result_register != "" and SmaliMethodInvocation.is_wide_datatype(invocation_statement.return_type):
            #     if method.get_next_register(invocation_statement.move_result_register) == register:
            #         register_type_after = invocation_statement.return_type

                

            ### End checks
            if not skip_instr_before:
                report.register_index = register_index
                report.is_before_invoke = True
                report.register_name = register
                report.register_type = invocation_statement.arg_types_pre[register_index]
                code = invoke_static_heapsnapshot_function(report,
                                                           register,
                                                           method_instr_registers[0],
                                                           self.static_function_signature)

                code_insertions.append(CodeInsertionModel(code, method_index,
                                                          invocation_statement.invoke_line_number,
                                                          method_instr_registers))

            if not skip_instr_after:
                # if is_return_register:
                #     # report = InstrumentationReport(
                #     #     invoke_signature=invocation_statement.get_signature(),
                #     #     invoke_id=invocation_id,
                #     #     is_arg_register=is_arg_register,
                #     #     is_return_register=is_return_register, # True
                #     #     register_index=-1,
                #     #     is_before_invoke=False,
                #     #     register_name=register,
                #     #     register_type=register_type_after,
                #     #     is_static=invocation_statement.is_static_invoke(),
                #     # )
                #     report.register_index=-1
                #     report.is_before_invoke=False
                # else:
                # report = InstrumentationReport(
                #     invoke_signature=invocation_statement.get_signature(),
                #     invoke_id=invocation_id,
                #     is_arg_register=is_arg_register,
                #     is_return_register=is_return_register, # False
                #     register_index=register_index,
                #     is_before_invoke=False,
                #     register_name=register,
                #     register_type=register_type_after,
                #     is_static=invocation_statement.is_static_invoke(),
                # )

                """
                is_arg_register=True, # Needs tweaked
                is_return_register=False, # Needs tweaked
                register_index=register_index, # Needs tweaked
                is_before_invoke=True, # Needs tweaked
                register_name=register, # Needs tweaked
                register_type=invocation_statement.arg_types_pre[register_index], # Needs tweaked
                """
                report.register_index = register_index
                report.is_before_invoke=False
                report.register_name = register
                report.register_type = invocation_statement.arg_types_pre[register_index]

                add_code_insertion(report, register)
                # code = invoke_static_heapsnapshot_function(report,
                #                                            register,
                #                                            method_instr_registers[0],
                #                                            self.static_function_signature)

                # # Place code after move_result if there is one, otherwise place code after invoke
                # target_line_number = invocation_statement.invoke_line_number + 1 if invocation_statement.move_result_line_number == -1 else invocation_statement.move_result_line_number + 1

                # code_insertions.append(CodeInsertionModel(code, method_index,
                #                                           target_line_number,
                #                                           method_instr_registers))
                
        # Next, consider the return register
        if invocation_statement.invoke_line_number > -1:
            report = InstrumentationReport(
                    invoke_signature=invocation_statement.get_signature(),
                    invoke_id=invocation_id,
                    is_arg_register=False,
                    is_return_register=True,
                    register_index=-1,
                    is_before_invoke=False,
                    register_name=invocation_statement.move_result_register,
                    register_type=invocation_statement.return_type,
                    is_static=invocation_statement.is_static_invoke(),
                )
            
            add_code_insertion(report, invocation_statement.move_result_register)

            # code = invoke_static_heapsnapshot_function(report,
            #                                                ,
            #                                                method_instr_registers[0],
            #                                                self.static_function_signature)

            # # Place code after move_result if there is one, otherwise place code after invoke
            # target_line_number = invocation_statement.invoke_line_number + 1 if invocation_statement.move_result_line_number == -1 else invocation_statement.move_result_line_number + 1

            # code_insertions.append(CodeInsertionModel(code, method_index,
            #                                             target_line_number,
            #                                             method_instr_registers))

        return code_insertions

    def needs_to_insert_directory(self) -> bool:
        return True

    def path_to_directory(self) -> str:
        # target_directory_suffix = "edu/utsa/sefm/heapsnapshot"
        # files = ["Snapshot.smali", "Snapshot$FieldInfo.smali"]
        dest = os.path.join("data/intercept/smali-files/heap-snapshot")
        return dest

def extract_decompiled_smali_code(config: HybridAnalysisConfig):
    config.decoded_apks_path
    target_directory_prefix = "app-debug/smali_classes3"
    target_directory_suffix = "edu/utsa/sefm/heapsnapshot"
    files = ["Snapshot.smali", "Snapshot$FieldInfo.smali"]
    dest = os.path.join("data/intercept/smali-files/heap-snapshot",
                        target_directory_suffix)
    src_files = [os.path.join(config.decoded_apks_path, target_directory_prefix,
                              target_directory_suffix, file_name) for file_name in files]

    if not os.path.isdir(dest):
        run_command(["mkdir", dest])

    run_command(["cp"] + src_files + [dest])


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


def invoke_static_heapsnapshot_function(report: InstrumentationReport,
                                        register_to_analyze, empty_register, static_function_signature: str):
    # static_function_signature = "Ledu/utsa/sefm/heapsnapshot/Snapshot;->checkObjectForPII(Ljava/lang/Object;Ljava/lang/String;)I"
    return f"""
    const-string {empty_register}, "{repr(report)}"
    invoke-static {{{register_to_analyze}, {empty_register}}}, {static_function_signature}
"""


def instr_strategy_from_strategy_name(
        strategy_name: str) -> \
        'InformalInstrumentationStrategyInterface':
    
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
        return StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy()
    else:
        raise ValueError(f"Invalid instrumentation strategy:"
                         f" {strategy_name}")

if __name__ == '__main__':
    pass
