import os
import re
import shutil
from typing import List, Tuple

from intercept import intercept_config

from util import logger

logger = logger.get_logger('intercept', 'instrument')


def instrument_main(config: intercept_config.InterceptConfig):
    logger.info("Instrumenting smali code...")

    instrumentation_strategy: InformalInstrumentationStrategyInterface = \
        instrStrategyFromInterceptConfig(config)

    apk_models: List[DecodedApkModel] = []
    for item in os.listdir(config.decoded_apks_path):
        apk_path = os.path.join(config.decoded_apks_path, item)
        if os.path.isdir(apk_path):
            # Parse each apk into a model class
            apk_models.append(DecodedApkModel(apk_path))

    for apk_model in apk_models:
        # Pass the instrumentation_strategy to each apk
        apk_model.instrument(instrumentation_strategy)


class InformalInstrumentationStrategyInterface:
    # def instrument(self, contents: List[str]) -> List[str]:
    #     """Scan through contents of smali file and return the instrumented
    #     smali code"""
    #     raise NotImplementedError("Interface not implemented")

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


### Begin Model Classes ###
# Model classes store lexing and parsing logic. The constructors should leave the model
# ready for instrumentation by any of the instrumentation strategies.

class DecodedApkModel:
    """
    Representation of a decoded apk's files for the purposes of instrumentation
    """
    apk_root_path: str
    project_smali_directory_names: List[str]
    smali_directories: List[List['SmaliFile']]

    def __init__(self, decoded_apk_root_path: str):
        """
        Parse all the smali directories and files for later instrumentation.
        :param decoded_apk_root_path: Path to the root directory of a single apk
        decoded by apktool.
        """
        self.apk_root_path = decoded_apk_root_path

        self.project_smali_directory_names = []
        for item in os.listdir(self.apk_root_path):
            if (os.path.isdir(os.path.join(self.apk_root_path, item)) and
                    item.startswith("smali")):
                assert (item == "smali"
                        or item.startswith("smali_classes")
                        or item.startswith("smali_assets"))
                self.project_smali_directory_names.append(item)

        # Sort the folder names so indexing into the list is consistent with
        # the file names.
        self.project_smali_directory_names.sort()
        assert self.project_smali_directory_names[0] == "smali"

        # Go through each folder smali_classes folder and parse all the smali
        # files.
        project_smali_directory_paths = map(os.path.join,
                                            [decoded_apk_root_path] * len(
                                                self.project_smali_directory_names),
                                            self.project_smali_directory_names)
        self.smali_directories: List[List[SmaliFile]] = []
        for path in project_smali_directory_paths:
            self.smali_directories.append(
                self.scan_for_smali_files(path, ""))

    def scan_for_smali_files(self, project_smali_folder_path: str,
                             class_path: str):
        """
        Recursively traverse the subdirectories of
        project_smali_folder_path, getting the methods in each smali file.
        :param project_smali_folder_path: path to the "smali" or
        "smali_classes[n]" directory.
        :param class_path: relative path referring to the subdirectories
        traversed so far.
        :return: List of SmaliFile objects containing data about each file in the apk
        """
        result_smali_files: List[SmaliFile] = []
        for item in os.listdir(os.path.join(project_smali_folder_path,
                                            class_path)):
            item_path = os.path.join(project_smali_folder_path, class_path,
                                     item)
            if os.path.isdir(item_path):
                result_smali_files += self.scan_for_smali_files(
                    project_smali_folder_path,
                    os.path.join(class_path, item))

            elif item.endswith(".smali"):
                result_smali_files.append(SmaliFile(
                    project_smali_folder_path, class_path, item))

        return result_smali_files

    def instrument(self, instrumenter: InformalInstrumentationStrategyInterface):
        if instrumenter.needs_to_insert_directory():
            self.insert_smali_directory(instrumenter.path_to_directory())

        for smali_directory in self.smali_directories:
            for smali_file in smali_directory:
                instrumenter.instrument_file(smali_file)

    def insert_smali_directory(self, smali_source_directory_path):
        """
        :param smali_source_directory_path: path to smali code that will be inserted
        (copied) into the apk
        """
        if os.path.isdir(smali_source_directory_path):
            raise ValueError(
                "Directory " + smali_source_directory_path + " does not exist.")

        destination_directory_path = os.path.join(self.apk_root_path,
                                                  self.project_smali_directory_names[
                                                      -1])
        if os.path.isdir(destination_directory_path):
            raise ValueError(
                "Directory " + destination_directory_path + " does not exist.")

        shutil.copytree(smali_source_directory_path, destination_directory_path)


