
from typing import List
from util.input import ApkModel, InputModel


# HarnessSourcesStep

def harness_with_observed_sources(dataframe):
    # modify DA interpretation results so this step can receive them
    # needs hard interface for intermediate sources & observed contexts
    # implement the guts of this to see what changes need to be made to the jsons being printed out

    expected_cols = ["input_model", "decoded_apk_path", "intermediate_sources", "observed_contexts", "harnessed_apk_path"]

    for row in dataframe:
        # handle fallbacks and things
        dataframe[expected_cols]


    # step should return an input for FD step
    pass

def harness_with_observed_sources_single(input_model: InputModel, decoded_apks_directory_path: str, intermediate_sources, observed_contexts, result_apk_path):
    # modify DA interpretation results so this step can receive them
    # needs hard interface for intermediate sources & observed contexts
    # implement the guts of this to see what changes need to be made to the jsons being printed out

    

    # step should return an input for FD step
    pass