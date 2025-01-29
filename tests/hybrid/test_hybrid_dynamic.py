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
    # Different access path on second arg, no new leak
    assert len(observation.get_tainting_invocation_contexts()) == 0

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
