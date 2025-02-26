
from typing import List, Set, Tuple

import pandas as pd

from hybrid.invocation_register_context import InvocationRegisterContext
from intercept.InstrumentationReport import InstrumentationReport


def save_to_file(file, contents):
    # Overwrite file
    with open(file, 'w') as out_file:
        out_file.write(contents)

def instrumentation_reports_details(instrumentation_report_tuples: Tuple) -> str:
    details = ""
    details += f"Instrumentation reports observing tainted strings {len(instrumentation_report_tuples)} times.\n"
    details += "\n".join([f"String '{observed_string}' \nobserved at access path {str(access_path)} \nby report {str(report)}" for report, access_path, observed_string in instrumentation_report_tuples])
    return details


def observed_intermediate_sources_details(tainting_invocation_contexts: List[InvocationRegisterContext], contexts_strings:List[Set[str]]):
    details = f"{len(tainting_invocation_contexts)} contexts observed to produce target strings\n"

    intermediate_sources_df = pd.DataFrame(index=range(len(tainting_invocation_contexts)), columns=["Invocation Signature", "Observed Strings", "Enclosing Class", "Enclosing Method", "Tainting Base Arg/Return", "Access Path"])
    for i, context, strings in zip(intermediate_sources_df.index, tainting_invocation_contexts, contexts_strings):
        instr_report: InstrumentationReport
        instr_report, access_path = context

        # intermediate_sources_df.at[i, "Invocation Name"] = instr_report.invocation_java_signature
        intermediate_sources_df.at[i, "Invocation Signature"] = instr_report.invocation_java_signature
        
        intermediate_sources_df.at[i, "Observed Strings"] = strings

        intermediate_sources_df.at[i, "Enclosing Class"] = instr_report.enclosing_class_name
        intermediate_sources_df.at[i, "Enclosing Method"] = instr_report.enclosing_method_name
        intermediate_sources_df.at[i, "Invocation ID"] = instr_report.invoke_id

        intermediate_sources_df.at[i, "Tainting Base Arg/Return"] = _instr_report_position(instr_report)
            # TODO: pretty print as "func(this, a, *b*, c) -> d" or something
        
        intermediate_sources_df.at[i, "Access Path"] = access_path

    details += "\n"
    details += intermediate_sources_df.to_string()

    return details

def _instr_report_position(instr_report: InstrumentationReport):
    if instr_report.is_return_register:
        return "return"
    elif not instr_report.is_static and instr_report.invocation_argument_register_index == 0:
        return f"this"
    else:
        return f"register{instr_report.invocation_argument_register_index}"


def harnessed_source_calls_details(harnessed_source_calls: List[Tuple[int, str]]) -> str:
    details = ""
    details += f"\n\nObserved {len(harnessed_source_calls)} calls to harnessed sources:\n"
    details += "\n".join([f"Log line {i}, {line.strip()}" for i, line in harnessed_source_calls])

    return details

    
        # out_file.write(f"Instrumentation reports observing tainted strings {len(instrumentation_report_tuples)} times.\n")
        # out_file.write("\n".join([f"String '{observed_string}' \nobserved at access path {str(access_path)} \nby report {str(report)}" for report, access_path, observed_string in instrumentation_report_tuples]))
        # out_file.write(f"\n\nObserved {len(harnessed_source_calls)} calls to harnessed sources:\n")
        # out_file.write("\n".join([f"Log line {i}, {line.strip()}" for i, line in harnessed_source_calls]))

def observation_details():
    pass

