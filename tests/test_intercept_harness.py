import os
from typing import List, Tuple
import pytest
import pandas as pd

from experiment.LoadBenchmark import LoadBenchmark, get_droidbench_files_paths3
from experiment.paths import ResultPathManager, StepInfoInterface
from experiment.common import benchmark_df_from_benchmark_directory_path
from intercept.harness import harness_with_observed_sources
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

    # print(benchmark_df.to_string())


    apk_path = ""
    decompiled_apk_path = ""
    copied_decompiled_apk_path = ""

    apk_model = ""
    intermediate_sources = []
    observed_contexts = []

    # harness_with_observed_sources(copied_decompiled_apk_path, [apk_model], intermediate_sources, observed_contexts)

    # assert target file X was modified
    # Check modification by hand 

if __name__ == "__main__":

    test_harness_with_observed_sources_smoke()