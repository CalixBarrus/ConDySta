


import pandas as pd
import pytest
from experiment.batch import process_as_dataframe


# def test_function():
#     return test_function

@pytest.fixture
def test_data_df():
    # return [[1,2], [3,4]]
    return pd.DataFrame({"A": [1,2,3,4], "C": [3,4,5,3]})

def test_process_as_dataframe(test_data_df):

    def test_function(a, b, c):
        return a + b + c

    batch_function = process_as_dataframe(test_function, [True, False, True], [])

    batch_function("A", 2, "C", input_df=test_data_df, output_col="output")

    assert test_data_df["output"].tolist() == [6, 8, 10, 9]


def test_process_as_dataframe_with_kwarg(test_data_df):

    def test_function_with_kwarg(a, b, c = 0):
        return a + b + c
    
    batch_function2 = process_as_dataframe(test_function_with_kwarg, [True, False], [True])

    # batch_function("A", 2, "C", test_data_df, output_col="output")

    batch_function2("A", 4, c = "C", input_df = test_data_df, output_col = "output2")

    assert test_data_df["output2"].tolist() == [8, 10, 12, 11]