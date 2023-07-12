import os
from typing import List


class InputApkModel:
    # TODO: this should be used more widely, and moved to a different file (somewhere
    #  in util?)
    apk_name: str
    apk_path: str

    def __init__(self, apk_path: str):
        self.apk_path = apk_path
        self.apk_name = apk_path.split("/")[-1]

        if not os.path.isfile(self.apk_path) or not self.apk_path.endswith(".apk"):
            raise ValueError(f"The path {self.apk_path} isn't an apk.")


def input_apks_from_dir(dir_path: str) -> List[InputApkModel]:
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

if __name__ == '__main__':
    # create list of flowdroid apps
    input_apks = input_apks_from_dir(
        "/Users/calix/Documents/programming/research-programming/benchmarks/ICCBench20")

    with open('data/input-apk-lists/ICCBench20-list.txt', 'w') as file:
        for input_apk in input_apks:
            file.write(input_apk.apk_path + "\n")


