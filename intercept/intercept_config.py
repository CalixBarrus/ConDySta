from typing import List

from util import input

def get_default_intercept_config():
    input_apks_path: str = "data/input-apks"
    input_apks: List[input.InputApkModel] = input.input_apks_from_dir(input_apks_path)

    config = InterceptConfig(input_apks=input_apks,
                             decoded_apks_path="data/intercept/decoded-apks/",
                             instrumentation_strategy="StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy",
                             rebuilt_apks_path="data/intercept/rebuilt-apks/",
                             key_path="data/intercept/apk-keys/",
                             signed_apks_path="data/signed-apks/",
                             logs_path="data/logs/",
                             use_monkey=True,
                             seconds_to_test_each_app=10,
                             monkey_rng_seed=42,
                             )
    return config


class InterceptConfig:
    input_apks: List[input.InputApkModel]
    decoded_apks_path: str
    instrumentation_strategy: str
    rebuilt_apks_path: str
    key_path: str
    signed_apks_path: str
    logs_path: str
    use_monkey: bool
    seconds_to_test_each_app: int
    monkey_rng_seed: int


    def __init__(self,
                 input_apks,
                 decoded_apks_path,
                 instrumentation_strategy,
                 rebuilt_apks_path,
                 key_path,
                 signed_apks_path,
                 logs_path,
                 use_monkey,
                 seconds_to_test_each_app,
                 monkey_rng_seed,
                 ):
        self.input_apks = input_apks
        self.decoded_apks_path = decoded_apks_path
        self.instrumentation_strategy = instrumentation_strategy
        self.rebuilt_apks_path = rebuilt_apks_path
        self.key_path = key_path
        self.signed_apks_path = signed_apks_path
        self.logs_path = logs_path

        # If True, use monkey to send random commands to the app. If False,
        # launch the app but do not send commands to it.
        self.use_monkey = use_monkey
        # About how many seconds monkey should run on a given app
        self.seconds_to_test_each_app = seconds_to_test_each_app
        self.monkey_rng_seed = monkey_rng_seed