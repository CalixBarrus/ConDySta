from typing import List

import pexpect
import sys
import os

from hybrid.hybrid_config import HybridAnalysisConfig, apk_key_path
from util import logger
from util.input import InputApkModel

logger = logger.get_logger('intercept', 'keygen')

def generate_keys_batch(config: HybridAnalysisConfig, apks: List[InputApkModel]):
    for apk in apks:
        generate_keys_single(config, apk)

def generate_keys_single(config: HybridAnalysisConfig, apk: InputApkModel):
    if apk.apk_key_name() in os.listdir(config.keys_dir_path):
        logger.debug(f"APK keystore {apk.apk_key_name()} already exists, skipping.")
        return

    cmd = "keytool -genkey -alias abc.keystore -keyalg RSA -validity 20000 -keystore {}".format(apk_key_path(config, apk))
    logger.debug(cmd)

    # Todo: should some of this logic be in util.subprocess? It's fairly business logic specific, so it may be ok leaving it here
    # set encoding to utf-8 or stdout will whine about getting bytes, instead of strings
    # Use the first line if you want to see the output of the signing process
    # child = pexpect.spawn(cmd, logfile=sys.stdout, encoding='utf-8')
    child = pexpect.spawn(cmd, encoding='utf-8')

    # password
    try:
        if (child.expect('password') == 0):  # Enter keystore password:
            child.sendline('123456')
    except Exception as e:
        logger.error(str(child))

    # re-enter password
    try:
        if (child.expect([pexpect.TIMEOUT, 'Re-enter'])):  # Re-enter new password:
            child.sendline('123456')
    except Exception as e:
        logger.error(str(child))

    # first and last name
    try:
        if (child.expect([pexpect.TIMEOUT, 'last'])):  # What is you first and last name?\n  [Unknown]:
            child.sendline('Calix Barrus')
    except Exception as e:
        logger.error(str(child))

    # unit
    try:
        if (child.expect([pexpect.TIMEOUT, 'unit'])):  # What is the name of your organizational unit?
            child.sendline('UTSA')
    except Exception as e:
        logger.error(str(child))

    # organization
    try:
        if (child.expect([pexpect.TIMEOUT, 'organization'])):
            child.sendline('UTSA')
    except Exception as e:
        logger.error(str(child))

    # city
    try:
        if (child.expect([pexpect.TIMEOUT, 'City'])):
            child.sendline('San Antonio')
    except Exception as e:
        logger.error(str(child))

    # state
    try:
        if (child.expect([pexpect.TIMEOUT, 'State'])):
            child.sendline('TX')
    except Exception as e:
        logger.error(str(child))

    # country code
    try:
        if (child.expect([pexpect.TIMEOUT, 'country code'])):
            child.sendline('01')
    except Exception as e:
        logger.error(str(child))

    # correct?
    try:
        if (child.expect([pexpect.TIMEOUT, 'correct'])):
            child.sendline('y')
    except Exception as e:
        logger.error(str(child))

    # RETURN
    try:
        child.expect(pexpect.EOF)
    except Exception as e:
        logger.debug(str(child))

if __name__ == '__main__':
    pass