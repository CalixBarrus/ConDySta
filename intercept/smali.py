from dataclasses import dataclass, field
import re
from intercept.InstrumentationReport import InstrumentationReport
from intercept.code_insertion_model import CodeInsertionModel


from typing import List, Tuple

# TODO: refactor - put these back in order

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

    # TODO: this needs to be moved outside of this class
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

    def args_overriden_by_return(self, parent_method: 'SmaliMethod') -> List[bool]:
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
    
    def validate_observation_report(self, report: InstrumentationReport):
        # Check for issue where register name in report doesn't correspond to copy of current smali code
        if report.is_return_register:
            if self.move_result_register != report.invocation_argument_register_name:
                raise ReportMismatchException(f"Smali return register {self.move_result_register} doesn't match report return register {report.invocation_argument_register_name}. ")
            
            # Check to make sure the invoke still has a 'move_result'
        else:
            if report.invocation_argument_register_index > len(self.argument_registers):
                raise ReportMismatchException(f"Report references index {report.invocation_argument_register_index} but there are only {len(self.argument_registers)} registers")            

            if self.argument_registers[report.invocation_argument_register_index] != report.invocation_argument_register_name:
                raise ReportMismatchException(f"Report references index {report.invocation_argument_register_index} but there are only {len(self.argument_registers)} registers")
            

            


class ReportMismatchException(Exception):
    # Mismatch between instrumentation report and live smali code
    pass


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


### Smali/Java Type Conversion
    
def java_type_to_smali_type(java_type: str) -> str:
    # TODO: test this for edge cases
    
    if java_type == "void":
        return "V"
    elif java_type == "boolean":
        return "Z"
    elif java_type == "byte":
        return "B"
    elif java_type == "short":
        return "S"
    elif java_type == "char":
        return "C"
    elif java_type == "int":
        return "I"
    elif java_type == "long":
        return "J"
    elif java_type == "float":
        return "F"
    elif java_type == "double":
        return "D"
    else:
        return "L" + java_type.replace(".", "/") + ";"
    
def smali_type_to_java_type(smali_type: str) -> str:
    
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
    elif smali_type == "J":
        return "long"
    elif smali_type == "F":
        return "float"
    elif smali_type == "D":
        return "double"
    else:
        assert smali_type[0] == "L"
        assert smali_type[-1] == ";"
        return smali_type.replace("/", ".")[1:-1]
    

### End Smali/Java Type Conversion

# class JavaSignature:
#     is_static: bool

#     def __init__(self, signature: str, is_static: bool):
#         # Return Method Invocation in the style found in Flowdroid source/sink lists and Flowdroid log output
#         # Example
#         # <[full package name]: [return type] [method name]([arg types,])>

#         # expects output from SmaliMethodInvocation.get_java_style_signature()

        

#         match = re.search(r"<(.+): (.+) (.+)(((.+)))>", signature)
#         if match is None:
#             pass

#         base_class = match.group(1)
#         return_type = match.group(2)
#         method_name = match.group(3)
#         args = list(map(lambda s: s.strip(), match.group(4).split(",")))





