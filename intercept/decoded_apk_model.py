from intercept.InstrumentationReport import InstrumentationReport
from intercept.instrument import HarnessObservations, SmaliInstrumentationStrategy
from intercept.smali import SmaliFile


import os
import shutil
from typing import List, Tuple


class DecodedApkModel:
    """
    Representation of a decoded apk's files for the purposes of instrumentation
    """
    apk_root_path: str
    project_smali_directory_paths: List[str]
    smali_directories: List[List['SmaliFile']] # TODO: this doesn't need to be a list of lists, this could just be a list of SmaliFiles (as long as the directory's are being kept track of separate)
    # is_instrumented: bool TODO: this is a good idea, but right now DecodedApkModels are constructed when they are needed and then deleted; this kind of state wouldn't get cached anywhwere

    def __init__(self, decoded_apk_root_path: str):
        """
        Parse all the smali directories and files for later instrumentation.
        :param decoded_apk_root_path: Path to the root directory of a single apk
        decoded by apktool.
        """
        if not os.path.isdir(decoded_apk_root_path):
            raise AssertionError(f"Path {decoded_apk_root_path} expected to be directory")

        self.apk_root_path = decoded_apk_root_path

        # self.project_smali_directory_names = []
        # for item in os.listdir(self.apk_root_path):
        #     if (os.path.isdir(os.path.join(self.apk_root_path, item)) and
        #             item.startswith("smali")):
        #         assert (item == "smali"
        #                 or item.startswith("smali_classes")
        #                 or item.startswith("smali_assets"))
        #         self.project_smali_directory_names.append(item)

        # # Sort the folder names so indexing into the list is consistent with
        # # the file names.
        # self.project_smali_directory_names.sort()
        # assert self.project_smali_directory_names[0] == "smali"

        # # Go through each folder smali_classes folder and parse all the smali
        # # files.
        # project_smali_directory_paths = map(os.path.join,
        #                                     [decoded_apk_root_path] * len(
        #                                         self.project_smali_directory_names),
        #                                     self.project_smali_directory_names)

        self.project_smali_directory_paths = DecodedApkModel.get_project_smali_directory_paths(self.apk_root_path)

        self.smali_directories: List[List[SmaliFile]] = []
        for smali_dir_path in self.project_smali_directory_paths:
            smali_paths = DecodedApkModel.scan_for_smali_file_paths(smali_dir_path)
            # self.smali_directories.append(
            #     self.scan_for_smali_files(path, ""))
            self.smali_directories.append([SmaliFile(smali_file_path) for smali_file_path in smali_paths])

        # self.is_instrumented = False

    @staticmethod
    def get_project_smali_directory_paths(decoded_apk_root_path: str) -> List[str]:
        project_smali_directory_names = []
        for item in os.listdir(decoded_apk_root_path):
            if (os.path.isdir(os.path.join(decoded_apk_root_path, item)) and
                    item.startswith("smali")):
                assert (item == "smali"
                        or item.startswith("smali_classes")
                        or item.startswith("smali_assets"))
                project_smali_directory_names.append(item)

        # Sort the folder names so indexing into the list is consistent with
        # the file names.
        project_smali_directory_names.sort()
        assert project_smali_directory_names[0] == "smali"

        project_smali_directory_paths = list(map(os.path.join,
                                            [decoded_apk_root_path] * len(
                                                project_smali_directory_names),
                                            project_smali_directory_names))

        return project_smali_directory_paths


    @staticmethod
    def scan_for_smali_file_paths(project_smali_folder_path: str, _class_path: str="") -> List[str]:
        """
        Recursively traverse the subdirectories of
        project_smali_folder_path, getting the methods in each smali file.
        :param project_smali_folder_path: path to the "smali" or
        "smali_classes[n]" directory.
        :param _class_path: relative path referring to the subdirectories
        traversed so far, used for recursion.
        :return: List of SmaliFile objects containing data about each file in the apk
        """

        assert os.path.basename(project_smali_folder_path).startswith("smali")

        result_smali_file_paths: List[str] = []
        # result_smali_files: List[SmaliFile] = []
        for item in os.listdir(os.path.join(project_smali_folder_path,
                                            _class_path)):
            item_path = os.path.join(project_smali_folder_path, _class_path,
                                     item)
            if os.path.isdir(item_path):
                result_smali_file_paths += DecodedApkModel.scan_for_smali_file_paths(
                    project_smali_folder_path,
                    os.path.join(_class_path, item))

            elif item.endswith(".smali"):
                # result_smali_files.append(SmaliFile(
                #     project_smali_folder_path, _class_path, item))
                result_smali_file_paths.append(os.path.join(project_smali_folder_path, _class_path, item))

        return result_smali_file_paths

    def instrument(self, instrumenters: List[SmaliInstrumentationStrategy], observation_context: List[Tuple[InstrumentationReport, str, str]]=None):
        for instrumenter in instrumenters:
            if instrumenter.needs_to_insert_directory():
                self.insert_smali_directory(instrumenter.path_to_directory())

        insertions_count = [0] * len(instrumenters)
        for smali_directory in self.smali_directories:
            for smali_file in smali_directory:

                # Apply each instrumentation strategy
                insertions = []
                for index, instrumenter in enumerate(instrumenters):

                    if isinstance(instrumenter, HarnessObservations):
                        new_insertions = instrumenter.instrument_file(smali_file, observation_context)
                    else:
                        new_insertions = instrumenter.instrument_file(smali_file)

                    insertions_count[index] += len(new_insertions)
                    insertions += new_insertions


                smali_file.insert_code(insertions)

        # start debug
        # logger.debug(f"Instrumenters performed {",".join([str(count) for count in insertions_count])} code insertions, respectively on apk {os.path.basename(self.apk_root_path)}")
        # end debug

        self.is_instrumented = True

    def insert_smali_directory(self, smali_source_directory_path: str):
        # TODO this could get called twice for two different instrumentation strategies

        if not os.path.isdir(smali_source_directory_path):
            raise ValueError(
                "Directory " + smali_source_directory_path + " does not exist.")

        # Use the last directory; it hopefully has the fewest methods, so we don't put too many methods into the same smali directory
        destination_directory_path = self.project_smali_directory_paths[-1]
        if not os.path.isdir(destination_directory_path):
            raise ValueError(
                "Directory " + destination_directory_path + " does not exist.")

        shutil.copytree(smali_source_directory_path, destination_directory_path,
                        dirs_exist_ok=True)