from dataclasses import dataclass

# dataclass requires Python 3.10+
# kw_only -> constructor calls have to use keywords
# slots -> errors will be thrown if any fields not declared here are accessed

@dataclass(kw_only=True,slots=True)
class InstrumentationReport:
    """ This model class is intended to contain information that will be left 
    in hard coded strings in the instrumented code, to be later recovered and reconstructed by a log analysis.
    It is meant to contain all the info that the Static Analysis-based Instrumentation code knows.

    It is meant to pinpoint a specific program point to the granularity of a register before/after being used by a an invocation
    """
    invoke_id: int
    invocation_java_signature: str
    enclosing_method_name: str
    enclosing_class_name: str

    is_arg_register: bool
    is_return_register: bool
    invocation_argument_register_index: int
    is_before_invoke: bool
    invocation_argument_register_name: str
    invocation_argument_register_type: str
    is_static: bool

