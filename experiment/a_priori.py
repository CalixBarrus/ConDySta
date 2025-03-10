import pandas as pd

from experiment.benchmark_name import BenchmarkName

def a_priori_string_info(name: BenchmarkName) -> pd.DataFrame:
    general_a_priori_strings = "data/a-priori-strings/general-a-priori-strings.csv"
    gpbench_a_priori_strings = "data/a-priori-strings/gpbench-l-a-priori-strings.csv"

    match name:
        case BenchmarkName.FOSSDROID:
            # Load general
            df = load_a_priori_string_info(general_a_priori_strings)
        case BenchmarkName.GPBENCH:
            # Load both gpbench and general
            df = pd.concat((load_a_priori_string_info(gpbench_a_priori_strings), load_a_priori_string_info(general_a_priori_strings)), ignore_index=True)

    return df

A_PRIORI_STRING_INFO_COLUMNS = ["value", "expected-source-method", "scenario", "scenario-category"]

def load_a_priori_string_info(path: str) -> pd.DataFrame:
    
    df = pd.read_csv(path, delimiter=";")

    return df

