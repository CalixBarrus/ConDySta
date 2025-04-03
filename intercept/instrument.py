from abc import ABC, abstractmethod
import os
import re
from typing import Callable, List, Set, Tuple, Union

import pandas as pd


from hybrid.invocation_register_context import InvocationRegisterContext, filter_access_paths_with_length_1, reduce_for_field_insensitivity
from hybrid.access_path import AccessPath
from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path
from hybrid.source_sink import MethodSignature
from intercept.code_insertion_model import CodeInsertionModel
from intercept.InstrumentationReport import InstrumentationReport
from intercept.smali import ReportMismatchException, SmaliFile, SmaliMethod, SmaliMethodInvocation
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
def instrument_by_invocation(smali_file: SmaliFile, instrument_invocation: Callable[[int, SmaliMethod, List[str], SmaliMethodInvocation], List[CodeInsertionModel]], registers_count=1) -> List[CodeInsertionModel]:
    code_insertions: List[CodeInsertionModel] = []

    for method_index, method in enumerate(smali_file.methods):

        # Skip abstract methods
        if method.is_abstract:
            continue

        try:
            method_instrumentation_registers = smali_file.get_registers(
                method_index, registers_count)
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

    def __init__(self, sources: List[MethodSignature], overwrite_return: bool=True):
        self.sources_to_instrument = sources
        self.invocation_id = -1

        # TODO Existing experiments weren't controlling this value
        self.overwrite_return = overwrite_return



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
            logger.debug(f"Code insertions on file {smali_file.file_path} on lines {','.join([str(insertion.line_number) for insertion in code_insertions])}")
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
            report = f"Source Method {invocation_statement.class_name + ' ' + invocation_statement.method_name} called in class and method <{method.enclosing_class_name + ' ' + method.method_name}>. Return is being replaced with {harness_value}. Previous value was:"
        else:
            report = f"Source Method {invocation_statement.class_name + ' ' + invocation_statement.method_name} called in class and method <{method.enclosing_class_name + ' ' + method.method_name}>. Return value was:"
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
    
    @staticmethod
    def parse_harness_output(message: str):
        # Example of retrieved output
        # 10-21 11:40:27.756  8455  8455 D HarnessedSource: Source Method Landroid/widget/EditText; getText called in class and method <Lalc; onClick>. Return value was:;
        # 
        if "Return is being replaced with" in message:
            pattern = r"Source Method (.+) called in class and method <(.+) (.+)>\. Return is being replaced with (.+). Previous value was:(.+)"

            match = re.findall(pattern, message)

            assert match is not None
            assert len(match) == 1

            smali_source_method = match[0][0] #smali_class method_name
            enclosing_smali_class = match[0][1]
            enclosing_method_name = match[0][2]
            observed_value = ""
            substituting_value = match[0][3]
            original_value = match[0][4]

        else:
            pattern = r"Source Method (.+) called in class and method <(.+) (.+)>\. Return value was:(.+)"

            match = re.findall(pattern, message)

            assert match is not None
            assert len(match) == 1

            smali_source_method = match[0][0] #smali_class method_name
            enclosing_smali_class = match[0][1]
            enclosing_method_name = match[0][2]
            observed_value = match[0][3]
            substituting_value = ""
            original_value = ""


        return smali_source_method, enclosing_smali_class, enclosing_method_name, observed_value, substituting_value, original_value
    
