import os

from intercept import intercept_config


def clean(config):
    decoded_apks_path = config.decoded_apks_path
    rebuilt_apks_path = config.rebuilt_apks_path
    key_path = config.key_path
    signed_apks_path = config.signed_apks_path
    logs_path = config.logs_path

    for folder in [rebuilt_apks_path, signed_apks_path]:
        cmd = f'rm {os.path.join(folder, "*.apk")}'
        print(cmd)
        os.system(cmd)
    
    cmd = f'rm {os.path.join(key_path, "*.keystore")}'
    print(cmd)
    os.system(cmd)

    cmd = f'rm {os.path.join(signed_apks_path, "*.idsig")}'
    print(cmd)
    os.system(cmd)

    cmd = f'rm {os.path.join(logs_path, "*.log")}'
    print(cmd)
    os.system(cmd)

    # For the smali code,
    # remove the whole directory and replace the root in order to avoid a
    # confirmation prompt.
    cmd = 'rm -rf {}'.format(decoded_apks_path)
    print(cmd)
    os.system(cmd)

    cmd = 'mkdir {}'.format(decoded_apks_path)
    print(cmd)
    os.system(cmd)

    # Todo: uninstall apks off connected device

def setup_folders(config):
    input_apks_path = config.input_apks_path
    decoded_apks_path = config.decoded_apks_path
    rebuilt_apks_path = config.rebuilt_apks_path
    key_path = config.key_path
    signed_apks_path = config.signed_apks_path
    logs_path = config.logs_path

    directory_list = [input_apks_path, decoded_apks_path, rebuilt_apks_path, key_path,
                      signed_apks_path, logs_path]
    for directory in directory_list:
        if not os.path.exists(directory):
            cmd = "mkdir {}".format(directory)
            print(cmd)
            os.system(cmd)

if __name__ == '__main__':
    configuration = intercept_config.get_default_intercept_config()

    clean(configuration)

    # setup_folders()