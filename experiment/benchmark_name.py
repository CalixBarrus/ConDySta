
from enum import Enum


class BenchmarkName(Enum):
    GPBENCH = "gpbench"
    FOSSDROID = "fossdroid"


def lookup_benchmark_name(path: str) -> BenchmarkName:
    # Guess at the benchmark name given a path

    names_in_path = [name for name in BenchmarkName.__members__.values() if name.value in path]

    if len(names_in_path) == 0:
        raise ValueError(f"Cannot find benchmark name in path {path}")
    if len(names_in_path) == 1:
        return names_in_path[0]
    else:
        raise ValueError(f"Found multiple benchmark names in path {path}")
    
