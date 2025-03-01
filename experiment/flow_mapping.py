

from typing import List, Set
import pandas as pd

from hybrid.invocation_register_context import InvocationRegisterContext, reduce_for_field_insensitivity
from intercept.decoded_apk_model import DecodedApkModel
from intercept.instrument import HarnessObservations


def get_observation_harness_to_observed_source_map(harnesser: HarnessObservations, decoded_apk_model: DecodedApkModel, observations: List[InvocationRegisterContext]) -> pd.DataFrame:
    # harnesser - expected to have record_taint_function_mapping enabled.
    # decoded_apk_model - expected to be *not* instrumented. Will only be read, and not written to. 
    #
    # result - key & result columns are fields of harnesser
    #   as of right now, key columns are ["Taint Function Name", "Enclosing Class", "Enclosing Method"]
    #   and result columsn are expected to look up ["Invocation Java Signature", "Argument Register Index", "Access Path"]

    assert harnesser.record_taint_function_mapping
    instrumenters = [harnesser]
    _ = decoded_apk_model.get_code_insertions_for_files(instrumenters, observations)

    df_mapping = harnesser.df_instrumentation_reporting[harnesser.mapping_key_cols + harnesser.mapping_observation_lookup_cols]

    return df_mapping
    
def get_observed_source_to_original_source_map(harnesser: HarnessObservations, decoded_apk_model: DecodedApkModel, observations: List[InvocationRegisterContext]) -> pd.DataFrame:

    # Invocation java signature & context -> set of strings,
    # Then sets of strings map to whatever was observed by the source harnessing, or we use a hardcoded mapping
    # key columns ["Enclosing Class", "Enclosing Method", "Invocation Java Signature", "Argument Register Index", "Access Path"]
        # aka, the instr report(s)
    # lookup columns ["String Set"]

    # use one of two mappings to go from ["Observed Strings"] to ["Source Signature"] or ["Enclosing Class", "Enclosing Method", "Source Signature"]
    # These would be for implicit and explicit, respectively

    # These mappings would be joined on ["String Set"] and ["Observed Strings"]
        # Will need to expand String set/Observed strings into separate rows for the join to work properly

    

    pass

def get_observed_source_to_string_set_map():
    # key columns ["Enclosing Class", "Enclosing Method", "Invocation Java Signature", "Argument Register Index", "Access Path"]
    # aka, the instr report(s)
    # lookup columns ["String Set"]

    # probably query harnesser, with a parallel reduction on observed str sets

    harnesser = HarnessObservations()

    observations: List[InvocationRegisterContext]
    observed_strings: List[Set[str]]

    if harnesser.disable_field_sensitivity:
        # need to reduce observations/string sets in parallel 
        _, reduced_observed_strings = reduce_for_field_insensitivity(harnesser.observations)
        
def get_observation_harness_to_string_set_map(harnesser: HarnessObservations, decoded_apk_model: DecodedApkModel, observations: List[InvocationRegisterContext], observed_strings: List[Set[str]]) -> pd.DataFrame:
    # join get_observation_harness_to_observed_source_map() and get_observed_source_to_string_set_map()
    # which is basically already done by HarnessObservations

    assert harnesser.record_taint_function_mapping
    harnesser.set_observed_strings(observed_strings)
    instrumenters = [harnesser]
    _ = decoded_apk_model.get_code_insertions_for_files(instrumenters, observations)

    # df_mapping = harnesser.df_instrumentation_reporting[harnesser.mapping_key_cols + harnesser.mapping_observation_lookup_cols + harnesser.mapping_str_observation_lookup_cols]
    df_mapping = harnesser.df_instrumentation_reporting[harnesser.mapping_key_cols + harnesser.mapping_str_observation_lookup_cols]

    # TODO: would this need to agg on the mapping_key_cols while unioning the str col?

    return df_mapping
    

def get_observed_string_to_original_source_map() -> pd.DataFrame:

    # load up harnessed sources information if it's available

    pass