class HarnessObservations(SmaliInstrumentationStrategy):
    
    unprocessed_observations: List[InvocationRegisterContext]
    disable_field_sensitivity: bool # base object should be tainted; don't taint specific access path
    
    report_mismatch_exceptions: int
    report_mismatch_repair_attempted: int 

    record_taint_function_mapping: bool
    filter_to_length1_access_paths: bool
    df_instrumentation_reporting: pd.DataFrame
    mapping_key_cols: Tuple[str, str, str] # Expected cols from FD output
    mapping_observation_lookup_cols: Tuple[str, str, str] # Which should correspond to an observation(s) from DA output
    mapping_str_observation_lookup_cols: Tuple[str]
    result_cols: List[str]

    unprocessed_observed_strings: List[Set[str]]
    processed_observed_strings: List[Set[str]]

    HIGHEST_TAINT_ID = 10  # suffixes are from 0-10 inclusive

    def __init__(self, observations: List[InvocationRegisterContext]=[], 
                 disable_field_sensitivity: bool=False, 
                 record_taint_function_mapping: bool=False, 
                 filter_to_length1_access_paths: bool=False):

        self.disable_field_sensitivity = disable_field_sensitivity
        self.record_taint_function_mapping = record_taint_function_mapping
        self.filter_to_length1_access_paths = filter_to_length1_access_paths
        self.report_mismatch_exceptions = 0
        self.report_mismatch_repair_attempted = 0

        self.set_observations(observations)

        if self.record_taint_function_mapping:
            self.mapping_key_cols = ["Taint Function Name", "Enclosing Class", "Enclosing Method"]
            self.mapping_observation_lookup_cols = ["Invocation Java Signature", "Argument Register Index", "Access Path"]
            self.mapping_str_observation_lookup_cols = ["Observed Strings"]
            # TODO: df_cols won't get updated correctly if someone changes any col names
            self.cols_of_df_instrumentation_reporting = self.mapping_key_cols + self.mapping_observation_lookup_cols + self.mapping_str_observation_lookup_cols
            # self.result_cols = ["Enclosing Class", "Enclosing Method", "Invocation ID", "Argument Register Index", "Access Path"]

            self.df_instrumentation_reporting = self._initialize_df()

        self.unprocessed_observed_strings = []


    def set_observations(self, observations: List[InvocationRegisterContext]):
        self.unprocessed_observations = observations

        if self.filter_to_length1_access_paths:
            # if there is ever a non-string level 0 access path, this logic needs to be rethought out
            self.processed_observations, _ = filter_access_paths_with_length_1(observations)
        elif self.disable_field_sensitivity:
            self.processed_observations, _ = reduce_for_field_insensitivity(observations)
        else: 
            self.processed_observations = observations

        # TODO: need to reset counters? 
    
    def set_observed_strings(self, observed_strings: List[Set[str]]):
        self.unprocessed_observed_strings = observed_strings

        if self.filter_to_length1_access_paths:
            # if there is ever a non-string level 0 access path, this logic needs to be rethought out
            _, self.processed_observed_strings = filter_access_paths_with_length_1(self.unprocessed_observations, observed_strings)

        elif self.disable_field_sensitivity:
            # assume set_observations is always called first
            _, self.processed_observed_strings = reduce_for_field_insensitivity(self.unprocessed_observations, observed_strings)

        else: 
            self.processed_observed_strings = observed_strings


    def instrument_file(self, smali_file: 'SmaliFile')-> List[CodeInsertionModel]:      
        if not self.disable_field_sensitivity and not self.filter_to_length1_access_paths:
            observations = self.unprocessed_observations        
            if self.unprocessed_observed_strings != []:
                observed_strings = self.unprocessed_observed_strings
        else:
            observations = self.processed_observations  
            if self.unprocessed_observed_strings != []:
                observed_strings = self.processed_observed_strings

        file_observations = [observation for observation in observations if observation[0].enclosing_class_name == smali_file.class_name]

        if self.unprocessed_observed_strings != []:
            file_observed_strings = [observed_set for observed_set, observation in zip(observed_strings, observations) if observation[0].enclosing_class_name == smali_file.class_name]

        def _instrument_invocation_statement(method_index: int, method: SmaliMethod, method_instrumentation_registers: List[str], invocation_statement: SmaliMethodInvocation) -> List[CodeInsertionModel]:
            # Requires two method_instrumentation_registers. 
            method_observations = [observation for observation in file_observations if observation[0].enclosing_method_name == method.method_name]
            if self.unprocessed_observed_strings != []:
                method_observed_strings = [observed_set for observed_set, observation in zip(file_observed_strings, file_observations) if observation[0].enclosing_method_name == method.method_name]

            # Enclosing class/method is the granularity level that'll be returned by fd
            method_taint_function_ids = range(len(method_observations))
            method_taint_function_ids = [id % (self.HIGHEST_TAINT_ID+1) for id in method_taint_function_ids]

            # match observation if java method signature matches invocation signature
            # TODO: add option to match against actual call granularity (line number, etc.)
            invocation_observations = [observation for observation in method_observations if observation[0].invocation_java_signature == invocation_statement.get_java_style_signature()]
            invocation_taint_function_ids = [i for i, observation in zip(method_taint_function_ids, method_observations) if observation[0].invocation_java_signature == invocation_statement.get_java_style_signature()]
            if self.unprocessed_observed_strings != []:
                invocation_observed_strings = [observed_set for observed_set, observation in zip(method_observed_strings, method_observations) if observation[0].invocation_java_signature == invocation_statement.get_java_style_signature()]

            code_insertions = []

            for invocation_observation, invocation_taint_function_id, i in zip(invocation_observations, invocation_taint_function_ids, range(len(invocation_observations))):
                report, access_path = invocation_observation

                try:
                    invocation_statement.validate_observation_report(report)
                except ReportMismatchException as e:
                    self.report_mismatch_exceptions += 1
                    msg = f"Report mismatch in {smali_file.file_path} invocation line {invocation_statement.invoke_line_number}" + str(e)
                    logger.error(msg)
                    logger.debug(f"Report mismatch in {invocation_statement} from report {report}")
                    # don't Instrument based on this report, because the mismatch may not baksmali

                    # I'm not sure if these errors occur because of APK Tool behaving differently on different environments, or if the field in the reports is just wrong (maybe it's filled out for an arbitrary argument instead of the name of the return register?)
                    # If the report is for a return, attempt to repair by using the correct return register

                    if report.is_return_register:
                        # Check if the invoke still has a move_result
                        if invocation_statement.move_result_line_number == -1:
                            logger.debug(f"No move result when one was expected")
                            continue

                        report.invocation_argument_register_name = invocation_statement.move_result_register
                        self.report_mismatch_repair_attempted += 1
                    else:
                        continue

                destination_register = report.invocation_argument_register_name
                
                # TODO: Check that dest register is still valid after the call; i.e., isn't next to a wide return register, isn't an arg register getting returned over, etc.
                code = self._taint_access_path_code(destination_register, method_instrumentation_registers, access_path, invocation_taint_function_id)

                # place code after move result if there is one, otherwise place code after invoke
                target_line_number = invocation_statement.invoke_line_number + 1 if invocation_statement.move_result_line_number == -1 else invocation_statement.move_result_line_number + 1

                code_insertions.append(CodeInsertionModel(code, method_index, target_line_number, method_instrumentation_registers))

                if self.record_taint_function_mapping:
                    taint_method = self._lookup_static_taint_method(invocation_taint_function_id, access_path)

                    if self.unprocessed_observed_strings != []:
                        observed_string_set = invocation_observed_strings[i]
                    else:
                        observed_string_set = set()
                    
                    self._record_observation_harness(taint_method, method.enclosing_class_name, method.method_name, invocation_statement.get_java_style_signature(), report.invocation_argument_register_index, access_path, observed_string_set)



            return code_insertions

        code_insertions = []
        if len(file_observations) > 0:
            required_registers = 2
            code_insertions = instrument_by_invocation(smali_file, _instrument_invocation_statement, required_registers)

        # start debug
        if len(code_insertions) > 0:
            logger.debug(f"Code insertions on file {smali_file.file_path} on lines {','.join([str(insertion.line_number) for insertion in code_insertions])}")
        # end debug

        return code_insertions
    

    def needs_to_insert_directory(self):
        return True

    def path_to_directory(self):
        dest = os.path.join("data/intercept/smali-files/taint-insertion")
        return dest
    
    @staticmethod
    def _lookup_static_taint_method(invocation_taint_function_id: int, access_path: AccessPath) -> str:
        # Behavior of _taint_access_path_code is very closely tied to which of these objects gets returned

        if access_path.fields[-1].fieldClassName != "java.lang.String":
            # static_taint_method = f"Lcom/example/taintinsertion/TaintInsertion;->taintObject{invocation_taint_function_id}(Ljava/lang/Object;)Ljava/lang/Object;"
            static_taint_method = HarnessObservations.get_static_taint_method(invocation_taint_function_id, "object")
        else: 
            # static_taint_method = f"Lcom/example/taintinsertion/TaintInsertion;->taintStr{invocation_taint_function_id}()Ljava/lang/String;"
            static_taint_method = HarnessObservations.get_static_taint_method(invocation_taint_function_id, "str")

        return static_taint_method

    @staticmethod
    def get_static_taint_method(id: int, type: str) -> str:
        match type:
            case "str":
                return f"Lcom/example/taintinsertion/TaintInsertion;->taintStr{id}()Ljava/lang/String;"
            case "object":
                return f"Lcom/example/taintinsertion/TaintInsertion;->taintObject{id}(Ljava/lang/Object;)Ljava/lang/Object;"
        raise ValueError("Expects 'str' or 'object'")
    
    def get_all_static_taint_methods(self) -> List[str]:
        methods = []
        for i in range(self.HIGHEST_TAINT_ID):
            methods.append(HarnessObservations.get_static_taint_method(i, "str"))
            methods.append(HarnessObservations.get_static_taint_method(i, "object"))

        return methods
    
    @staticmethod
    def _taint_access_path_code(base_object_register: str, instrumentation_registers: List[str], access_path: AccessPath, invocation_taint_function_id: int) -> str:

        static_taint_method = HarnessObservations._lookup_static_taint_method(invocation_taint_function_id, access_path)

        # check if end of access_path is an object; should only occur when access path has been truncated
        if access_path.fields[-1].fieldClassName != "java.lang.String":
            assert len(access_path.fields) == 1
            # taint_object_method_id = "1"
            # static_taint_method = f"Lcom/example/taintinsertion/TaintInsertion;->taintObject{taint_object_method_id}(Ljava/lang/Object;)Ljava/lang/Object;"
            code = f"""
    invoke-static {{{base_object_register}}}, {static_taint_method}
    move-result-object {base_object_register}
"""
            return code


        # static_taint_method = "Lcom/example/instrumentableexample/MainActivity;->taint()Ljava/lang/String;"
        # static_taint_method = "Lcom/example/taintinsertion/TaintInsertion;->taint()Ljava/lang/String;"

        # assert len(instrumentation_registers) == 2
        tainted_str_register, access_path_register = instrumentation_registers[0], instrumentation_registers[1]
        # call taint() to get the tainted string
        # TODO: change HarnessObservations so this taint function gets added from assets.


        code = f"""
    invoke-static {{}}, {static_taint_method}
    move-result-object {tainted_str_register}
"""
        # get the target access path into a register
        if len(access_path.fields) == 1:
            # move contents of taint register into base_object_register (whose type must be compatible)
            # TODO: this branch doesn't use access_path_register; only 1 register is needed.
            source_register = tainted_str_register
            dest_register = base_object_register
            assert access_path.fields[0].get_smali_type() == "Ljava/lang/String;"
            code += f"""    move-object {dest_register}, {source_register}"""
        elif len(access_path.fields) == 2:
            # Field can be accessed directly
            base_object_smali_type = access_path.fields[0].get_smali_type()

            string_field_name = access_path.fields[1].fieldName        
            string_type = "Ljava/lang/String;"
            assert access_path.fields[1].get_smali_type() == string_type

            code += f"""    iput-object {base_object_register}, {tainted_str_register}, {base_object_smali_type}->{string_field_name}:{string_type}
"""
            pass
        elif len(access_path.fields) > 2:
            # Only this case requires the access path register
            code += instance_child_access_code(base_object_register, access_path_register, access_path)
            second_to_last_field_type = access_path.fields[-2].get_smali_type()
            string_field_name = access_path.fields[-2].fieldName
            string_type = access_path.fields[-1].get_smali_type()
            code += f"""    iput-object {access_path_register}, {tainted_str_register}, {second_to_last_field_type}->{string_field_name}:{string_type}
"""
        # Example of field access in smali
        # iput-object v2, v1, Lcom/example/instrumentableexample/Child$SubSubChild;->str:Ljava/lang/String;

        return code

    def _initialize_df(self) -> pd.DataFrame:
        # Index doesn't really matter
        # There'll effectively be a non-unique multi index accross the first three cols
        # key_cols = ["Taint Function Name", "Enclosing Class", "Enclosing Method"]
        # to_lookup_cols = ["Invocation ID", "Argument Register Index", "Access Path"]
        # result_cols = ["Enclosing Class", "Enclosing Method", "Invocation ID", "Argument Register Index", "Access Path"]

        df = pd.DataFrame(columns=self.cols_of_df_instrumentation_reporting)

        return df
    
    def _record_observation_harness(self, taint_function: str, enclosing_class: str, enclosing_method: str, invoke_id: int, argument_register_index: int, access_path: AccessPath, observed_string_set: Set[str]):
        # key_cols = ["Taint Function Name", "Enclosing Class", "Enclosing Method"]
        # to_lookup_cols = ["Invocation ID", "Argument Register Index", "Access Path"]
        # result_cols = ["Enclosing Class", "Enclosing Method", "Invocation ID", "Argument Register Index", "Access Path"]
        # df_cols = self.mapping_key_cols + self.mapping_observation_lookup_cols
        df_cols = self.cols_of_df_instrumentation_reporting

        new_row = pd.DataFrame({col:[item] for col, item in zip(df_cols, [taint_function, enclosing_class, enclosing_method, invoke_id, argument_register_index, access_path, observed_string_set])})
        self.df_instrumentation_reporting = pd.concat((self.df_instrumentation_reporting, new_row), ignore_index=True)
        # self.df_instrumentation_reporting = self.df_instrumentation_reporting.reindex(index=range(len(self.df_instrumentation_reporting)))



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



