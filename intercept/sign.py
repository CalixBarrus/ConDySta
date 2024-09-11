from typing import List

import pexpect
import sys
import os

from hybrid.hybrid_config import HybridAnalysisConfig, signed_apk_path, rebuilt_apk_path, apk_key_path
from util.input import ApkModel

import util.logger
logger = util.logger.get_logger(__name__)

def assign_key_batch(config: HybridAnalysisConfig, apks: List[ApkModel]):
    for apk in apks:
        assign_key_single(config, apk)

def assign_key_single(config: HybridAnalysisConfig, apk: ApkModel):
    # If the apk is already signed, don't sign it again.
    if os.path.exists(signed_apk_path(config, apk)):
        logger.debug(f"APK {apk.apk_name} already signed, skipping.")
        return

    # Make sure the apk being signed exists
    if not os.path.exists(rebuilt_apk_path(config, apk)):
        logger.error(f"Rebuilt APK {apk.apk_name} is not found at {rebuilt_apk_path(config, apk)}")
        return

    # cmd = "jarsigner -verbose -keystore {}{} -storepass 123456 -signedjar {}{} {}{} abc.keystore".format(keyPath, apkKeyName, signedApksPath, apkName, rebuiltApksPath, apkName)
    # In theory, this should be "zipalign"ed and verified before signing. It seems to work OK without that step though.
    cmd = ["apksigner", "sign",
           "--ks", apk_key_path(config, apk),
           "--ks-pass", "pass:123456",
           "--in", rebuilt_apk_path(config, apk),
           "--out", signed_apk_path(config, apk)]
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





