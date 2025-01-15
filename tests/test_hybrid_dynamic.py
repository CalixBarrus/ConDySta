from hybrid import dynamic    
from hybrid.AccessPath import AccessPath
from hybrid.dynamic import ExecutionObservation
from intercept.InstrumentationReport import InstrumentationReport

# def test_find_logcat_errors_anr_errors():

#     path = "tests/data/hybrid/dynamic/0.eu.kanade.tachiyomi_41.apk.log"
#     errors = dynamic.find_logcat_errors(path)

#     assert errors == ["42"]

#     # assert False


# def test_find_logcat_errors_class_not_found_errors():

#     path = "tests/data/hybrid/dynamic/1.io.github.lonamiwebs.klooni_820.apk.log"
#     errors = dynamic.find_logcat_errors(path)

#     assert errors == ["42"]


def get_mock_result(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="a"):
    report = get_mock_instrumentation_report(is_arg=is_arg, is_return=is_return, arg_register_index=arg_register_index, is_before=is_before)
    if access_path == "a":
        path = AccessPath("[<org.Container .>, <java.lang.String secret>]")
    elif access_path == "b":
        path = AccessPath("[<org.Container .>, <java.lang.String public>]")
    
    return (report, AccessPath("[<org.Container .>, <java.lang.String secret>]"),"42")

def get_mock_instrumentation_report(is_arg=False, is_return=True, arg_register_index=-1, is_before=False):
    return InstrumentationReport(
            invoke_id=1,
            invocation_java_signature="java.lang.String toString()",
            enclosing_method_name="exampleMethod",
            enclosing_class_name="ExampleClass",
            is_arg_register=is_arg,
            is_return_register=is_return,
            invocation_argument_register_index=arg_register_index,
            is_before_invoke=is_before,
            invocation_argument_register_name="_",
            invocation_argument_register_type="_",
            is_static=False
        )

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