class SmaliFile:
    """
    Class representing a single smali text file.

    Most parsing and modification logic for smali files should be contained in this
    class. Contained classes should focus on being model classes, and should have
    limited parsing/update logic.
    """
    file_path: str
    methods: List['SmaliMethod']

    def __init__(self, project_smali_folder_path, class_path,
                 file_name):
        self.file_path = os.path.join(project_smali_folder_path, class_path,
                                      file_name)
        self.methods = []

        with open(self.file_path, 'r') as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            if line.startswith(".method"):
                self.methods.append(self.parse_smali_method(lines, i))

    def parse_smali_method(self, lines, function_start_index) -> 'SmaliMethod':
        result_method = SmaliMethod()
        result_method.start_line_number = function_start_index

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
                self.parse_move_result(
                    result_method.invocation_statements[-1], i, line)

        # debug
        assert result_method.start_line_number < result_method.end_line_number
        # end debug

        return result_method

    def parse_method_signature(self, method, signature):
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
        result_invocation = SmaliMethodInvocation()

        result_invocation.invoke_line_number = line_number

        # First word is invoke-[kind]
        result_invocation.invoke_kind = line.split()[0]

        # find and capture the contents of matched curly braces
        arg_registers_string = re.search(r"\{(.*)\}", line).group(1)
        result_invocation.arg_registers = arg_registers_string.split(", ")

        # find and capture the class name and method name which are between "},
        # " and "->"; and "->" and "(", respectively
        match = re.search(r"\}, (.*)->(.*)\(", line)
        result_invocation.class_name = match.group(1)
        result_invocation.method_name = match.group(2)

        # find and capture the arg types, which consist of a comma separated list
        # between a left and right paren
        arg_types_str = re.search(r"\((.*)\)", line).group(1)
        result_invocation.arg_types = arg_types_str.strip().split(", ")
        # empty out arg_types list if it only contains an empty string
        if len(result_invocation.arg_types) == 1 and result_invocation.arg_types[
            0] == '':
            result_invocation.arg_types = []

        # find and capture the return type, between a right paren and the end of the
        # string.
        result_invocation.return_type = re.search("\)(.*)$", line).group(1).strip()

        return result_invocation

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
        method = self.methods[method_number]
        if method.register_count() + requested_register_count > 16:
            raise ValueError("Requesting too many registers")

        if requested_register_count == 1:
            return ["v" + str(method.number_of_locals)]
        elif requested_register_count == 2:
            return ["v" + str(method.number_of_locals), "v" + str(method.number_of_locals+1)]
        else:
            raise NotImplementedError()

    def insert_code_into_method(self, code,
                                method_number, destination_line_number,
                                used_registers):
        with open(self.file_path, 'r') as file:
            contents = file.readlines()

        # Debugging
        for method in self.methods:
            assert contents[method.start_line_number].strip().startswith(".method")
        temp = len(contents)
        # end debugging

        # # adjust # of locals
        # if not self.methods[method_number].num_locals_updated:
        #     if len(used_registers) > 0:
        #         contents[self.methods[
        #             method_number].locals_line_number] = f".locals {self.methods[method_number].number_of_locals + len(used_registers)}\n"
        #         self.methods[method_number].num_locals_updated = True

        # insert code
        code_lines = code.splitlines(keepends=True)
        contents[destination_line_number:destination_line_number] = code_lines

        # Debugging
        temp = len(contents)
        # end debugging

        # Write changes
        with open(self.file_path, 'w') as file:
            file.writelines(contents)

        # Debugging
        with open(self.file_path, 'r') as file:
            temp2 = file.readlines()
            for i in range(len(contents)):
                assert contents[i] == temp2[i]
            assert len(temp2) == temp
        # end debugging

        # update model of code
        # Parse the modified method again
        self.methods[method_number] = self.parse_smali_method(contents,
                                                              self.methods[
                                                                  method_number].start_line_number)
        # increment line numbers in all the methods after the modified method
        for method in self.methods[method_number + 1:]:
            method.increment_line_numbers(len(code_lines))

        # Debugging
        for method in self.methods:
            assert contents[method.start_line_number].strip().startswith(".method")
        # end debugging

    def update_method_preamble(self, method_number, used_registers):
        if len(used_registers) > 0:
            with open(self.file_path, 'r') as file:
                contents = file.readlines()

            # adjust # of locals
            contents[self.methods[
                method_number].locals_line_number] = f"    .locals {self.methods[method_number].number_of_locals + len(used_registers)}\n"

            # Write changes
            with open(self.file_path, 'w') as file:
                file.writelines(contents)


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
        if self.is_static:
            return self.number_of_locals + len(self.args)
        else:
            # There is an extra parameter, p0, which is "this"
            return self.number_of_locals + len(self.args) + 1

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
    arg_types: List[str]
    return_type: str

    move_result_line_number: int
    move_result_kind: str
    move_result_register: str

    def __init__(self):
        self.move_result_line_number = -1

    @staticmethod
    def is_invocation(line: str) -> bool:
        return line.strip().startswith("invoke")

    @staticmethod
    def is_move_result(line):
        return line.strip().startswith("move-result")

    def increment_line_number(self, increment: int):
        self.invoke_line_number += increment

        if self.move_result_line_number != -1:
            self.move_result_line_number += increment

    def __str__(self):
        return f"<{self.class_name}: {self.return_type} {self.method_name}({','.join(self.arg_types)})>"



