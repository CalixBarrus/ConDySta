# TODO: make this an entry point to call and control all the scripts in the
#  package
from intercept import decode, intercept, rebuildApk, keyGeneration, \
    intercept_config, assignKey


def main():
    config = intercept_config.get_default_intercept_config()

    decode.decode(config)
    intercept.stringReturnDetection(config)
    rebuildApk.rebuild(config)
    keyGeneration.generate_keys(config)
    assignKey.main(config)

    pass

if __name__ == '__main__':
    main()