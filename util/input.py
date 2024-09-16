import os
from typing import List, Union, Dict, Iterable, Tuple


class BatchInputModel:
    """
    Batch of input model. Maintains additional information about contents for easier batch processing.
    """
    _ungrouped_apks: List["ApkModel"]
    ungrouped_inputs: List["InputModel"]
    grouped_inputs: List["InputModel"]
    unique_apks: List["ApkModel"]

    def __init__(self, ungrouped_inputs: List["InputModel"], grouped_inputs: List["InputModel"]):
        self.ungrouped_inputs = ungrouped_inputs
        self.grouped_inputs = grouped_inputs
        self._validate_inputs()
        self.unique_apks = self._collect_unique_apks(ungrouped_inputs, grouped_inputs)

    def _validate_inputs(self):
        """ Check that ungrouped/grouped inputs have exactly 1 or more than 1 apk per group. """
        for ungrouped_input in self.ungrouped_inputs:
            if ungrouped_input.is_group():
                raise AssertionError("Unexpected grouped input")
        for grouped_input in self.grouped_inputs:
            if not grouped_input.is_group():
                raise AssertionError("Unexpected ungrouped input")

    def _collect_unique_apks(self, ungrouped_inputs: List["InputModel"], grouped_inputs: List["InputModel"]) -> List["ApkModel"]:
        unique_apks: List["ApkModel"] = []
        for ungrouped_input in ungrouped_inputs:
            apk: "ApkModel" = ungrouped_input.apk()
            if apk not in unique_apks:
                unique_apks.append(apk)

        for grouped_input in grouped_inputs:
            # TODO: update
            for apk in grouped_input.apks():
                if apk not in unique_apks:
                    unique_apks.append(apk)
        return unique_apks

    def all_input_models(self) -> List["InputModel"]:
        return self.ungrouped_inputs + self.grouped_inputs

class InputModel:
    """
    Model with experiment-specific information for a single experiment, specifically info on apk (or apks if a group)
    and source/sink list.

    Clients who don't care if input is group or not shouldn't have to. Model should be transparent enough for clients
    who do need to care. (This could be implemented with polymorphism, but at this time it would be overkill.)
    """

    _apks: List["ApkModel"]
    _next_input_id: int = 0
    input_id: int
    benchmark_id: int

    def __init__(self, apks: List["ApkModel"], benchmark_id: int=-1):
        if len(apks) < 1:
            raise AssertionError("Input list empty")

        self._apks = apks
        self.input_id = InputModel._next_input_id
        InputModel._next_input_id += 1

        self.benchmark_id = benchmark_id

    def input_identifier(self, grouped_apk_idx: int = -1) -> str:
        """ Short identifier string. Especially useful for grouped apks. If grouped_apk_idx specified, identifier is for a specific apk in a group """
        if not self.is_group():
            if grouped_apk_idx != -1:
                raise AssertionError()
            return str(self.benchmark_id) + "." + self.apk().apk_name

        else:
            if grouped_apk_idx == -1:
                return str(self.benchmark_id) + "." + "group_of_" + str(len(self._apks))
            else:
                return str(self.benchmark_id) + "." + "group_of_" + str(len(self._apks)) + self.apk(grouped_apk_idx).apk_name

    def is_group(self) -> bool:
        if len(self._apks) == 1:
            return False
        else:
            return True

    def apk(self, grouped_apk_idx: int = -1) -> "ApkModel":
        if grouped_apk_idx == -1:
            if self.is_group():
                raise AssertionError()
            return self._apks[0]
        else:
            return self._apks[grouped_apk_idx]

    def apks(self) -> Iterable[Tuple[int, "ApkModel"]]:
        """ Return list of tuples, grouped_apk_index and grouped_apk """
        if not self.is_group():
            raise AssertionError()

        return enumerate(self._apks)


class ApkModel:
    """
    Model with information for a single apk
    """

    apk_name: str
    apk_path: str
    apk_package_name: str

    def __init__(self, apk_path: str):
        self.apk_path = apk_path
        self.apk_name = os.path.basename(apk_path)

        if not os.path.isfile(self.apk_path) or not self.apk_path.endswith(".apk"):
            raise ValueError(f"The path {self.apk_path} isn't an apk.")
        
        self.apk_package_name = None

    def apk_name_no_suffix(self):
        # Drop the ".apk" on the end
        return self.apk_name[:-4]

    def apk_key_name(self):
        return self.apk_name + ".keystore"


def input_apks_from_dir(dir_path: str) -> 'BatchInputModel':
    """ Recursively traverse the target directory and it's children. Return all apks
    discovered as InputApksModel with no grouped_apks. """

    if dir_path == "":
        return None

    ungrouped_apks = _input_apks_from_dir_as_list(dir_path)
    ungrouped_inputs = [InputModel([apk_model]) for apk_model in ungrouped_apks]

    return BatchInputModel(ungrouped_inputs, [])


