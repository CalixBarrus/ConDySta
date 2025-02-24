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
    # args_as_columns_mask: Dimension should match the dimension of the args passed to on_single.
    # If true, that arg is the name of a column in the dataframe. If false, that arg is a constant across rows.
    # kwargs_as_columns_mask: works the same

    # Row will be skipped if LAST_ERROR_COLUMN is not empty.
    # ExperementStepException will be caught with errors stored in LAST_ERROR_COLUMN.

    # Get the signature of the on_single function
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

        # TODO: ideally the "single" steps should throw a custom type of error that will get caught and handled by the batch code.
        if LAST_ERROR_COLUMN not in input_df.columns:
            input_df[LAST_ERROR_COLUMN] = ""    

        if output_col != "":
            if not output_col in input_df.columns:
                input_df[output_col] = "" # or some other null value? 
            else:
                result_series = pd.Series(index=input_df.index)

        for i in input_df[input_df[LAST_ERROR_COLUMN] == ""].index: # Filter out rows with errors.
            try:
                # Extract the arguments for the current row
                # row_args = [arg if is_column == False else input_df.at[i, arg] for arg, is_column in zip(bound_args.args, args_as_columns_mask)]
                row_kwargs = {kwarg_key: input_df.at[i, kwarg_value] if is_col_name else kwarg_value for kwarg_key, kwarg_value, is_col_name in zip(bound_args.arguments.keys(), bound_args.arguments.values(), args_as_columns_mask + kwargs_as_columns_mask)}
                # result = on_single(*row_args, **row_kwargs)
                result = on_single(**row_kwargs)
                if output_col != "":
                    input_df.at[i, output_col] = result
                else:
                    result_series.at[i] = result

            except ExperimentStepException as e:
                input_df.at[i, LAST_ERROR_COLUMN] = e.__str__()
                logger.error(e)

        if output_col != "":
            return None
        else:
            return result_series

    return as_batch


