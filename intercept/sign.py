from typing import List

import pexpect
import sys
import os

from experiment import external_path
from hybrid.hybrid_config import HybridAnalysisConfig, apk_path, apk_path, apk_key_path
from util.input import ApkModel

import util.logger
logger = util.logger.get_logger(__name__)

def assign_key_batch(signed_apks_directory_path: str, rebuilt_apks_directory_path: str, keys_directory_path: str, apks: List[ApkModel], clean: bool=False):
    for apk in apks:
        assign_key_single(signed_apks_directory_path, rebuilt_apks_directory_path, keys_directory_path, apk, clean=clean)

def assign_key_single(signed_apks_directory_path: str, rebuilt_apks_directory_path: str, keys_directory_path: str, apk: ApkModel, clean: bool):

    # If the apk is already signed, don't sign it again.
    if os.path.exists(apk_path(signed_apks_directory_path, apk)):
        if not clean:
            logger.debug(f"APK {apk.apk_name} already signed, skipping.")
            return
        else: 
            logger.debug(f"APK {apk.apk_name} already signed, deleting.")
            os.remove(apk_path(signed_apks_directory_path, apk))


    # Make sure the apk being signed exists
    if not os.path.exists(apk_path(rebuilt_apks_directory_path, apk)):
        logger.error(f"Rebuilt APK {apk.apk_name} is not found at {apk_path(rebuilt_apks_directory_path, apk)}")
        return

    # cmd = "jarsigner -verbose -keystore {}{} -storepass 123456 -signedjar {}{} {}{} abc.keystore".format(keyPath, apkKeyName, signedApksPath, apkName, rebuiltApksPath, apkName)
    # In theory, this should be "zipalign"ed and verified before signing. It seems to work OK without that step though.
    apksigner_path = "apksigner"
    # apksigner_path = external_path.apksigner_path



    cmd = [apksigner_path, "sign",
           "--ks", apk_key_path(keys_directory_path, apk),
           "--ks-pass", "pass:123456",
           "--in", apk_path(rebuilt_apks_directory_path, apk),
           "--out", apk_path(signed_apks_directory_path, apk)]
    logger.debug(" ".join(cmd))

    # Use the first line if you want to see the output of the signing process
    # child = pexpect.spawn(cmd, logfile=sys.stdout, encoding='utf-8')
    child = pexpect.spawn(" ".join(cmd), encoding='utf-8')

    # password
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
        logger.error(str(child))

if __name__ == '__main__':
    pass