def find_apk_paths_in_dir_recursive(dir_path: str) -> List[str]:
    """ Recursively traverse the target directory and it's children. Return all apks
        discovered. """
    result = []

    for item in os.listdir(dir_path):
        new_path = os.path.join(dir_path, item)

        if new_path.endswith(".apk"):
            result.append(new_path)
        elif os.path.isdir(new_path):
            result += find_apk_paths_in_dir_recursive(new_path)
    return result
    

def _input_apks_from_dir_as_list(dir_path: str) -> List[ApkModel]:
    
    result = []
    for path in find_apk_paths_in_dir_recursive(dir_path):
        result.append(ApkModel(path))

    return result
    


def input_apks_from_list(list_path: str) -> 'BatchInputModel':
    """ list_path should be a txt file with each line containing a path to an apk. """

    if not os.path.isfile(list_path):
        raise AssertionError(f"Given path {list_path} is not a file.")

    result = []
    with open(list_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line != "":
                benchmarks_dir_prefix = "~/Documents/programming/benchmarks"
                line = os.path.join(benchmarks_dir_prefix, line)

                result.append(InputModel([ApkModel(line)]))

    return BatchInputModel(result, [])


def input_apks_from_dir_with_groups(dir_path: str, apk_groups_paths: List[List[str]],
                                    apk_ungrouped_paths: Union[List[str], None] = None) -> BatchInputModel:
    """
    Take all apks from directory indicated by dir_path into an InputApksModel. Apks
    whose paths are specified in apk_groups_paths will be grouped. Apks not specified
    will be ungrouped. Apks with their paths in apk_ungrouped_paths will be included
    in the ungrouped apks, even if they are also in one or more apk groups.
    """

    input_apks = _input_apks_from_dir_as_list(dir_path)
    if apk_ungrouped_paths is None:
        apk_ungrouped_paths = []

    return _input_apks_from_list_with_groups(input_apks, apk_groups_paths,
                                             apk_ungrouped_paths)


def input_apks_from_list_with_groups(list_path: str, groups_list_path: str, apk_ungrouped_paths: Union[List[str], None] = None) -> BatchInputModel:

    groups_lists: List[List[str]] = list_of_lists_from_file(groups_list_path)

    input_apks = input_apks_from_list(list_path).unique_apks
    if apk_ungrouped_paths is None:
        apk_ungrouped_paths = []

    return _input_apks_from_list_with_groups(input_apks, groups_lists,
                                             apk_ungrouped_paths)


def _input_apks_from_list_with_groups(apks_list: List[ApkModel], apk_groups_paths: List[List[
    str]], apk_ungrouped_paths: List[str]) -> BatchInputModel:
    """
    Turn the input apks_list into an BatchInputModel. Apks
    whose paths are specified in apk_groups_paths will be grouped. Apks not specified
    in apk_groups_paths
    will be ungrouped. Apks with their paths in apk_ungrouped_paths will also be
    included in the ungrouped apks, even if they are also in one or more apk groups.
    """

    # Verify and build apk_groups
    apk_path_dict: Dict[str, ApkModel] = {apk.apk_path: apk for apk in apks_list}
    remaining_apk_paths = [apk.apk_path for apk in apks_list]

    grouped_inputs = []
    for apk_group_paths in apk_groups_paths:
        apk_group_list = []
        for apk_path in apk_group_paths:

            # Get apk from input_apks with matching path
            if apk_path not in apk_path_dict.keys():
                raise ValueError(f"Provided apk_path {apk_path} not in provided "
                                 "apks_list.")
            apk_group_list.append(apk_path_dict[apk_path])

            # keep track of which apks haven't been put in groups
            if apk_path in remaining_apk_paths:
                remaining_apk_paths.remove(apk_path)

        grouped_inputs.append(InputModel(apk_group_list))

    # Put any apks in apks_list not included in apk_groups as ungrouped_apks
    ungrouped_apks: List[ApkModel] = [apk_path_dict[apk_path] for apk_path in remaining_apk_paths]

    # Add to ungrouped_apks any apks in apks_ungrouped_paths still not included
    for apk_path in apk_ungrouped_paths:
        if apk_path not in [apk.apk_path for apk in ungrouped_apks]:
            ungrouped_apks.append(apk_path_dict[apk_path])

    # Wrap ApkModels as ungrouped InputModels
    ungrouped_inputs = [InputModel([apk_model]) for apk_model in ungrouped_apks]

    return BatchInputModel(ungrouped_inputs, grouped_inputs)


def list_of_lists_from_file(file_path: str) -> List[List[str]]:
    """
    Read in the lines of a file into a list of strings.
    Sets of lines in the file separated by a line of whitespace will be grouped in
    separate, inner lists.
    """
    result = []
    with open(file_path, 'r') as file:
        inner_list = []
        for line in file.readlines():
            if line.strip() == "":
                if len(inner_list) > 0:
                    result.append(inner_list)
                    inner_list = []
            else:
                inner_list.append(line.strip())

    if len(inner_list) > 0:
        result.append(inner_list)
    return result
        


if __name__ == '__main__':
    pass