def instance_child_access_code(base_object_register: str, access_path_register: str, access_path: AccessPath) -> str:
    # After this code executes, access_path_register should contain the second to last object in the access path
    if len(access_path.fields) == 2:
        # TODO: case accounted for by calling code
        pass

    base_object_smali_type = access_path.fields[0].get_smali_type()
    child_field_name = access_path.fields[1].fieldName
    child_smali_type = access_path.fields[1].get_smali_type()

    code = f"""    iget-object {access_path_register}, {base_object_register}, {base_object_smali_type}->{child_field_name}:{child_smali_type}
"""
    # limit range to len(access_path.fields) - 2 since we're only getting the second to last object
    # i.e., this code should only run if >= 4 fields in access path
    for i in range(1, len(access_path.fields) - 2):
        cur_parent_type = access_path.fields[i].get_smali_type()
        cur_child_field_name = access_path.fields[i+1].fieldName
        cur_child_type = access_path.fields[i+1].get_smali_type()

        # read from & write to the same register
        code = f"""    iget-object {access_path_register}, {access_path_register}, {cur_parent_type}->{cur_child_field_name}:{cur_child_type}
"""

    # opcode = "iget-object" # will change if field is not an object or field is of a static class
    # destination_register = "v0"
    # base_object_register = "p0"
    # base_object_type = "Lde/ecspride/Datacontainer;"
    # field_name = "description"
    # field_type = "Ljava/lang/String;"
    # instance_field_reference = f"{base_object_type}->{field_name}:{field_type}"
    # code = f"    {opcode} {destination_register}, {base_object_register}, {instance_field_reference}"
    return code


