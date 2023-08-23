Setup Notes:

Have Java and Python 3 installed.

Check file names in hybrid_config.py and intercept_config.py

Make "data/intercept", "data/logs", "data/sources-and-sinks", "data/logs/instrumentation-run", "input-apk-lists" and "data/input-apks" directories.

Install the following python modules:
pexpect

Install apktool (https://apktool.org/docs/install/)

Run setup_folders() method in hybrid/experiment.py

Ensure the following tools can be run from the command line:
    In /usr/local/bin run "sudo ln -s /Users/calix/Library/Android/sdk/platform-tools/adb adb" where the second to last
    arg is the path to the executable, and the last arg is the name of the executable
adb (/Users/calix/Library/Android/sdk/platform-tools/adb)
apksigner (/Users/calix/Library/Android/sdk/build-tools/34.0.0/apksigner)
aapt (/Users/calix/Library/Android/sdk/build-tools/34.0.0/aapt)

Get a JAR of Flowdroid, and make sure the path in hybrid_config.py points to it.

You probably will want to download and use benchmarks, I used the ones from ReproDroid's website (https://foellix.github.io/ReproDroid/).

If using injected directories of smali code, add the code being injected to data/intercept/smali-files.

