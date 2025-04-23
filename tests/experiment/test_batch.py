


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


def test_output_multiple_columns(test_data_df: pd.DataFrame):
    def test_function(a, b, c):
        return a + b + c, 2*(a+b+c)

    batch_function = process_as_dataframe(test_function, [True, False, True], [])

    batch_function("A", 2, "C", input_df=test_data_df, output_col=["output", "2x Output"])

    # print(test_data_df.to_string())

    assert test_data_df["output"].tolist() == [6, 8, 10, 9]
    assert test_data_df["2x Output"].tolist() == [12, 16, 20, 18]


def test_multiindex_practice():
    # Create a sample DataFrame with a MultiIndex
    arrays = [
        ['A', 'A', 'B', 'B'],
        ['one', 'two', 'one', 'two']
    ]
    index = pd.MultiIndex.from_arrays(arrays, names=('first', 'second'))
    # df = pd.DataFrame({'value': [1, 2, 3, 4]}, index=index)

    df1 = pd.DataFrame({'value': [7, 8]}, index=[0, 1])
    df2 = pd.DataFrame({'other': [9, 10]}, index=[0, 1])
    df3 = pd.DataFrame({'value': [11, 12]}, index=[1, 4])

    df = pd.concat([df1, df2, df3], axis=0)

    test_series = pd.Series([df1, df2, df3], index=[0, 1, 3])

    print(test_series)
    # print(test_series.shape)
    # print(test_series.index)

    # change test_series to multiindex df
    arrays = [
        ['A', 'A', 'B', 'B'],
        ['one', 'two', 'one', 'two']
    ]
    benchmark_exploded_index = []
    flows_indices = []
    for benchmark_id in test_series.index:

        benchmark_exploded_index = benchmark_exploded_index + [benchmark_id]*len(test_series[benchmark_id].index)
        flows_indices = flows_indices + list(test_series[benchmark_id].index)

    multiindex = pd.MultiIndex.from_arrays([benchmark_exploded_index, flows_indices], names=('benchmark_id', 'flow_id'))
    print(multiindex)

    combined_df = pd.concat(test_series.values, axis=0)
    print(combined_df)
    combined_df.index = multiindex
    print(combined_df)

    # print(pd.concat([df1, df2, df3], axis=1))
    # print(df.index)
    # print(df.columns)

    # # Print the original DataFrame
    # print("Original DataFrame:")
    # print(df)

    # # Reset the index to flatten the MultiIndex
    # df_reset = df.reset_index()

    # # Print the DataFrame after resetting the index
    # print("\nDataFrame after resetting index:")
    # print(df_reset)