def instrument_decoded_apks(decoded_apks_path):
    decoded_apks_list = []
    for item in os.listdir(decoded_apks_path):
        if os.path.isdir(item):
            decoded_apks_list.append(DecodedApkModel(os.path.join(decoded_apks_path,
                                                                  item)))


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

                    # Debugging
                    with open(smali_file.file_path, 'r') as file:
                        contents = file.readlines()
                    for count, method in enumerate(smali_file.methods):
                        assert contents[method.start_line_number].strip().startswith(
                            ".method")
                    # end debugging
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

        # Scan through the file and note all of the code that must be inserted. Then,
        # back to front (so the line numbers stay valid), insert each code snippet.
        # Finally, re-parse the file so the
        # model object matches up. Note that this only works because each bit of
        # inserted code is independent of other bits of inserted code.
        # TODO: re-parse logic is in insert_code_into_method, yet this method depends
        #  on that internal logic. Need to change approach.

        # Make a list of [code to insert, method index, line number, registers] tuples
        # TODO: This is not a good way to do this. Need to change how code insertion
        #  works with the insert_code_into_method function
        code_insertions: List[Tuple[str, int, int, List[str]]] = []

        instrumentation_id = 0
        for method_index, method in enumerate(smali_file.methods):

            # Debug
            # if method.method_name == "dump" and smali_file.file_path.endswith(
            #         "FragmentManagerImpl.smali"):
            #     print(1)
            # End Debug

            method_instr_registers = []

            for invocation_statement in method.invocation_statements:

                # if a method is invoked that returns a string and the result is saved
                # to a register
                if invocation_statement.return_type == SMALI_STRING_CLASS_NAME and \
                        invocation_statement.move_result_line_number != -1:
                    # Insert code just after move-result statement
                    target_line_number = invocation_statement.move_result_line_number + 1

                    if method_instr_registers == []:
                        try:
                            method_instr_registers = smali_file.get_registers(
                                method_index, 2)
                        except ValueError:
                            # If the method has too many registers used,
                            # don't instrument it
                            continue

                    target_code = log_invocation_string_return_with_stacktrace(
                        invocation_statement.move_result_register,
                        method_instr_registers[0],
                        method_instr_registers[1],
                        method_index,
                        invocation_statement,
                        instrumentation_id)
                    instrumentation_id += 1

                    code_insertions.append((target_code, method_index,
                                            target_line_number,
                                            [method_instr_registers[0]]))

            smali_file.update_method_preamble(method_index, method_instr_registers)

        for code, method_index, line_number, registers in code_insertions.__reversed__():
            smali_file.insert_code_into_method(code, method_index,
                                               line_number,
                                               registers)

    def needs_to_insert_directory(self) -> bool:
        return False

    def path_to_directory(self) -> str:
        raise AssertionError("Instrumenter does not need to insert any "
                             "directories.")


