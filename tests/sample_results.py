import pytest
from hybrid.invocation_register_context import InvocationRegisterContext
from hybrid.access_path import AccessPath
from intercept.InstrumentationReport import InstrumentationReport
from util.input import ApkModel

def get_mock_instrumentation_report(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, content="placeholder") -> InstrumentationReport:
    if content == "placeholder":
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
    elif content == "blackbox-call":
        return InstrumentationReport(
                invoke_id=1,
                invocation_java_signature="com.example.instrumentableexample.Parent blackBox(com.example.instrumentableexample.Parent)", 
                enclosing_method_name="onCreate",
                enclosing_class_name="Lcom/example/instrumentableexample/MainActivity;",
                is_arg_register=is_arg,
                is_return_register=is_return,
                invocation_argument_register_index=arg_register_index,
                is_before_invoke=is_before,
                invocation_argument_register_name=("v1" if is_arg else "v2"),
                invocation_argument_register_type="Lcom/example/instrumentableexample/Parent;",
                is_static=True
            )

def get_mock_access_path(access_path="a") -> AccessPath:
    if access_path == "a":
        path = AccessPath("[<org.Container .>, <java.lang.String secret>]")
    elif access_path == "b":
        path = AccessPath("[<org.Container .>, <java.lang.String public>]")
    elif access_path == "parent-string":
        path = AccessPath("[<com.example.instrumentableexample.Parent .>, <java.lang.String string>]")
    elif access_path == "parent-child-string":
        path = AccessPath("[<com.example.instrumentableexample.Parent .>, <com.example.instrumentableexample.Child b>, <java.lang.String str>]")

    return path

def get_mock_result(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="a") -> InvocationRegisterContext:
    report = get_mock_instrumentation_report(is_arg=is_arg, is_return=is_return, arg_register_index=arg_register_index, is_before=is_before)

    path = get_mock_access_path(access_path)


    return (report, path,"42")