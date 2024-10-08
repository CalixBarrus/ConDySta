from typing import List

import pexpect
import sys
import os

from experiment import personal_info
from hybrid.hybrid_config import HybridAnalysisConfig, apk_key_path
from util.input import ApkModel

import util.logger
logger = util.logger.get_logger(__name__)

def generate_keys_batch(keys_directory_path: str, apks: List[ApkModel]):
    for apk in apks:
        generate_keys_single(keys_directory_path, apk)

def generate_keys_single(keys_directory_path: str, apk: ApkModel):

    if os.path.isfile(apk_key_path(keys_directory_path, apk)):
        logger.debug(f"APK keystore {apk.apk_key_name()} already exists, skipping.")
        return

    cmd = "keytool -genkey -alias abc.keystore -keyalg RSA -validity 20000 -keystore {}".format(apk_key_path(keys_directory_path, apk))
    logger.debug(cmd)

    # Todo: should some of this logic be in util.subprocess? It's fairly business logic specific, so it may be ok leaving it here
    # set encoding to utf-8 or stdout will whine about getting bytes, instead of strings

    # Use the first line if you want to see the output of the signing process
    # child = pexpect.spawn(cmd, logfile=sys.stdout, encoding='utf-8')
    child = pexpect.spawn(cmd, encoding='utf-8')


    # Details that will be used for signing the apk
    name = personal_info.name  # First and last name
    unit = personal_info.unit  # I used the university acronym
    organization = personal_info.organization  # I used the same value as unit
    city = personal_info.city
    state = personal_info.state
    country_code = personal_info.country_code
    if any([detail == "" for detail in [name, unit, organization, city, state, country_code]]):
        raise NotImplementedError("Please fill out details for key signing")


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
            child.sendline(name)
    except Exception as e:
        logger.error(str(child))

    # unit
    try:
        if (child.expect([pexpect.TIMEOUT, 'unit'])):  # What is the name of your organizational unit?
            child.sendline(unit)
    except Exception as e:
        logger.error(str(child))

    # organization
    try:
        if (child.expect([pexpect.TIMEOUT, 'organization'])):
            child.sendline(organization)
    except Exception as e:
        logger.error(str(child))

    # city
    try:
        if (child.expect([pexpect.TIMEOUT, 'City'])):
            child.sendline(city)
    except Exception as e:
        logger.error(str(child))

    # state
    try:
        if (child.expect([pexpect.TIMEOUT, 'State'])):
            child.sendline(state)
    except Exception as e:
        logger.error(str(child))

    # country code
    try:
        if (child.expect([pexpect.TIMEOUT, 'country code'])):
            child.sendline(country_code)
    except Exception as e:
        logger.error(str(child))

    # correct?
    try:
        if (child.expect([pexpect.TIMEOUT, 'correct'])):
            child.sendline('y')
    except Exception as e:
        logger.error(str(child))

    # correct?
    try:
        if (child.expect([pexpect.TIMEOUT, 'Enter key password'])):
            child.sendline("")
    except Exception as e:
        logger.error(str(child))

    # RETURN
    try:
        child.expect(pexpect.EOF)
    except Exception as e:
        logger.debug(str(child))

if __name__ == '__main__':
    pass