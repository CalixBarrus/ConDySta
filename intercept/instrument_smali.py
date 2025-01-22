from experiment.paths import StepInfoInterface
from intercept.instrument import SmaliInstrumentationStrategy, instrumentation_strategy_factory
from intercept.decoded_apk_model import DecodedApkModel


import pandas as pd


import shutil
from typing import List, Tuple

from util.input import ApkModel


class InstrumentSmali(StepInfoInterface):
    observations_column: str = "Observations Lists"
    strategies: List['SmaliInstrumentationStrategy']
    _concise_params: str
    def __init__(self, strategy_names: List[str]) -> None:
        self.strategies = []

        self._concise_params = ""
        for strategy_name in strategy_names:
            self.strategies.append(instrumentation_strategy_factory(strategy_name))

            if strategy_name is "HarnessSources":
                self._concise_params += "source-substitution"
            # TODO: fill out more of these cases



    @property
    def step_name(self) -> str:
        return "instrument"

    @property
    def version(self) -> Tuple[int]:
        return (0, 1, 0)

    @property
    def concise_params(self) -> List[str]:
        return self._concise_params

    def execute(self, input_df: pd.DataFrame, output_path_column: str=""):
        # Input: df with columns "Decompiled Path", ["{output_path}", "Observations Lists"]
        # Output: in-place on "Decompiled Path" or changes are made to copies at a path in the indicated column name.
        # observations columns should be provided if HarnessObservations is used as a strategy.


        smali_paths: pd.Series = pd.Series()
        if output_path_column == "":
            smali_path_column = "Decompiled Path"
        else:
            # copy smalis into new dirs
            for i in input_df.index:
                # dirs_exist_ok -> Overwrite files & directories if they are already there.
                shutil.copytree(input_df.loc[i, "Decompiled Path"], input_df.loc[i, output_path_column],
                        dirs_exist_ok=True)

            smali_path_column = output_path_column

        # handle observations_column optional parameter
        if not self.observations_column in input_df.columns:
            input_df.loc[self.observations_column] = None

        for i in smali_paths.index:

            smali_path = input_df.at[i, smali_path_column]
            context = input_df.at[i, self.observations_column]

            decoded_apk_model = DecodedApkModel(smali_path)
            decoded_apk_model.instrument(self.strategies, observation_context=context)
            return decoded_apk_model
        

# def instrument_batch(config: HybridAnalysisConfig, apks: List[ApkModel]):
def instrument_batch(decoded_apks_directory_path: str, instrumentation_strategy: List[SmaliInstrumentationStrategy], apks: List[ApkModel]):

    # Read in and parse decoded apks
    decoded_apk_models: List[DecodedApkModel] = []
    for apk in apks:
        decoded_apk_models.append(instrument_apk(decoded_apks_directory_path, instrumentation_strategy, apk))

    # We may later decide to save the decoded_apk_models for use in interpreting dynamic analysis results

# def instrument_apk(config: HybridAnalysisConfig, apk: ApkModel) -> 'DecodedApkModel':
def instrument_apk(decoded_apks_directory_path: str, instrumenters: List[SmaliInstrumentationStrategy], apk: ApkModel) -> 'DecodedApkModel':

    # TODO: in theory, this factory should get called after the start of the experiment, but outside of the business layer, so it can be transparent via experiment args how this is being constructed exactly.
    # instrumenters: List[SmaliInstrumentationStrategy] = [instrumentation_strategy_factory(instrumentation_strategy) for instrumentation_strategy in instrumentation_strategies]
    # decoded_apks_directory_path = config._decoded_apks_path

    decoded_apk_path = decoded_apk_path(decoded_apks_directory_path, apk)

    decoded_apk_model = DecodedApkModel(decoded_apk_path)
    decoded_apk_model.instrument(instrumenters)
    return decoded_apk_model