def sources_to_harness(sources_list: str) -> List[MethodSignature]:

    with open(sources_list, "r") as file:
        sources_text = file.read()
    signatures = [MethodSignature.from_source_string(line.strip()) for line in sources_text.splitlines()]
    return signatures

def extract_private_string(flagged_string_value: str) -> Set[str]:
    # Given a value that was flagged as sensitive, find the specific ad hoc string led to the value being flagged. 
    # Reference implementation in HeapSnapshot

    """
    private static final List<String> PII = Arrays.asList("8901240197155182897", "355458061189396", "ZX1H22KHQK", "b91481e8-4bfc-47ce-82b6-728c3f6bff60", "f8:cf:c5:d1:02:e8", "f8:cf:c5:d1:02:e7", "tester.sefm@gmail.com", "Class-Deliver-Put-Earn-5", 
    // Unique-ish Strings observed from "Ljava/util/Locale; toString", "Ljava/util/Locale; toString", "Landroid/provider/Settings$Secure; getString", "Landroid/net/nsd/NsdServiceInfo; getServiceName", respectively.
    "en_US", "3a15cc3d742be836", "Q2hhbm5lbF8wMA:OhXMPXQr6DY:");

    private static final String HARNESSED_PII_PATTERN = "\\*\\*\\*\\d{12}\\*\\*\\*";
    """
    a_priori_strings = ["8901240197155182897", "355458061189396", "ZX1H22KHQK", "b91481e8-4bfc-47ce-82b6-728c3f6bff60", "f8:cf:c5:d1:02:e8", "f8:cf:c5:d1:02:e7", "tester.sefm@gmail.com", "Class-Deliver-Put-Earn-5", "en_US", "3a15cc3d742be836", "Q2hhbm5lbF8wMA:OhXMPXQr6DY:"]
    pattern = r"\*\*\*\d{12}\*\*\*"

    private_strings = set()

    for a_priori_string in a_priori_strings:
        if a_priori_string in flagged_string_value:
            private_strings.add(a_priori_string)
    
    test = 'Error reading file: ***000000186130***'
    matches = re.findall(pattern, flagged_string_value)
    if len(matches) > 0:
        private_strings = private_strings.union(set(matches))

    if len(private_strings) > 0:
        return private_strings
    else:
        logger.error(f"Unable to determine private string that caused flag on value: {flagged_string_value}")
        return {"UNKNOWN"}
    

if __name__ == '__main__':
    pass


