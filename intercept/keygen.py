import pexpect
import sys
import os

from intercept import intercept_config

from util import logger
logger = logger.get_logger('intercept', 'keygen')

def generate_keys(config):
    logger.info("Generating Keys...")

    key_path = config.key_path
    rebuilt_apks_path = config.rebuilt_apks_path

    apkNameList = []
    for apk_name in os.listdir(rebuilt_apks_path):
        apk_name = apk_name.strip()
        apkNameList.append(apk_name)

    i = 1
    files = os.listdir(key_path)
    for apkName in apkNameList:

        apkKeyName = apkName + ".keystore"
        if apkKeyName in files:
            logger.debug("APK keystore {} already exists, skipping.".format(
                apkKeyName))
        else:
            cmd = "keytool -genkey -alias abc.keystore -keyalg RSA -validity 20000 -keystore {}{}".format(key_path, apkKeyName)
            logger.debug(cmd)

            # set encoding to utf-8 or stdout will whine about getting bytes, instead of strings

            # Use the first line if you want to see the output of the signing process
            # child = pexpect.spawn(cmd, logfile=sys.stdout, encoding='utf-8')
            child = pexpect.spawn(cmd, encoding='utf-8')


            #password
            try:
                if(child.expect('password') == 0): # Enter keystore password:
                    child.sendline('123456')
            except Exception as e:
                logger.error(str(child))


            #re-enter password
            try:
                if (child.expect([pexpect.TIMEOUT, 'Re-enter'])): # Re-enter new password:
                    child.sendline('123456')
            except Exception as e:
                logger.error(str(child))


            # first and last name
            try:
                if (child.expect([pexpect.TIMEOUT, 'last'])):# What is you first and last name?\n  [Unknown]:
                    child.sendline('Calix Barrus')
            except Exception as e:
                logger.error(str(child))


            # unit
            try:
                if (child.expect([pexpect.TIMEOUT, 'unit'])): # What is the name of your organizational unit?
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

            i+= 1

if __name__ == '__main__':
    configuration = intercept_config.get_default_intercept_config()

    generate_keys(configuration)