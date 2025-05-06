import inspect
from typing import Callable, List

import pandas as pd

import util.logger
logger = util.logger.get_logger(__name__)

class ExperimentStepException(Exception):
    # TODO: add field for the step name?
    pass

LAST_ERROR_COLUMN = "last_error"

def process_as_dataframe(on_single: Callable, args_as_columns_mask: List[bool], kwargs_as_columns_mask: List[bool]) -> Callable:
    # Returns a modified version of input function "on_single" with two additional kwargs, "input_df" and "output_col".
    # The resulting function calls "on_single" on each row of input_df, where arguments to the batch function are either 
    # passed to on_single or reference columns whose entries will be passed to on_single. 
    # The results of "on_single" will be stored in the column indicated by "output_col"; if output_col is not specified, the output will be returned as a series.

    # args_as_columns_mask: Dimension should match the dimension of the args passed to on_single.
    # If true, that arg is the name of a column in the dataframe. If false, that arg is a constant across rows.
    # kwargs_as_columns_mask: works the same

    # Row will be skipped if LAST_ERROR_COLUMN is not empty.
    # ExperimentStepException will be caught with errors stored in LAST_ERROR_COLUMN.

    # TODO: setup so output_col can take list, in order to sort multiple outputs into multiple columns :3


    on_single_signature = inspect.signature(on_single)
    assert len(args_as_columns_mask) + len(kwargs_as_columns_mask) == len(on_single_signature.parameters), f"args_as_columns_mask {args_as_columns_mask} does not match the number of parameters in on_single {on_single_signature.parameters}"

    # Define the new keyword arguments
    additional_params = [ 
        # Choice of input_df as POSITIONAL_OR_KEYWORD Forces the split between args and kwargs (if present) to either be between input_df and input_col or the original function's args/kwargs.
        inspect.Parameter('input_df', inspect.Parameter.POSITIONAL_OR_KEYWORD, default=""),
        inspect.Parameter('output_col', inspect.Parameter.KEYWORD_ONLY, default=""),
    ]

    # Combine the parameters of on_single with the new keyword arguments
    new_params = list(on_single_signature.parameters.values()) + additional_params

    # Create a new signature for the as_batch function
    as_batch_signature = on_single_signature.replace(parameters=new_params)
    test_signature = inspect.Signature(parameters=new_params)
    # Define the as_batch function with the new signature
    def as_batch(*args, **kwargs):
        bound_args = as_batch_signature.bind(*args, **kwargs)
        bound_args.apply_defaults()

        input_df: pd.DataFrame = bound_args.arguments['input_df']
        output_col = bound_args.arguments['output_col']

        # Check that the required column identifiers are in the dataframe
        # args_as_columns = [arg in input_df.columns for arg, is_column in zip(bound_args.args, args_as_columns_mask) if is_column]
        # assert all(args_as_columns), f"Not all args {args_as_columns} are in the dataframe columns {input_df.columns}"
        # kwargs_as_columns = [kwarg_value in input_df.columns for kwarg_value, is_column in zip(bound_args.kwargs, kwargs_as_columns_mask) if is_column]
        # assert all(kwargs_as_columns), f"Not all kwargs {kwargs_as_columns} are in the dataframe columns {input_df.columns}"
        arguments_as_columns = [arg in input_df.columns for arg, is_column in zip(bound_args.arguments.values(), args_as_columns_mask + kwargs_as_columns_mask) if is_column]
        assert all(arguments_as_columns), f"Not all args {arguments_as_columns} are in the dataframe columns {input_df.columns}"
        # args_as_columns = [arg in input_df.columns for arg, is_column in zip(bound_args.args, args_as_columns_mask) if is_column]
        # same for kwargs

        is_tuple_output = isinstance(output_col, list)


        if output_col != "":
            # add output columns if necessary
            if is_tuple_output:
                for col in output_col:
                    if not col in input_df.columns:
                        input_df[col] = "" 
            elif not output_col in input_df.columns:
                input_df[output_col] = "" # or some other null value? 
        else:
            result_series = pd.Series(index=input_df.index)

        # ExperimentStepExceptions require use of LAST_ERROR_COLUMN
        if LAST_ERROR_COLUMN not in input_df.columns:
            input_df[LAST_ERROR_COLUMN] = ""    


        for i in input_df[input_df[LAST_ERROR_COLUMN] == ""].index: # Filter out rows with errors.
            try:
                # Extract the arguments for the current row
                # row_args = [arg if is_column == False else input_df.at[i, arg] for arg, is_column in zip(bound_args.args, args_as_columns_mask)]
                row_kwargs = {kwarg_key: input_df.at[i, kwarg_value] if is_col_name else kwarg_value for kwarg_key, kwarg_value, is_col_name in zip(bound_args.arguments.keys(), bound_args.arguments.values(), args_as_columns_mask + kwargs_as_columns_mask)}
                # result = on_single(*row_args, **row_kwargs)
                result = on_single(**row_kwargs)
                if not is_tuple_output:
                    if output_col != "":
                        input_df.at[i, output_col] = result
                    else:
                        result_series.at[i] = result
                else: 
                    # TODO check that result is tuple of scalars; if there is a list in there, loc might break
                    if output_col != "":
                        for single_col, single_result in zip(output_col, result):
                            input_df.at[i, single_col] = single_result
                    else:
                        # Save the raw tuple as each entry in the series
                        result_series.at[i] = result

            except ExperimentStepException as e:
                input_df.at[i, LAST_ERROR_COLUMN] = e.__str__()
                logger.error(e)

        if output_col != "":
            return None
        else:
            return result_series

    return as_batch


def series_of_dataframe_to_multiindexed_dataframe(series: pd.Series, multi_index_names: List=["benchmark_id", "flow_id"]) -> pd.DataFrame:
    # Convert a series of dataframes to a multiindexed dataframe
    # uses the index of the series as the first level of the multiindex

    outer_exploded_index = []
    inner_indices = []
    for outer_index in series.index:

        outer_exploded_index = outer_exploded_index + [outer_index]*len(series[outer_index].index)
        inner_indices = inner_indices + list(series[outer_index].index)

    assert len(multi_index_names) == 2
    multiindex = pd.MultiIndex.from_arrays([outer_exploded_index, inner_indices], names=multi_index_names)

    combined_df = pd.concat(series.values, axis=0)
    combined_df.index = multiindex
    
    return combined_df