import pytest
from hybrid.invocation_register_context import InvocationRegisterContext
from hybrid.access_path import AccessPath
from intercept.InstrumentationReport import InstrumentationReport
from util.input import ApkModel

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


def get_mock_result(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="a") -> InvocationRegisterContext:
    report = get_mock_instrumentation_report(is_arg=is_arg, is_return=is_return, arg_register_index=arg_register_index, is_before=is_before)
    if access_path == "a":
        path = AccessPath("[<org.Container .>, <java.lang.String secret>]")
    elif access_path == "b":
        path = AccessPath("[<org.Container .>, <java.lang.String public>]")

    return (report, AccessPath("[<org.Container .>, <java.lang.String secret>]"),"42")