from functools import reduce
from textwrap import indent
import pandas as pd
from hybrid.access_path import AccessPath
from intercept.instrumentation_report import InstrumentationReport


from typing import List, Set, Tuple

from intercept.smali import SmaliMethodInvocation


InvocationRegisterContext = Tuple[InstrumentationReport, AccessPath]

def reduce_for_field_insensitivity(contexts: List[InvocationRegisterContext], string_sets: List[Set[str]] = []) -> Tuple[List[InvocationRegisterContext], List[Set[str]]]:
    # Combine contexts such that contexts that only differ by access path get merged, and all access paths get cut to depth 1

    if string_sets == []:
        string_sets = [set()] * len(contexts)
    
    def new_access_path(smali_type):
        # return AccessPath(f"[<{SmaliMethodInvocation.smali_type_to_java_type(report.invocation_argument_register_type)} .>]")
        return AccessPath(f"[<{SmaliMethodInvocation.smali_type_to_java_type(smali_type)} .>]")

    df = pd.DataFrame({"context": contexts, 
                       "report": map(lambda c: c[0], contexts), 
                       "path": map(lambda c: c[1], contexts), 
                       "string_set": string_sets})
    
    grouping_cols = ["enclosing_class_name", "enclosing_method_name", "invoke_id", "invocation_argument_register_index"]
    for col in grouping_cols:
        df[col] = df["report"].apply(lambda r: getattr(r, col))
    
    grouped_df = df.groupby(grouping_cols).first()

    grouped_df["string_set"] = df.groupby(grouping_cols)["string_set"].agg(lambda s: reduce(set.union, s))
    grouped_df["access_path"] = grouped_df["report"].apply(lambda r: new_access_path(r.invocation_argument_register_type))


    reduced_contexts = [(grouped_df.at[i, "report"], grouped_df.at[i, "access_path"]) for i in grouped_df.index]
    reduced_string_sets = [(grouped_df.at[i, "string_set"]) for i in grouped_df.index]

    return reduced_contexts, reduced_string_sets

    
def filter_access_paths_with_length_1(contexts: List[InvocationRegisterContext], string_sets: List[Set[str]] = []) -> Tuple[List[InvocationRegisterContext], List[Set[str]]]:
    # Cut out any observations with access path lengths greater than 1
    # This is meant to simulate a dynamic analysis that would only check base objects, instead of checking sub fields too

    # context: InvocationRegisterContext
    # len(context[1].fields)

    f = lambda i: len(contexts[i][1].fields) == 1
    filtered_indices = filter(f, range(len(contexts)))

    # TODO: deduplicate contexts/merge string_sets

    return [contexts[i] for i in filtered_indices], [string_sets[i] for i in filtered_indices]

