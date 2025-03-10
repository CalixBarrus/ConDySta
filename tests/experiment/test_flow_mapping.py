


import os
import shutil
import pandas as pd
import pytest
from experiment.benchmark_name import BenchmarkName
from experiment.flow_mapping import apply_flow_mapping, get_observation_harness_to_observed_source_map, get_observation_harness_to_string_set_map, get_observed_string_to_original_source_map
from intercept.decoded_apk_model import DecodedApkModel
from intercept.instrument import HarnessObservations
from tests.sample_results import get_mock_invocation_register_context

@pytest.fixture
def decompiled_apk_copy_readonly():
    # copy smali dirs
    decompiled_apk = "tests/data/decompiledInstrumentableExample/app-debug"
    assert os.path.exists(decompiled_apk)

    copy_readonly = os.path.join("tests/data/decompiledInstrumentableExample_copyreadonly", "app-debug")
    
    if not os.path.exists(copy_readonly):
        shutil.copytree(decompiled_apk, copy_readonly, dirs_exist_ok=False)
    else: 
        # blithely assume the users actually treat is as readonly, so don't do the next two lines
        # shutil.rmtree(copy_readonly)
        # shutil.copytree(decompiled_apk, copy_readonly, dirs_exist_ok=False)
        pass

    yield copy_readonly
    
    # don't delete after


def test_get_observation_harness_to_observed_source_map_smoke(decompiled_apk_copy_readonly):
    
    harnesser = HarnessObservations(record_taint_function_mapping=True)
    decoded_apk_model = DecodedApkModel(decompiled_apk_copy_readonly)
    observations = [get_mock_invocation_register_context(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="parent-string", content="blackbox-call"), 
                    get_mock_invocation_register_context(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="parent-child-string", content="blackbox-call"), 
                    get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="parent-string", content="blackbox-call"), 
                    get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="parent-child-string", content="blackbox-call"), 
                    ]
    df = get_observation_harness_to_observed_source_map(harnesser, decoded_apk_model, observations)

    # Should be 4 rows, one per unique context
    assert len(df) == 4 
    # taint functions should all be different since these are all in the same enclosing class/method
    assert len(df[harnesser.mapping_key_cols[0]].unique()) == 4


def test_get_observation_harness_to_string_set_map_smoke(decompiled_apk_copy_readonly):
    harnesser = HarnessObservations(record_taint_function_mapping=True)
    decoded_apk_model = DecodedApkModel(decompiled_apk_copy_readonly)

    observations = [get_mock_invocation_register_context(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="parent-string", content="blackbox-call"), 
                get_mock_invocation_register_context(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="parent-child-string", content="blackbox-call"), 
                # get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="parent-string", content="blackbox-call"), 
                get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="parent-child-string", content="blackbox-call"), 
                ]
    observed_strings = [
        set(["a"]),
        set(["b", "c"]),
        # set([]),
        set(["d"]),
    ]
    df = get_observation_harness_to_string_set_map(harnesser, decoded_apk_model, observations, observed_strings)


    # Should be 4 cols, 3 for key and 1 for the string sets
    assert len(df.columns) == 4 
    # Taint functions should be unique -> rows shouldn't have been reduced -> observed string sets should all be different like the test input
    # assert len(df[harnesser.mapping_str_observation_lookup_cols[0]].unique()) == 3
    assert df.at[0, harnesser.mapping_str_observation_lookup_cols[0]] == set(["a"])


@pytest.mark.parametrize("benchmark_name", 
    [
        (BenchmarkName.FOSSDROID),
        (BenchmarkName.GPBENCH),
    ],)
def test_get_observed_string_to_original_source_map_smoke(benchmark_name):
    mapping_df = get_observed_string_to_original_source_map(benchmark_name)

    assert mapping_df.shape[0] > 0

def test_get_observed_string_to_original_source_map_source_harness_parses_without_crashing():

    benchmark_name = BenchmarkName.FOSSDROID
    log_with_source_harnessing = "tests/data-persistent/mock_da_results/fossdroid/0.eu.kanade.tachiyomi_41.apk.log"
    mapping_df = get_observed_string_to_original_source_map(benchmark_name, log_with_source_harnessing)

    assert mapping_df.shape[0] > 0

    # context should be filled out for many mapping rows
    assert not all(mapping_df["enclosing_class"] != "")

def test_apply_flow_mapping_cross_demo():

    df3 = pd.DataFrame({"a": list(range(5)), 
                        "expected_string_observed": ["secret1", "secret2", "secret3", "***secret1***", "***secret2***"],
                        "scenario": ["profile", "profile", "profile", "intercept", "intercept"],
                        "source_function": ["", "", "", "getImei()", "getLocale()"],
                        "source_function_context": ["", "", "", "CatTown/build()", "CatTown/build()"],
                        })

    df2 = pd.DataFrame({"d": list(range(3)), 
                        "string_observed": ["secret1", "secret2", "***secret1***"], 
                        "taint_function_name": ["taint1", "taint2", "taint3"],
                        "context_method": ["", "", "mlem()"],
                        "context_class": ["", "", "Cats"],
                        })

    df1 = pd.DataFrame({"f": list(range(6)), 
                        "taint_function_name": ["taint1", "taint1", "taint1", "taint2", "taint2", "taint3"], 
                        "context_method": ["a()", "a()", "a()", "a()", "a()", "mlem()"],
                        "context_class": ["Foo", "Foo", "Foo", "Foo", "Foo", "Cats"],
                        "sink_function": ["sink1()", "sink2()", "sink1()", "sink2()", "sink1()", "sink2()"],
                        "sink_context": ["Bar/zap()", "Bar/zap()", "Bar/zap()", "Bar/zap()", "Bar/zap()", "Bar/zap()"],
                        })
    
    m12 = df1.merge(df2, left_on=["taint_function_name", "context_method", "context_class"], 
              right_on=["taint_function_name", "context_method", "context_class"])

    mapped_12 = apply_flow_mapping(df1, df2, ["taint_function_name", "context_method", "context_class"], ["taint_function_name", "context_method", "context_class"])

    mapped_23 = apply_flow_mapping(df2, df3, ["string_observed"], ["expected_string_observed"])

    mapped_13 = apply_flow_mapping(mapped_12, df3, ["string_observed"], ["expected_string_observed"])

    assert len(mapped_23) > 1

