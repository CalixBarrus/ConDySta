def get_default_intercept_config():
    config = InterceptConfig(input_apks_path="input-apks/",
                             decoded_apks_path="intercept/decoded-apks/",
                             rebuilt_apks_path="intercept/rebuilt-apks/",
                             key_path="intercept/apk-keys/",
                             signed_apks_path="signed-apks/",
                             logs_path="logs/",
                             android_platform_path="/Users/calix/Library/Android/sdk/platforms/",
                             flowdroid_jar_path="/Users/calix/Documents/CodingProjects/research/soot-infoflow-cmd-jar-with-dependencies.jar",
                             verbose=True,
                             is_recursive_on_input_apks_path=False)
    return config


class InterceptConfig:
    def __init__(self, input_apks_path, decoded_apks_path, rebuilt_apks_path,
                 key_path, signed_apks_path, logs_path,
                 android_platform_path, flowdroid_jar_path, verbose, is_recursive_on_input_apks_path):
        self.input_apks_path = input_apks_path
        self.decoded_apks_path = decoded_apks_path
        self.rebuilt_apks_path = rebuilt_apks_path
        self.key_path = key_path
        self.signed_apks_path = signed_apks_path
        self.logs_path = logs_path
        self.android_platform_path = android_platform_path
        self.flowdroid_jar_path = flowdroid_jar_path
        self.verbose = verbose
        self.is_recursive_on_input_apks_path = is_recursive_on_input_apks_path

        self.use_monkey = True
        # About how many seconds monkey should run on a given app
        self.seconds_to_test_each_app = 5
        self.monkey_rng_seed = 42