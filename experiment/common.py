# from datetime import timedelta
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import typing
import pandas as pd
import os

from experiment import external_path
from experiment.batch import ExperimentStepException, process_as_dataframe
from hybrid.flowdroid import FlowdroidArgs
from hybrid.hybrid_config import _apk_log_file_name, apk_logcat_output_path
from util.input import ApkModel, BatchInputModel, InputModel, input_apks_from_dir

import util.logger
logger = util.logger.get_logger(__name__)

def get_flowdroid_file_paths() -> Dict[str, str]:
    flowdroid_jar_path: str = external_path.flowdroid_jar_path
    
    android_path: str = external_path.android_platforms_directory
    return {
            "flowdroid_jar_path": flowdroid_jar_path,
            "android_path": android_path,
            }

#### End External & Data File Paths Settings

def subset_setup_generic(benchmark_files: Dict[str, str], type: str) -> Dict[str, str]:
    # Set "ids_subset" and "always_new_experiment_directory"
    # "always_new_experiment_directory" will be False for "small", True for the rest

    benchmark_name = benchmark_files["benchmark_name"]
    experiment_args = {} | benchmark_files

    if type == "small":
        if benchmark_name == "gpbench":
            # experiment_args["ids_subset"] = [2,13]
            experiment_args["ids_subset"] = [4]
            # experiment_args["ids_subset"] = [1,2,3,4]
        elif benchmark_name == "fossdroid":
            experiment_args["ids_subset"] = [11,12,13,14]
            # experiment_args["ids_subset"] = [12]
        elif benchmark_name == "droidbench3":
            experiment_args["ids_subset"] = [0,1]
        experiment_args["always_new_experiment_directory"] = False

    elif type == "full":

        if benchmark_name == "gpbench":
            experiment_args["ids_subset"] = list(range(1,20))
        elif benchmark_name == "fossdroid":
            experiment_args["ids_subset"] = None
        elif benchmark_name == "droidbench3":
            experiment_args["ids_subset"] = None
        experiment_args["always_new_experiment_directory"] = True
    elif type == "several":
        if benchmark_name == "gpbench":
            experiment_args["ids_subset"] = list(range(1,5))
        elif benchmark_name == "fossdroid":
            experiment_args["ids_subset"] = list(range(0,4))
        elif benchmark_name == "droidbench3":
            experiment_args["ids_subset"] = list(range(0,4))
        experiment_args["always_new_experiment_directory"] = True
    elif type == "misc":
        # Don't set anything. Errors will help users figure out what they need to set.
        pass
    else:
        assert False

    return experiment_args

def flowdroid_setup_generic(benchmark_files: Dict[str, str], type: str) -> Dict[str, str]:
    experiment_args = {} | get_flowdroid_file_paths()

    # experiment_args = experiment_args | benchmark_files
    # Set "ids_subset" and "always_new_experiment_directory"
    experiment_args = experiment_args | subset_setup_generic(benchmark_files, type)

    # benchmark_name = benchmark_files["benchmark_name"]

    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.default_settings)
    
    if type == "small":
        # Don't tweak "timeout" if it was already set by the client.
        if "timeout" not in experiment_args.keys():
            # experiment_args["timeout"] = 15 * 60
            experiment_args["timeout"] = 5
        
    elif type == "full":
        if "timeout" not in experiment_args.keys():
                # experiment_args["timeout"] = 45 * 60
                experiment_args["timeout"] = 15 * 60

    elif type == "misc":
        # Don't set anything. Errors will help users figure out what they need to set.
        pass
    else:
        assert False

    return experiment_args

def instrumentation_arguments_default(benchmark_files: Dict[str, str]=None) -> Dict[str, str]:
    # TODO: This doesn't account for the need to harness different sources for gpbench spyware scenario

    if benchmark_files is None:
        instrumentation_strategy = ["StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy"]
        return instrumentation_strategy

    # instrumentation_strategy = ["StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy"]
    instrumentation_strategy = ["StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy", "HarnessSources"]    

    arguments = {"instrumentation_strategy": instrumentation_strategy}

    if "HarnessSources" in instrumentation_strategy:
        harness_sources_directory = os.path.join(get_project_root_path(), "data", "harness-sources")
        if benchmark_files["benchmark_name"] == "gpbench":
            harness_sources_path = os.path.join(harness_sources_directory, "gpbench-harness-sources.txt")
        elif benchmark_files["benchmark_name"] == "fossdroid":
            harness_sources_path = os.path.join(harness_sources_directory, "fossdroid-harness-sources.txt")
        arguments["harness_sources"] = harness_sources_path

    return arguments

def observation_arguments_default(logcat_directory_path: str) -> Dict[str, str]:
    experiment_args = {}
    experiment_args["logcat_processing_strategy"] = "InstrReportReturnAndArgsDynamicLogProcessingStrategy"
    experiment_args["logcat_directory_path"] = logcat_directory_path

    return experiment_args



