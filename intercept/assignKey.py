
import pexpect
import sys
import os

from intercept import intercept_config


def assign_key(config):
    print("Signing APKs...")

    key_path = config.key_path
    signed_apks_path = config.signed_apks_path
    rebuilt_apks_path = config.rebuilt_apks_path

    apk_name_list = []
    for apk_name in os.listdir(rebuilt_apks_path):
        apk_name = apk_name.strip()
        apk_name_list.append(apk_name)

    i = 1
    # for line in apkNameList:
    for apkName in os.listdir(rebuilt_apks_path):

        # If the apk is already signed, don't sign it again.
        if os.path.exists(os.path.join(signed_apks_path, apkName)):
            print("APK {} already signed, skipping.".format(apkName))
            continue

        # Make sure the apk being signed exists
        if os.path.isfile(os.path.join(rebuilt_apks_path, apkName)):
            apkKeyName = apkName + ".keystore"
            # cmd = "jarsigner -verbose -keystore {}{} -storepass 123456 -signedjar {}{} {}{} abc.keystore".format(keyPath, apkKeyName, signedApksPath, apkName, rebuiltApksPath, apkName)
            # In theory, this should be "zipalign"ed and verified before signing. It seems to work OK without that step though.
            cmd = "apksigner sign --ks {}{} --ks-pass pass:123456 --in {}{} --out {}{}".format(key_path, apkKeyName, rebuilt_apks_path, apkName, signed_apks_path, apkName)
            print(cmd)
            child = pexpect.spawn(cmd, logfile=sys.stdout, encoding='utf-8')

            #password
            try:
                result = child.expect([pexpect.EOF, 'password', pexpect.TIMEOUT])
                if result == 0:
                    # Expected result, do nothing.
                    pass
                elif result == 1:
                    # It might be asking for a password?
                    child.sendline('123456')
                    child.expect(pexpect.EOF)
                else:
                    raise NotImplementedError("Unexpected result from jarsigner")
            except Exception as e:
                print(str(child))
        else:
            print("Apk {} isn't recognized as a file?".format(os.path.join(rebuilt_apks_path, apkName)))


if __name__ == '__main__':
    configuration = intercept_config.get_default_intercept_config()

    assign_key(configuration)