# class StaticFunctionInserter():
#     def instrument(self, contents: List[str]) -> List[str]:
#         """
#         :param contents: Contents of single smali file
#         :return:
#         """
#         is_reading_method = False
#         method_start_index = 0
#         new_contents = None
#         method_number = 1
#         i = 0
#         while i < len(contents):
#             line = contents[i].rstrip()
#
#             # Start method collection for any string return functions that are
#             # not abstract, contructors, or native.
#             if ".method" in line and "abstract" in line:
#                 i += 1
#                 continue
#
#             elif ".method" in line and "constructor" in line:
#                 i += 1
#                 continue
#
#             elif ".method" in line and "native" in line:
#                 i += 1
#                 continue
#
#             elif ".method" in line and ")Ljava/lang/String;" in line:  # method return string
#                 method = []
#                 is_reading_method = True
#                 method_start_index = i
#                 method.append(line)
#                 i += 1
#                 continue
#
#             # When an appropriate string return method is detected, collect all
#             # the code until ".end method" into the "method" variable. When
#             # ".end method" gets hit, pass it to "instrument" and begin scanning
#             # for more methods.
#             if is_reading_method == True:
#                 if ".end method" in line:
#                     is_reading_method = False
#                     new_contents = self._instrument_method(contents,
#                                                            method_start_index,
#                                                            i,
#                                                            method_number)
#                     method_number += 1
#
#             i += 1
#
#         if new_contents is None:
#             return contents
#         else:
#             return new_contents
#
#     def _instrument_method(self, contents, method_start_index,
#                            method_end_index, method_number):
#         localsNumber = 0
#         locals_index = 0
#         parameterCount = 0
#         paraNumberList = []
#         paraRegList = []
#
#         for i in range(method_start_index, method_end_index + 1):
#             # get number of locals
#             line = contents[i]
#             if ".locals" in line:
#                 locals_index = i
#                 localsNumber = int(line.split()[1])
#
#             paraRegList = paraRegList + re.findall(r'p\d+', line)
#
#         for item in paraRegList:
#             number = re.findall(r'\d+', item)
#             paraNumberList.append(int(number[0]))
#
#         if len(paraNumberList) > 0:
#             parameterCount = max(paraNumberList) + 1
#
#         # Most dalvik opcodes can only use first 16 registers
#         # Distinction between local registers and parameter registers (vX and
#         # pX) is virtual. In reality there is only one set of registers and
#         # locals are first, then parameters
#         if (16 - localsNumber - parameterCount) >= 1:
#             # Overwrite locals declaration to reflect the additional local
#             # used by the inserted code
#             contents[locals_index] = "    .locals " + str(localsNumber + 1)
#             v1 = "v" + str(localsNumber)
#         else:
#             # Don't instrument method if not enough locals for us to use
#             # TODO: modify function to stick required local into a local
#             #  register
#             return contents
#
#         instrumentation_id = 1
#
#         i = method_start_index
#         while i < method_end_index:
#             # for i in range(method_start_index, method_end_index + 1):
#             line = contents[i]
#
#             if "return-object" in line:
#                 # line will be "return-object v[#]"
#                 returnVar = line.split()[1]
#                 text_to_insert = [log_stacktrace(returnVar, v1,
#                                                  method_number,
#                                                  instrumentation_id)]
#
#                 # insert text_to_insert before the "return-object" line
#                 instrumentation_id += 1
#
#                 contents[i:i] = text_to_insert
#
#                 # increment relevant loop indices
#                 i += 1
#                 method_end_index += 1
#
#             i += 1
#
#         return contents
#
#     def insert_smali_files(self, new_smali_files_path, apk_smali_files_path):
#         apk_smali_root_items = os.listdir(apk_smali_files_path)
#         """
#         There will be many files in the root of a decompiled apk. These
#         include build, kotlin, META-INF, original, res, smali,
#         smali_classes[n], unknown, AndroidManifest.xml, apktool.yml,
#         resources.arsc.
#         We are interested in the smali and smali_classes[n] folders.
#
#         From my understanding, each smali/smali_classes[n] folder represents
#         a different DEX file, with each having at most 64K methods, and each DEX
#         having more methods than the next.
#         """
#
#         smali_classes_directories = [directory for directory in
#                                      apk_smali_root_items if
#                                      directory.startswith("smali")]
#
#         if len(smali_classes_directories) < 2:
#             raise RuntimeError("Expected at least 2 smali and smali_classes["
#                                "n] folders. Check the decompiled apk.")
#
#         # We should be able to insert our new smali files into the
#         # highest-numbered smali classes folder
#
#         cmd = f"mv {new_smali_files_path} " \
#               f"{os.path.join(apk_smali_files_path, smali_classes_directories[-1])}"
#         print(cmd)
#         os.system(cmd)


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


def instrStrategyFromInterceptConfig(
        intercept_config: intercept_config.InterceptConfig) -> \
        'InformalInstrumentationStrategyInterface':
    if intercept_config.instrumentation_strategy == \
            "LogStringReturnInstrumentationStrategy":
        return LogStringReturnInstrumentationStrategy()
    elif intercept_config.instrumentation_strategy == \
            "StringReturnInstrumentationStrategy":
        return StringReturnInstrumentationStrategy()
    elif intercept_config.instrumentation_strategy == \
            "StringReturnValuesInstrumentationStrategy":
        return StringReturnValuesInstrumentationStrategy()
    else:
        raise ValueError(f"Invalid instrumentation strategy:"
                         f" {intercept_config.instrumentation_strategy}")


if __name__ == '__main__':
    config = intercept_config.get_default_intercept_config()

    instrument_main(config)
