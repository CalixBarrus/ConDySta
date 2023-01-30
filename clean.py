import os

def main():
    for folder in [rebuilt_apks_path, signed_apks_path]:
        cmd = 'rm {}*.apk'.format(folder)
        print(cmd)
        os.system(cmd)
    
    cmd = 'rm {}*.keystore'.format(key_path)
    print(cmd)
    os.system(cmd)

    # Remove the whole directory and replace the root in order to avoid a
    # confirmation prompt.
    cmd = 'rm.rf {}'.format('smalis')
    print(cmd)
    os.system(cmd)

    cmd = 'mkdir {}'.format('smalis')
    print(cmd)
    os.system(cmd)

    # Todo: uninstall apks off connected device

def setup_folders():
    directory_list = [input_apks_path, decoded_apks_path, rebuilt_apks_path, key_path,
                      signed_apks_path]
    for directory in directory_list:
        if not os.path.exists(directory):
            cmd = "mkdir {}".format(directory)
            print(cmd)
            os.system(cmd)

if __name__ == '__main__':
    # All these paths should end with '/'
    input_apks_path = "input-apks/"
    decoded_apks_path = 'decoded-apks/'
    rebuilt_apks_path = 'rebuilt-apks/'
    key_path = "apk-keys/"
    signed_apks_path = 'signed-apks/'

    main()
    # setup_folders()