class AbstractStep(ABC):
    # Abstracts repeated operations that should be done on a per step basis (save off metadata)
    @abstractmethod
    def execute(self, input=""):
        # Maybe this should be more than one method depending on how the outputs be (if its a df, stuff written to an input col, or both)
        pass

    @property
    @abstractmethod
    def params(self) -> List[str]:
        # params that will be saved off as metadata for the given step. 
        raise NotImplementedError()
    
    # do metadata management inside of here
    # have a test & debug & performance setting/mode

#### Start Internal File Stuff

def benchmark_description_path_from_benchmark_files(benchmark_files: Dict[str, str]) -> str:
    return "" if "benchmark_description_path" not in benchmark_files.keys() else benchmark_files["benchmark_description_path"]

def setup_dirs_with_ic3(experiment_name, experiment_description):
    # TODO: refactor this out
    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, {})
    dir_names = ["ic3_output", "ic3-logs", "flowdroid-logs"]
    df_path =  os.path.join(experiment_dir_path, experiment_id + ".csv")
    return df_path, *setup_additional_directories(experiment_dir_path, dir_names)

def setup_dirs_with_dependency_info(experiment_name: str, experiment_description: str, dir_names: List[str], dependency_dict: Dict[str,typing.Any], always_new_experiment_directory: bool=False) -> Tuple[str, List[str]]:
    # TODO: refactor this out
    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict, always_new_experiment_directory)

    df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    return df_path, setup_additional_directories(experiment_dir_path, dir_names)

def get_experiment_name(dataset_name: str, step_name: str, version: Tuple[int,int,int], params: List=[], date_override: str="", reproduction: int=-1) -> str:
    if date_override != "":
        # "YYYY-MM-DD"
        date = str(pd.to_datetime('today').date())
    else: 
        date = date_override

    version_str = ".".join([str(num) for num in version])

    reproduction_list = ([] if reproduction == -1 else [f"rep{reproduction}"])
    return "_".join([date, step_name, dataset_name, version_str] + params + reproduction_list)
    # return f"date_dataset_version_params"

def setup_experiment_dir(experiment_name: str, experiment_description: str, dependency_dict: Dict[str,typing.Any], always_new_experiment_directory: bool=False) -> Tuple[str, str]:
    # TODO: this should be refactored into ResultPathManager
    experiment_description += ('\n')
    for key, value in dependency_dict.items():
        if key in ["experiment_name", "experiment_description"]:
            # These args should already be in the experiment_description
            continue
        if key == "timeout":
            experiment_description += (f"{key}: {format_num_secs(value)}\n")
            continue
        if key == "flowdroid_args":
            experiment_description += (f"{key}: {str(value.args)}\n")
            continue
        experiment_description += (f"{key}: {value}\n")

    # "YYYY-MM-DD"
    date = str(pd.to_datetime('today').date())
    experiment_id = date + "-" + experiment_name

    if always_new_experiment_directory:
        # Check experiment directory for items of form expriment_id[n], and find the next n for which there is no directory
        experiment_names = os.listdir(os.path.join("data", "experiments"))
        if experiment_id in experiment_names:

            # if more than 20 dirs, just keep overwriting the original dir
            for i in range(0,20):
                if experiment_id + str(i) not in experiment_names:
                    logger.info(f"Replacing experiment_id {experiment_id} with {experiment_id + str(i)}")
                    experiment_id = experiment_id + str(i)
                    break

    experiment_directory_path = os.path.join("data", "experiments", experiment_id)    
    for dir_path in [os.path.join("data"), os.path.join("data", "experiments"), experiment_directory_path]:
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

    # Record experiment description
    readme_path = os.path.join(experiment_directory_path, "README.txt")
    with open(readme_path, 'w') as file:
        file.write(experiment_description)

    experiment_log_path = os.path.join(experiment_directory_path, f"{experiment_id}.log")
    util.logger.set_all_loggers_file_handler(experiment_log_path)

    return experiment_id, experiment_directory_path

def setup_additional_directories(experiment_dir_path: str, dir_names: List[str]) -> List[str]:
    # TODO: this should probably not act on lists; that's not any of the use cases I'm coding right now
    # setup new directories in the experiment directory. If a directory name is already taken, create and return one with a slightly tweaked name.
    dir_paths = []
    for dir_name in dir_names:
        dir_path = os.path.join(experiment_dir_path, dir_name)


        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)
        dir_paths.append(dir_path)
    
    return dir_paths

