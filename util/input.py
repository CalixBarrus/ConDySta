import os
from typing import List, Union


class InputApksModel:
    input_apks: Union[List["InputApkModel"], None]  # Should this be renamed "ungrouped_apks"? would need to allow apks in both fields if so
    input_apk_groups: Union[List[List["InputApkModel"]], None]

    def __init__(self, input_apks, input_apk_groups):
        self.input_apks = input_apks
        self.grouped_apks_lists = input_apk_groups

        if input_apks is None:
            if input_apk_groups is None:
                raise AssertionError("Either input_apks or input_apk_groups must not be None")
        else:
            if input_apk_groups is not None:
                raise AssertionError("One of input_apks or input_apk_groups must be None")

class InputApkModel:
    apk_name: str
    apk_path: str
    def __init__(self, apk_path: str):
        self.apk_path = apk_path
        self.apk_name = apk_path.split("/")[-1]

        if not os.path.isfile(self.apk_path) or not self.apk_path.endswith(".apk"):
            raise ValueError(f"The path {self.apk_path} isn't an apk.")

def input_apks_from_dir(dir_path: str) -> 'InputApksModel':
    """ Recursively traverse the target directory and it's children. Return all apks
    discovered as InputApksModel with no grouped_apks. """
    return InputApksModel(_input_apks_from_dir_as_list(dir_path), None)

def _input_apks_from_dir_as_list(dir_path: str) -> List[InputApkModel]:
    """ Recursively traverse the target directory and it's children. Return all apks
        discovered. """

    result = []

    for item in os.listdir(dir_path):
        new_path = os.path.join(dir_path, item)

        if new_path.endswith(".apk"):
            result.append(InputApkModel(new_path))
        elif os.path.isdir(new_path):
            result += input_apks_from_dir(new_path)
    return result

def input_apks_from_list(list_path: str) -> List[InputApkModel]:
    """ list_path should be a txt file with each line containing a path to an apk. """

    if not os.path.isfile(list_path):
        raise AssertionError(f"Given path {list_path} is not a file.")

    result = []
    with open(list_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line != "":
                result.append(InputApkModel(line))

    return result

def input_apks_from_dir_with_groups(dir_path: str, apk_groups_paths: List[List[str]]) -> InputApksModel:

    input_apks = _input_apks_from_dir_as_list(dir_path)

    # Verify and build apk_groups
    apk_groups = []
    for apk_group_paths in apk_groups_paths:
        apk_group = []
        for apk_path in apk_group_paths:

            # Get apk from input_apks with matching path
            for input_apk in input_apks:
                if apk_path == input_apk.apk_path:
                    apk_group.append(input_apk)
                    input_apks.remove(input_apk)
                    break # Get out of list because we modified the container in which we are iterating

        apk_groups.append(apk_group)

    # Put any remaining input apks into apk_groups as singletons.
    apk_groups += [[input_apk] for input_apk in input_apks]

    return InputApksModel(None, apk_groups)



if __name__ == '__main__':
    # create list of flowdroid apps
    input_apks = input_apks_from_dir(
        "/Users/calix/Documents/programming/research-programming/benchmarks/DroidBenchExtended")

    with open('data/input-apk-lists/DroidBenchExtended-apk-name-list.csv', 'w') as file:
        for input_apk in input_apks:
            # input_apk.

            file.write(input_apk.apk_name + "\n")


