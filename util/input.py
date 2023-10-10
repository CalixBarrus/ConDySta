import os
from typing import List, Union, Dict


class InputApksModel:
    ungrouped_apks: List["InputApkModel"]
    input_apk_groups: List["InputApkGroup"]
    unique_apks: List["InputApkModel"]

    def __init__(self, ungrouped_apks: List["InputApkModel"], input_apk_groups: List["InputApkGroup"]):
        self.ungrouped_apks = ungrouped_apks
        self.input_apk_groups = input_apk_groups
        self.unique_apks = self._collect_unique_apks(ungrouped_apks, input_apk_groups)

    def _collect_unique_apks(self, input_apks: List["InputApkModel"], input_apk_groups: List["InputApkGroup"]) -> List["InputApkModel"]:
        unique_apks: List["InputApkModel"] = []
        for apk in input_apks:
            if apk not in unique_apks:
                unique_apks.append(apk)

        for group in input_apk_groups:
            for apk in group.apks:
                if apk not in unique_apks:
                    unique_apks.append(apk)
        return unique_apks

class InputApkGroup:
    apks: List["InputApkModel"]
    _group_counter: int = 0
    group_id: int

    def __init__(self, apks):
        self.apks = apks
        self.group_id = InputApkGroup._group_counter
        InputApkGroup._group_counter += 1

class InputApkModel:
    apk_name: str
    apk_path: str
    def __init__(self, apk_path: str):
        self.apk_path = apk_path
        self.apk_name = apk_path.split("/")[-1]

        if not os.path.isfile(self.apk_path) or not self.apk_path.endswith(".apk"):
            raise ValueError(f"The path {self.apk_path} isn't an apk.")

    def apk_name_no_suffix(self):
        # Drop the ".apk" on the end
        return self.apk_name[:-4]

    def apk_key_name(self):
        return self.apk_name + ".keystore"

def input_apks_from_dir(dir_path: str) -> 'InputApksModel':
    """ Recursively traverse the target directory and it's children. Return all apks
    discovered as InputApksModel with no grouped_apks. """
    return InputApksModel(_input_apks_from_dir_as_list(dir_path), [])

def _input_apks_from_dir_as_list(dir_path: str) -> List[InputApkModel]:
    """ Recursively traverse the target directory and it's children. Return all apks
        discovered. """

    result = []

    for item in os.listdir(dir_path):
        new_path = os.path.join(dir_path, item)

        if new_path.endswith(".apk"):
            result.append(InputApkModel(new_path))
        elif os.path.isdir(new_path):
            result += _input_apks_from_dir_as_list(new_path)
    return result

def input_apks_from_list(list_path: str) -> 'InputApksModel':
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

                result.append(InputApkModel(line))

    return InputApksModel(result, [])

def input_apks_from_dir_with_groups(dir_path: str, apk_groups_paths: List[List[str]],
                                    apk_ungrouped_paths: Union[List[str],None]=None) -> InputApksModel:
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


def input_apks_from_list_with_groups(list_path: str, apk_groups_paths: List[List[
    str]], apk_ungrouped_paths: Union[List[str],None]=None) -> InputApksModel:

    input_apks = input_apks_from_list(list_path).ungrouped_apks
    if apk_ungrouped_paths is None:
        apk_ungrouped_paths = []

    return _input_apks_from_list_with_groups(input_apks, apk_groups_paths,
                                       apk_ungrouped_paths)


def _input_apks_from_list_with_groups(apks_list: List[InputApkModel], apk_groups_paths: List[List[
    str]], apk_ungrouped_paths: List[str]) -> InputApksModel:
    """
    Turn the input apks_list into an InputApksModel. Apks
    whose paths are specified in apk_groups_paths will be grouped. Apks not specified
    in apk_groups_paths
    will be ungrouped. Apks with their paths in apk_ungrouped_paths will also be
    included in the ungrouped apks, even if they are also in one or more apk groups.
    """

    # Verify and build apk_groups
    apk_path_dict: Dict[str, InputApkModel] = {apk.apk_path:apk for apk in apks_list}
    remaining_apk_paths = [apk.apk_path for apk in apks_list]

    apk_groups = []
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

        apk_groups.append(InputApkGroup(apk_group_list))

    # Put any apks in apks_list not included in apk_groups as ungrouped_apks
    ungrouped_apks: List[InputApkModel] = [apk_path_dict[apk_path] for apk_path in remaining_apk_paths]

    # Add to ungrouped_apks any apks in apks_ungrouped_paths still not included
    for apk_path in apk_ungrouped_paths:
        if apk_path not in [apk.apk_path for apk in ungrouped_apks]:
            ungrouped_apks.append(apk_path_dict[apk_path])

    return InputApksModel(ungrouped_apks, apk_groups)

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


