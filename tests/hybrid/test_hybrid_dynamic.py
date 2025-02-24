import numpy as np
import pandas as pd
from hybrid import dynamic    
from hybrid.dynamic import ExecutionObservation
from tests.sample_results import get_mock_instrumentation_report, get_mock_result

def test_execution_observation_smoke():
    observation = ExecutionObservation()

    mock_result = get_mock_result()
    observation.parse_instrumentation_result(mock_result[0])

    _ = observation.get_tainting_invocation_ids()

    assert True


def test_execution_observation_get_tainting_invocation_contexts_arg_before_and_after():
    # Test that a taint is not created when an arg is seen before then after
    observation = ExecutionObservation()

    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=1, is_before=True)
    observation.parse_instrumentation_result(mock_result)
    # No leak if only seen before
    assert len(observation.get_tainting_invocation_contexts()) == 0

    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=1, is_before=False)
    observation.parse_instrumentation_result(mock_result)
    # No leak because seen before & after
    assert len(observation.get_tainting_invocation_contexts()) == 0

def test_execution_observation_get_tainting_invocation_contexts_arg_after_and_before():
    # Test that a taint is created then removed when an arg is seen after then before
    
    observation = ExecutionObservation()

    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=1, is_before=False)
    observation.parse_instrumentation_result(mock_result)
    # No leak if only seen before
    assert len(observation.get_tainting_invocation_contexts()) == 1

    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=1, is_before=True)
    observation.parse_instrumentation_result(mock_result)
    # No leak because seen before & after
    assert len(observation.get_tainting_invocation_contexts()) == 0


def test_execution_observation_get_tainting_invocation_contexts_arg_with_access_path_mismatch():
    
    observation = ExecutionObservation()

    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=2, is_before=True)
    observation.parse_instrumentation_result(mock_result)
    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=2, is_before=False, access_path="b")
    observation.parse_instrumentation_result(mock_result)
    # Different access path on second arg, therefore new leak
    assert len(observation.get_tainting_invocation_contexts()) == 1

    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=1, is_before=True, access_path="a")
    observation.parse_instrumentation_result(mock_result)
    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=1, is_before=False, access_path="a")
    observation.parse_instrumentation_result(mock_result)
    # Same access path on first arg, therefore no new leak
    assert len(observation.get_tainting_invocation_contexts()) == 1

def test_execution_observation_get_tainting_invocation_contexts_return():
    
    observation = ExecutionObservation()

    mock_result = get_mock_result(is_arg=False, is_return=True, arg_register_index=-1, is_before=False)
    observation.parse_instrumentation_result(mock_result)
    # Returns should be leaks like normal
    assert len(observation.get_tainting_invocation_contexts()) == 1


def test_execution_observation_get_tainting_invocation_ids_before_and_after():
    # Test that a taint is not created when an arg is seen before then after
    observation = ExecutionObservation()

    mock_instrumentation_report = get_mock_instrumentation_report(is_arg=True, is_return=False, arg_register_index=1, is_before=True)
    observation.parse_instrumentation_result(mock_instrumentation_report)
    # No leak if only seen before
    assert len(observation.get_tainting_invocation_ids()) == 0

    mock_instrumentation_report = get_mock_instrumentation_report(is_arg=True, is_return=False, arg_register_index=1, is_before=False)
    observation.parse_instrumentation_result(mock_instrumentation_report)
    # No leak because seen before & after
    assert len(observation.get_tainting_invocation_ids()) == 0

def test_execution_observation_get_tainting_invocation_ids_after_and_before():
    # Test that a taint is created then destroyed when an arg is seen after then before
    observation = ExecutionObservation()

    mock_instrumentation_report = get_mock_instrumentation_report(is_arg=True, is_return=False, arg_register_index=1, is_before=False)
    observation.parse_instrumentation_result(mock_instrumentation_report)
    # No leak if only seen before
    assert len(observation.get_tainting_invocation_ids()) == 1

    mock_instrumentation_report = get_mock_instrumentation_report(is_arg=True, is_return=False, arg_register_index=1, is_before=True)
    observation.parse_instrumentation_result(mock_instrumentation_report)
    # No leak because seen before & after
    assert len(observation.get_tainting_invocation_ids()) == 0

def test_execution_observation_get_tainting_invocation_ids_return():
    observation = ExecutionObservation()

    mock_instrumentation_report = get_mock_instrumentation_report(is_arg=False, is_return=True, is_before=False)
    observation.parse_instrumentation_result(mock_instrumentation_report)
    # No leak if only seen before
    assert len(observation.get_tainting_invocation_ids()) == 1


def test_execution_observation_get_tainting_invocation_ids_string():
    observation = ExecutionObservation()

    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=2, is_before=False, access_path="b", tainted_string="42")
    observation.parse_instrumentation_result(mock_result)
    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=2, is_before=False, access_path="b", tainted_string="secret")
    observation.parse_instrumentation_result(mock_result)
    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=1, is_before=False, access_path="a", tainted_string="42")
    observation.parse_instrumentation_result(mock_result)
    mock_instr_report = get_mock_instrumentation_report(is_arg=True, is_return=False, arg_register_index=0, is_before=False)
    observation.parse_instrumentation_result(mock_instr_report)

    tainting_invocation_contexts, contexts_strings = observation.get_tainting_invocation_contexts(with_observed_strings=True)
    assert len(tainting_invocation_contexts) == 2

    assert {"42", "secret"} in contexts_strings and {"42"} in contexts_strings

    tainting_invocation_ids, invocation_strings = observation.get_tainting_invocation_ids(with_observed_strings=True)
    assert len(tainting_invocation_ids) == 1
    assert {"42", "secret", "Not-Reported"} in invocation_strings


def test_execution_observation_get_tainting_invocation_contexts_as_table_smoke():
    observation = ExecutionObservation()

    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=2, is_before=False, access_path="b", tainted_string="42")
    observation.parse_instrumentation_result(mock_result)
    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=2, is_before=False, access_path="b", tainted_string="secret")
    observation.parse_instrumentation_result(mock_result)
    mock_result = get_mock_result(is_arg=True, is_return=False, arg_register_index=1, is_before=False, access_path="a", tainted_string="42")
    observation.parse_instrumentation_result(mock_result)

    observations_table = observation.get_tainting_invocation_contexts_as_table(enclosing_class_col="a", enclosing_method_col="b")

    print(observations_table.to_string())

    unique_value_counts = observations_table[["a", "b"]].value_counts()
    assert unique_value_counts.values == np.array([2])

    
