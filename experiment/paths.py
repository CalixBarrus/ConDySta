from abc import ABC, abstractmethod
from typing import List, Tuple
from experiment.common import get_project_root_path
from util.input import InputModel


import pandas as pd


import os


class StepInfoInterface(ABC):
    # Hooks used by ResultPathManager
    @property
    @abstractmethod
    def step_name(self) -> str:
        raise NotImplementedError()
    @property
    @abstractmethod
    def version(self) -> Tuple[int, int, int]:
        raise NotImplementedError()
    @property
    @abstractmethod
    def concise_params(self) -> List[str]:
        # params that will be listed in file name; 
        raise NotImplementedError()


class ResultPathManager:
    base_path: str
    dataset_name: str
    date: str

    def __init__(self, dataset_name: str, exclusive_dir_path: str="", default_date_override: str = "") -> None:
        self.dataset_name = dataset_name

        # handle fallback cases
        if exclusive_dir_path == "":
            self.base_path = os.path.join(get_project_root_path(), "data", "experiment")
        else:
            # Input is expected to be some relative path from the project root
            self.base_path = os.path.join(get_project_root_path(), exclusive_dir_path)

        if default_date_override == "":
            # "YYYY-MM-DD"
            self.date = str(pd.to_datetime('today').date())
        elif default_date_override == None:
            # If user overrides the date with "None", then path omits the date.
            self.date = ""
        else:
            self.date = default_date_override

    # TODO: lexicographic sort w/ exceptions for version #
    # TODO: grab recent path matching selected subset of features (most recent version, most recent date, matching params)

    def get_result_path(self, step_info: StepInfoInterface, input_model: InputModel=None, keep: bool=True, reproduction: bool=False, extension: str="") -> str:
        # Scheme: project_root/[exclusive_pipeline_dir/][date]_stepname_dataset_version_params/id.apk_name.apk[.extension]

        # TODO: refactor ideas from setup_experiment_dir into this function
        # TODO: implement reproduction; if true, add r[n] to a list of params, where [n] is the next available int not in dir.

        # allow for an omitted date. Unpack version and concise_params
        date = [self.date] if self.date != "" else []
        version = [".".join([str(version_number) for version_number in step_info.version])]
        params = ["_".join(step_info.concise_params)]
        experiment_id = "_".join(date + [step_info.step_name] + [self.dataset_name] + version + params)

        if input_model is not None:
            enclosing_dir_path = os.path.join(self.base_path, experiment_id)
            file_name = f"{input_model.input_identifier()}" + extension
            result_path = os.path.join(enclosing_dir_path, file_name)
        else:
            # if input_model is omitted, then return a path [exclusive_pipeline_dir/]date_stepname_dataset_version_params[.extension]
            # use .txt as a default extension for this case
            if extension == "":
                extension = ".txt"

            result_path = os.path.join(self.base_path, experiment_id + extension)

        if not os.path.isdir(os.path.dirname(result_path)):
            # makedirs -> make multiple intermediate directories if necessary
            os.makedirs(os.path.dirname(result_path))

        # TODO: implement keep; if false, add to list of files that will get deleted when clean() is called

        return result_path

    def clean():
        # clean up files created during lifetime of this ResultPathManager who indicated keep=False.
        pass