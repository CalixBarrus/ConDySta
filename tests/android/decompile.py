import os

from intercept.decode import decode_apk
from util.input import ApkModel

def main():

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    debug_apk_path = os.path.join(project_root, "tests/android/InstrumentableExample/app/build/outputs/apk/debug/app-debug.apk")
    result_path = os.path.join(project_root, "tests/data/decompiledInstrumentableExample/")

    apk = ApkModel(debug_apk_path)
    decode_apk(result_path, apk, clean=True)

if __name__ == "__main__":
    main()