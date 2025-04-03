import os
from typing import List, Tuple
import pytest
import pandas as pd

from experiment.load_benchmark import LoadBenchmark, get_droidbench_files_paths3
from experiment.paths import ResultPathManager, StepInfoInterface
from experiment.common import benchmark_df_from_benchmark_directory_path
from intercept.instrumentation_report import InstrumentationReport
from intercept.decode import DecodeApk
from intercept.harness import harness_with_observed_sources
from intercept.instrument_smali import InstrumentSmali
from intercept.decoded_apk_model import DecodedApkModel
from util.input import InputModel

def check_number(num: str):
    """
    Function to check if the number is negative or positive.
    """
    num = float(num)
    if num >= 0:
        if num == 0:
            return "Zero"
        else:
            return "Positive"
    else:
        return "Negative"

def test_check_number():
    assert check_number("-22") == "Negative"
    assert check_number("0") == "Zero"
    assert check_number("10") == "Positive"


def test_harness_with_observed_sources_smoke():
    # Smoke test for harness_with_observed_sources.
    # Prepare data, including smali for FieldAndObjectSensitivity/FieldSensitivity3, 
    # Copied into a fresh output dir that will be modified in place,
    # also a mocked observation object stating that d1.setSecret at line 29 tainted the access path d1.secret
    # call the function
    # assert # of lines in file is 2 more
    # verify by hand that the correct code was added to the smali.

    """
	- Use from droidbench extended, use FieldAndObjectSensitivity/FieldSensitivity3
	- Given observation that at line 29, the invoke d1.setSecret tainted access path d1.secret
        result should be that d1.secret gets tainted directly after invoke by harnessing-controlled source"""
    

    droidbench_files = get_droidbench_files_paths3()
    load_step = LoadBenchmark(droidbench_files)

    result_path_manager = ResultPathManager(droidbench_files["benchmark_name"], exclusive_dir_path=os.path.join("tests","data"), default_date_override=None)

    benchmark_df: pd.Dataframe = load_step.execute()


    class TestStringReport(StepInfoInterface):
        @property
        def step_name(self) -> str:
            return "test_report"

        @property
        def version(self) -> Tuple[int, int, int]:
            return (1,0,0)

        @property
        def concise_params(self) -> List[str]:
            return ["smoke_test"]
        
        def execute(self, input: pd.DataFrame, result_path: str):
            # Input: df with columns "Input Model"
            # Output: df with columns "APK Name"
            model: InputModel
            input["APK Name"] = input["Input Model"].map(lambda input: input.apk().apk_name)
            
            output = input.to_string()    
            with open(result_path, 'w') as file:
                file.write(output)

            # return input
        
    test_report = TestStringReport()
    test_report.execute(benchmark_df, result_path_manager.get_result_path(test_report))

    FIELD_SENSITIVITY_3_BENCHMARK_ID = 118
    target_mask = benchmark_df["Benchmark ID"] == FIELD_SENSITIVITY_3_BENCHMARK_ID

    # target_row = benchmark_df[benchmark_df["Benchmark ID"] == FIELD_SENSITIVITY_3_BENCHMARK_ID]
    

    # print(benchmark_df.to_string())
    # decompile if not already at the target path
    
    decode_step = DecodeApk()
    # TODO: setting up the input APK path col should in theory be done by the load step
    benchmark_df.loc[target_mask, "Input APK Path"] = benchmark_df.loc[target_mask, "Input Model"].map(lambda input: input.apk().apk_path)
    benchmark_df.loc[target_mask, "Decompiled Path"] = result_path_manager.get_result_paths(decode_step, benchmark_df.loc[target_mask, "Input Model"])
        
    # Only decode apks with no that haven't been decoded.
    already_decoded_mask = benchmark_df.loc[target_mask, "Decompiled Path"].map(lambda path: os.path.isdir(path))
    decode_step.execute(benchmark_df.loc[target_mask & ~already_decoded_mask])

    # Load mocked observations, imitate the output of scan_log_for_instrumentation_report_tuples
    
    instr_report_tuples: List[Tuple[InstrumentationReport, str, str]] = []
    # TODO: there are more steps to the dyn processing of instr report tuples that should be formalized, i.e. deduplication, seeing tainted values -> proposed creations of tainted values
    # assume these tuples are smali points that should produce taints

    # Example: 
    """
    String 'en_US' 
observed at access path [<com.android.internal.view.menu.MenuItemImpl .>, <java.lang.String sLanguage>] 
by report InstrumentationReport(invocation_java_signature='<android.view.Menu: android.view.MenuItem findItem(int)>', invoke_id=318897, enclosing_method_name='onPrepareOptionsMenu', enclosing_class_name='Lnya/miku/wishmaster/ui/MainActivity;', is_arg_register=False, is_return_register=True, invocation_argument_register_index=-1, is_before_invoke=False, invocation_argument_register_name='v7', invocation_argument_register_type='Landroid/view/MenuItem;', is_static=False)
    """
    # # Pull up model of decoded smali for the debugger
    # decoded_apk_path = benchmark_df.loc[target_mask, "Decompiled Path"].iat[0]
    # apk_model = DecodedApkModel(decoded_apk_path)
    # for smali_file in apk_model.smali_directories[0]:
    #     if smali_file.class_name == "Lde/ecspride/FieldSensitivity3;":
    #         # SmaliMethodInvocation(invoke_line_number=70, invoke_kind='invoke-virtual', is_range_kind=False, argument_registers=['v6'], class_name='Lde/ecspride/Datacontainer;', method_name='getSecret', argument_register_types_pre=['Lde/ecspride/Datacontainer;'], return_type='Ljava/lang/String;', move_result_line_number=72, move_result_kind='move-result-object', move_result_register='v3')
    #         print(smali_file)
    """
    invoke-virtual {v6, v1}, Lde/ecspride/Datacontainer;->setSecret(Ljava/lang/String;)V
    """
    instrumentation_report = InstrumentationReport(invocation_java_signature='<de/ecspride/Datacontainer void setSecret(java/lang/String)>', invoke_id=0, enclosing_method_name='onCreate', enclosing_class_name='Lde/ecspride/FieldSensitivity3;', is_arg_register=False, is_return_register=False, invocation_argument_register_index=-1, is_before_invoke=False, invocation_argument_register_name='v6', invocation_argument_register_type='Lde/ecspride/Datacontainer;', is_static=False)
    access_path = ["<com.android.internal.view.menu.MenuItemImpl .>", "<java.lang.String sLanguage>"] 
    instr_report_tuples = [(instrumentation_report, access_path, "sensitive")]
    benchmark_df.loc[target_mask, InstrumentSmali.observations_column] = pd.Series([instr_report_tuples], index=benchmark_df.loc[target_mask].index)

    instrument_step = InstrumentSmali([])
    instrument_output_column = "Instrumented Path"
    benchmark_df.loc[target_mask, instrument_output_column] = result_path_manager.get_result_paths(instrument_step, benchmark_df.loc[target_mask, "Input Model"])
    
    instrument_step.execute(benchmark_df.loc[target_mask], output_path_column=instrument_output_column)

    # harness_with_observed_sources(copied_decompiled_apk_path, [apk_model], intermediate_sources, observed_contexts)

    # assert target file X was modified, lines of code increased
    # Check modification by hand 

if __name__ == "__main__":

    test_harness_with_observed_sources_smoke()