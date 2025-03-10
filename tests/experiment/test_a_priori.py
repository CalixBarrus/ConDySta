


import pytest
from experiment.a_priori import a_priori_string_info
from experiment.benchmark_name import BenchmarkName


@pytest.mark.parametrize("benchmark_name", 
    [
        (BenchmarkName.FOSSDROID),
        (BenchmarkName.GPBENCH),
    ],)
def test_a_priori_string_info_smoke(benchmark_name):
    # make sure df loads as is nonempty

    df = a_priori_string_info(benchmark_name)

    assert df.shape[0] > 0