def next_available_directory_name(base_directory_path: str, new_directory_name: str):
    file_names = os.listdir(base_directory_path)
    
    if new_directory_name not in file_names:
        available_directory_name = new_directory_name
    else:
        modified_directory_name = new_directory_name
        # if more than 20 dirs, just keep overwriting the original dir
        for i in range(0,20):
            if new_directory_name + str(i) not in file_names:
                logger.info(f"Replacing directory {new_directory_name} with {new_directory_name + str(i)}")
                modified_directory_name = new_directory_name + str(i)
                break

        available_directory_name = modified_directory_name

    return available_directory_name
    
def recent_experiment_directory_path(size: str, base_name: str, benchmark_name: str, filter_word: str="") -> str:
    experiments_directory_path = os.path.join(get_project_root_path(), "data", "experiments")

    # directory_base_name = "execution-test-"

    filtered_names = [directory_name for directory_name in os.listdir(experiments_directory_path) if base_name in directory_name and size in directory_name and benchmark_name in directory_name]
    if filter_word != "":
        filtered_names = [name for name in filtered_names if filter_word in name]
    filtered_names.sort()

    if len(filtered_names) != 0:
        logger.debug(os.listdir(experiments_directory_path), )
    assert len(filtered_names) != 0

    result = os.path.join(experiments_directory_path, filtered_names[-1])

    logger.debug(f"Looked up recent directory: {result} from {filtered_names}")
    return result

def source_sink_dir_path() -> str:
    return "data/sources-and-sinks"

#### End Internal File Stuff

def format_num_secs(secs: int) -> str:
    td = pd.Timedelta(seconds=secs)
    td = td.round('s')
    
    return f"{td.seconds // (60 * 60)}h{(td.seconds % (60 * 60)) // 60}m{td.seconds % (60)}s"

def find_xml_paths_in_dir_recursive(dir_path: str) -> List[str]:
    """ Recursively traverse the target directory and it's children. Return all apks
        discovered. """
    result = []

    for item in os.listdir(dir_path):
        new_path = os.path.join(dir_path, item)

        if new_path.endswith(".xml"):
            result.append(new_path)
        elif os.path.isdir(new_path):
            result += find_xml_paths_in_dir_recursive(new_path)
    return result

def benchmark_df_from_benchmark_directory_path(benchmark_directory_path: str, benchmark_description_csv_path: str="", ids_subset: pd.Series=None) -> pd.DataFrame:
    # TODO: make loader class? Will want parallel loader classes for picking up at the start of any given step? 

    inputs_model = input_apks_from_dir(benchmark_directory_path)
    benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model, benchmark_description_csv_path=benchmark_description_csv_path)


    if ids_subset is not None:
        benchmark_df = benchmark_df.loc[ids_subset]

    return benchmark_df

def benchmark_df_base_from_batch_input_model(inputs_model: BatchInputModel, benchmark_description_csv_path: str=""):

    inputs = inputs_model.ungrouped_inputs
    # inputs = inputs_model.ungrouped_inputs + inputs_model.grouped_inputs

    benchmark_df = pd.DataFrame({"Benchmark ID": list(range(len(inputs))),
                    "Input Model": inputs})
    assert (benchmark_df.index == benchmark_df["Benchmark ID"]).all()

    for i in benchmark_df.index:
        benchmark_df.loc[i, "Input Model"].benchmark_id = i # type: ignore

    # TODO: everything after here is garbage
    if benchmark_description_csv_path != "":

        description_df = description_df_from_path(benchmark_description_csv_path)

        # if "AppID" in description_df.columns:
        #     description_df = description_df.set_index(description_df["AppID"])
        # else: 
        #     description_df["AppID"] = description_df.index

        # Change the Benchmark IDs to match the AppID's from the description.
        if os.path.basename(benchmark_description_csv_path) == "gpbench-info.csv":
            # Join on description_df["AppName"], where a given apk_name is [AppID].[AppName].apk
            description_df_apk_names = description_df["AppID"].astype(str) + "." + description_df["AppName"] + ".apk"
        elif os.path.basename(benchmark_description_csv_path) == "fossdroid-ids-ordering.csv":
            # df index is benchmark ID, APK Name should match input model's apk name
            description_df["AppID"] = description_df.index
            description_df_apk_names = description_df["APK Name"]
        else: 
            description_df_apk_names = description_df["apk"].apply(lambda path: os.path.basename(path))
            # logger.debug(description_df_apk_names)

        for i in benchmark_df.index:
            model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore

            mask = description_df_apk_names == model.apk().apk_name 
            assert sum(mask) == 1
            # logger.debug(f"{str(i)}, {str(description_df[mask]["AppID"].iloc[0])}")
            benchmark_df.loc[i, "Benchmark ID"] = description_df[mask]["AppID"].iloc[0]
            model.benchmark_id = description_df[mask]["AppID"].iloc[0]

        benchmark_df = benchmark_df.set_index("Benchmark ID")
        benchmark_df["Benchmark ID"] = benchmark_df.index

    benchmark_df.sort_index(inplace=True)

    return benchmark_df

