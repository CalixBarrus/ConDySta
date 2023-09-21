# import os
# from typing import List
#
# from util.input import InputApkModel
#
# def get_default_intercept_config():
#     # input_apks_path: str = "data/input-apks"
#     # input_apks: input.InputApksModel = input.input_apks_from_dir(input_apks_path)
#
#     config = HybridAnalysisConfig(
#         # input_apks=input_apks,
#                              decoded_apks_path="data/intercept/decoded-apks/",
#                              instrumentation_strategy="StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy",
#                              rebuilt_apks_path="data/intercept/rebuilt-apks/",
#                              keys_dir_path="data/intercept/apk-keys/",
#                              signed_apks_path="data/signed-apks/",
#                              logs_path="data/logs/",
#                              use_monkey=True,
#                              seconds_to_test_each_app=10,
#                              monkey_rng_seed=42,
#                              )
#     return config
#
#
# class HybridAnalysisConfig:
#     # input_apks: input.InputApksModel
#     decoded_apks_path: str
#     instrumentation_strategy: str
#     rebuilt_apks_path: str
#     keys_dir_path: str
#     signed_apks_path: str
#     logs_path: str
#     use_monkey: bool
#     seconds_to_test_each_app: int
#     monkey_rng_seed: int
#
#
#     def __init__(self,
#                  # input_apks: input.InputApksModel,
#                  decoded_apks_path: str,
#                  instrumentation_strategy: str,
#                  rebuilt_apks_path: str,
#                  keys_dir_path: str,
#                  signed_apks_path: str,
#                  logs_path: str,
#                  use_monkey: bool,
#                  seconds_to_test_each_app: int,
#                  monkey_rng_seed: int,
#                  ):
#
#         self.decoded_apks_path = decoded_apks_path
#         self.instrumentation_strategy = instrumentation_strategy
#         self.rebuilt_apks_path = rebuilt_apks_path
#         self.keys_dir_path = keys_dir_path
#         self.signed_apks_path = signed_apks_path
#         self.logs_path = logs_path
#
#         # If True, use monkey to send random commands to the app. If False,
#         # launch the app but do not send commands to it.
#         self.use_monkey = use_monkey
#         # About how many seconds monkey should run on a given app
#         self.seconds_to_test_each_app = seconds_to_test_each_app
#         self.monkey_rng_seed = monkey_rng_seed
#
# def decoded_apk_path(config: HybridAnalysisConfig, apk: InputApkModel):
#     return os.path.join(config.decoded_apks_path, apk.apk_name_no_suffix())
#
# def rebuilt_apk_path(config: HybridAnalysisConfig, apk: InputApkModel):
#     # Rebuilt apk keeps the ".apk" suffix
#     return os.path.join(config.rebuilt_apks_path, apk.apk_name)
#
# def apk_key_path(config: HybridAnalysisConfig, apk: InputApkModel):
#     return os.path.join(config.keys_dir_path, apk.apk_key_name())
#
# def signed_apk_path(config: HybridAnalysisConfig, apk: InputApkModel):
#     return os.path.join(config.signed_apks_path, apk.apk_name)
#
# def apk_logcat_dump_path(config: HybridAnalysisConfig, apk: InputApkModel):
#     pass
