from experiment.batch import process_as_dataframe
from experiment.benchmark_name import BenchmarkName
from hybrid.hybrid_config import source_sink_file_path
from hybrid.source_sink import MethodSignature, SourceSinkSignatures
from intercept.instrument import HarnessObservations
from util.input import InputModel


def get_default_source_sink_path(benchmark_name: str, fd_default: bool=False):
    if fd_default:
        return "data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"

    if benchmark_name == "fossdroid":
        return "data/sources-and-sinks/SS-from-fossdroid-ground-truth.txt"
    elif BenchmarkName.FOSSDROID:
        return "data/sources-and-sinks/SS-from-fossdroid-ground-truth.txt"
    elif benchmark_name == "gpbench":
        return "data/sources-and-sinks/ss-gpl.txt"
    elif BenchmarkName.GPBENCH:
        return "data/sources-and-sinks/ss-gpl.txt"
    else:
        raise NotImplementedError


def source_list_of_inserted_taint_function_single(default_ss_list: str, modified_ss_list_directory: str, input_model: InputModel) -> str:
    # Remove all sources and just include those placed by the harness

    # load source sink list
    source_sink: SourceSinkSignatures = SourceSinkSignatures.from_file(default_ss_list)

    source_sink.source_signatures = set()

    # add desired function
    # from instrument.py _invocation_observation_taint_code
    "Lcom/example/taintinsertion/TaintInsertion;->taint()Ljava/lang/String;"
    "Lcom/example/taintinsertion/TaintInsertion;->taint()Ljava/lang/String;"
    "Lcom/example/taintinsertion/TaintInsertion;->taint()Ljava/lang/String;"

    harness_observations = HarnessObservations()
    taint_functions = [MethodSignature.from_smali_style_signature(smali_method) for smali_method in harness_observations.get_all_static_taint_methods()]
    list(map(source_sink.source_signatures.add, taint_functions))

    # save new copy
    modified_ss_list_path = source_sink_file_path(modified_ss_list_directory, input_model)
    source_sink.write_to_file(modified_ss_list_path)

    # return file name of new copy
    return modified_ss_list_path
# TODO: This needs to be moved somewhere else
# TODO: this and above should be handled differently??????
# TODO: similar thing done in observation_processing
# def source_list_with_inserted_taint_function_batch(default_ss_list: str, modified_ss_list_directory: str, input_model: str, input_df: pd.DataFrame, output_col: str="") -> pd.Series:
#     assert input_model in input_df.columns

#     if output_col != "":
#         if not output_col in input_df.columns:
#             input_df[output_col] = "" # or some other null value? 
#         else:
#             result_series = pd.Series(index=input_df.index)

#     for i in input_df.index:
#         result = source_list_with_inserted_taint_function_single(default_ss_list, modified_ss_list_directory, input_df.loc[i, input_model])
#         if output_col != "":
#             input_df.at[i, output_col] = result
#         else:
#             result_series.at[i] = result

#     if output_col != "":
#         return None
#     else:
#         return result_series

source_list_of_inserted_taint_function_batch = process_as_dataframe(source_list_of_inserted_taint_function_single, [False, False, True], [])




def source_list_with_inserted_taint_function_single(default_ss_list: str, modified_ss_list_directory: str, input_model: InputModel) -> str:
    # load source sink list
    source_sink: SourceSinkSignatures = SourceSinkSignatures.from_file(default_ss_list)

    # add desired function
    # from instrument.py _invocation_observation_taint_code
    "Lcom/example/taintinsertion/TaintInsertion;->taint()Ljava/lang/String;"
    # new_taint_functions: Set[MethodSignature] = set()
    new_taint_function = MethodSignature.from_java_style_signature("<com.example.taintinsertion.TaintInsertion: java.lang.String taint()>")
    source_sink.source_signatures.add(new_taint_function)

    # save new copy
    modified_ss_list_path = source_sink_file_path(modified_ss_list_directory, input_model)
    source_sink.write_to_file(modified_ss_list_path)

    # return file name of new copy
    return modified_ss_list_path

