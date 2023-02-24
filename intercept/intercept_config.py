
def get_default_intercept_config():
    config = InterceptConfig(input_apks_path="../input-apks/",
                             decoded_apks_path="decoded-apks/",
                             rebuilt_apks_path="rebuilt-apks/",
                             key_path="apk-keys/",
                             signed_apks_path="signed-apks/",
                             logs_path="../logs/")
    return config


class InterceptConfig:
    def __init__(self, input_apks_path, decoded_apks_path, rebuilt_apks_path,
                 key_path, signed_apks_path, logs_path):
        self.input_apks_path = input_apks_path
        self.decoded_apks_path = decoded_apks_path
        self.rebuilt_apks_path = rebuilt_apks_path
        self.key_path = key_path
        self.signed_apks_path = signed_apks_path
        self.logs_path = logs_path
