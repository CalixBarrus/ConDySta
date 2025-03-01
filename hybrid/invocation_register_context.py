from functools import reduce
import pandas as pd
from hybrid.access_path import AccessPath
from intercept.InstrumentationReport import InstrumentationReport


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

    