def description_df_from_path(benchmark_description_path: str):
    description_df = pd.read_csv(benchmark_description_path, header=0)

    if "AppID" in description_df.columns:
        description_df = description_df.set_index(description_df["AppID"])
    else: 
        description_df["AppID"] = description_df.index

    return description_df

# def load_logcat_files_batch(logcat_files_directory: str, input_identifier: str, input_df: pd.DataFrame, output_col=""):
#     assert input_identifier in input_df.columns

#     last_error_column = "last_error" # TODO: This should live with Batch code; ideally the "single" steps should throw a custom type of error that will get caught and handled by the batch code.
#     if last_error_column not in input_df.columns:
#         input_df[last_error_column] = ""

#     if output_col != "":
#         if not output_col in input_df.columns:
#             input_df[output_col] = "" # or some other null value? 
#         else:
#             result_series = pd.Series(index=input_df.index)

    
#     for i in input_df[input_df[last_error_column] == ""].index: # Filter out rows with errors.
#         try:
#             result = load_logcat_file_single(logcat_files_directory, input_df.at[i, input_identifier])
#             if output_col != "":
#                 input_df.at[i, output_col] = result
#             else:
#                 result_series.at[i] = result

#         except Exception as e:
#             input_df.at[i, last_error_column] = e.__str__()
#             logger.error(e)

#     if output_col != "":
#         return None
#     else:
#         return result_series
    


def load_logcat_file_single(logcat_files_directory: str, input_identifier: str) -> str:
    # apk_logcat_output_path(logcat_files_directory, InputModel, grouped_apk_idx)
    logcat = os.path.join(logcat_files_directory, _apk_log_file_name(input_identifier))
    
    # make sure it's actually there
    # assert os.path.isfile(logcat)
    if not os.path.isfile(logcat):
        raise ExperimentStepException(f"Logcat file {logcat} not found.")
        # raise AssertionError(f"Logcat file {logcat} not found.")

    return logcat

load_logcat_files_batch = process_as_dataframe(load_logcat_file_single, [False, True], [])

### End LoadBenchmarksStep

def get_project_root_path() -> str:

    return os.path.dirname(os.path.dirname(__file__))


def modified_source_sink_path(modified_source_sink_directory_path: str, input_model: InputModel, grouped_apk_idx: int=-1, is_xml: bool=False):
    # modified_source_sink_directory = 
    return os.path.join(
        modified_source_sink_directory_path, input_model.input_identifier(grouped_apk_idx) + "source-sinks") + (".xml" if is_xml else ".txt")


def results_df_from_benchmark_df(benchmark_df: pd.DataFrame, benchmark_description_path: str="") -> pd.DataFrame:
    # Sets up new dataframe with index/Benchmark ID column, and APK Name column that match up with the benchmark_df.
    # Results data frames start with an empty Error Message column

    # Optionally copy over selected columns from the indicated csv file

    # results_df = benchmark_df[["Benchmark ID"]]
    results_df = pd.DataFrame({}, index=benchmark_df.index)
    if "APK Name" not in benchmark_df.columns:
        results_df["APK Name"] = ""
        for i in benchmark_df.index:
            results_df.loc[i, "APK Name"] = benchmark_df.loc[i, "Input Model"].apk().apk_name # type: ignore
    else:
        results_df["APK Name"] = benchmark_df["APK Name"]

    results_df["Error Message"] = ""

    if benchmark_description_path != "":
        description_df = description_df_from_path(benchmark_description_path)
        # print(f"{description_df.index}, {results_df.index}")
        # assert  == 

        if os.path.basename(benchmark_description_path) == "gpbench-info.csv":
            cols_to_copy = ["UBC # of Expected Flows", "UBC FlowDroid v2.7.1 Detected Flows"]
        elif os.path.basename(benchmark_description_path) == "fossdroid_config_aplength5_replication1.csv" or os.path.basename(benchmark_description_path) == "fossdroid_config_2way2_replication1.csv":
            cols_to_copy = ["num_flows", "time", "total_TP", "detected_TP", "total_FP", "detected_FP"]
        else:
            raise NotImplementedError()

        results_df[cols_to_copy] = description_df[cols_to_copy]

    return results_df


if __name__ == "__main__":
    # benchmark_files = get_droidbench_files_paths3()
    # benchmark_directory_path = benchmark_files["benchmark_dir_path"]
    # # benchmark_description_csv_path = benchmark_files[""]
    # inputs_model = input_apks_from_dir(benchmark_directory_path)
    # # benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model, benchmark_description_csv_path=benchmark_description_csv_path)
    # benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model)
    # benchmark_df.to_csv("droidbench3-test.csv")
    pass
