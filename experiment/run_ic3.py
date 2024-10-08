import os
from subprocess import CalledProcessError, TimeoutExpired
import time
import pandas as pd

from experiment.common import format_num_secs, results_df_from_benchmark_df, setup_additional_directories
from hybrid.ic3 import run_ic3_on_apk, run_ic3_script_on_apk

import util.logger
logger = util.logger.get_logger(__name__)


def run_ic3_generic(experiment_dir_path: str, benchmark_df: pd.DataFrame, **kwargs) -> pd.DataFrame:

    results_df: pd.DataFrame = results_df_from_benchmark_df(benchmark_df)

    android_path = kwargs["android_path"]
    ic3_timeout = kwargs["ic3_timeout"]
        
    ic3_logs_dir_path = setup_additional_directories(experiment_dir_path, ["ic3-logs"])[0]
    ic3_output_dir_path = setup_additional_directories(experiment_dir_path, ["ic3-output"])[0]

    for i in benchmark_df.index:
        # for input_model in input_apks.ungrouped_inputs:
        input_model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore
        

        # Run ic3 to get model for app, get file for FD
        # it makes an ic3 model, or fails to do so. The resulting path needs to get passed to FD (if this thang is being used)
        # These file paths are different, depending on the input. 
        # inputs: params for ic3 behavior, specific input model (plus group_id, i guess, though this should only be done once per apk)
        # dataframe with columns that will be used
        # output: dataframe with the outputs corresponding to the input dataframe
        if "use_model_paths_csv" in kwargs.keys() and kwargs["use_model_paths_csv"]:
            icc_model_path = results_df.loc[input_model.benchmark_id, "ICC Model Path"]
            if not os.path.isfile(str(icc_model_path)):
                results_df.loc[input_model.benchmark_id, "Error Message"] = "No ICC Model"
                continue

        elif "ic3_path" in kwargs.keys():
            ic3_path = kwargs["ic3_path"]
            using_ic3_script = kwargs["using_ic3_script"]
            if not using_ic3_script:
                ic3_log_path = os.path.join(ic3_logs_dir_path, input_model.input_identifier() + ".log")
                try:
                    t0 = time.time()
                    icc_model_path = run_ic3_on_apk(ic3_path, android_path, input_model, ic3_output_dir_path, record_logs=ic3_log_path, timeout=ic3_timeout)
                    
                    results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
                except CalledProcessError as e:
                    logger.error("Exception by ic3; details in " + ic3_log_path + " for apk " + input_model.apk().apk_name)
                    results_df.loc[input_model.benchmark_id, "Error Message"] = "IC3 Exception"
                    # skip the rest of the experiment; Can't run FD properly without the ICC model
                    continue
                except TimeoutExpired as e:
                    logger.error(f"ic3 timed out after {format_num_secs(ic3_timeout)}; details in " + ic3_log_path)
                    results_df.loc[input_model.benchmark_id, "Error Message"] = f"IC3 Timed Out after {format_num_secs(ic3_timeout)} "
                    # skip the rest of the experiment; Can't run FD properly without the ICC model
                    continue
                except ValueError as e:
                    logger.error(f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e))
                    continue
            else: 
                android_jar_path = os.path.join(android_path, f"android-{str(benchmark_df.loc[input_model.benchmark_id, "APILevel"])}", "android.jar")
                try:
                    t0 = time.time()
                    icc_model_path = run_ic3_script_on_apk(ic3_path, input_model.apk().apk_path, android_jar_path, ic3_timeout)
                    results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
                except CalledProcessError as e:
                    logger.error("Exception by ic3; details in " + ic3_path + " for apk " + input_model.apk().apk_name)
                    results_df.loc[i, "Error Message"] = "IC3 Exception"
                    # skip the rest of the experiment; Can't run FD properly without the ICC model
                    continue
                except TimeoutExpired as e:
                    msg = f"ic3 timed out after {format_num_secs(ic3_timeout)}; details in " + ic3_path
                    logger.error(msg)
                    results_df.loc[i, "Error Message"] = msg
                    # skip the rest of the experiment; Can't run FD properly without the ICC model
                    continue
                except ValueError as e:
                    msg = f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e)
                    logger.error(msg)
                    results_df.loc[i, "Error Message"] += msg # type: ignore
                    continue
        else: 
            # ic3_path is ""
            icc_model_path = ""
            pass