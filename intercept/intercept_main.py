# TODO: make this an entry point to call and control all the scripts in the
#  package
from intercept import decode, instrument, rebuildApk, keyGeneration, \
    intercept_config, assignKey, clean, monkey


def main(config, do_clean=True):
    if do_clean:
        clean.clean(config)
    decode.decode(config)
    instrument.stringReturnDetection(config)
    rebuildApk.rebuild(config)
    keyGeneration.generate_keys(config)
    assignKey.assign_key(config)

    monkey.run_apk(config)

    pass

def generate_smali_code(config):
    clean.clean(config)
    decode.decode(config)

def rebuild_smali_code(config):
    rebuildApk.rebuild(config)
    keyGeneration.generate_keys(config)
    assignKey.assign_key(config)


def instrument_app(config):
    clean.clean(config)
    decode.decode(config)
    instrument.stringReturnDetection(config)
    rebuildApk.rebuild(config)
    keyGeneration.generate_keys(config)
    assignKey.assign_key(config)

if __name__ == '__main__':
    configuration = intercept_config.get_default_intercept_config()

    # main(configuration)
    # generate_smali_code(configuration)
    instrument_app(configuration)