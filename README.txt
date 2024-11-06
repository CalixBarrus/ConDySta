Setup Notes:

Java Setup:
I'm currently using Java 17
gradle, used in HeapSnapshot directory, requires Java 11+

Python Setup:
Dependency in flow.py for >= python 3.9

Quick install instructions from the website https://docs.anaconda.com/miniconda/:

mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh

# Finish the install
~/miniconda3/bin/conda init bash
# Have the .bashrc changes reflect in the current shell
source $HOME/.bashrc  

For this project, have installed the following python modules:
numpy, pandas, pexpect
conda install numpy pandas pexpect


Android Setup: 

Download command line tools from the GUI link here. Go to the section called "Command line tools only"
https://developer.android.com/studio#command-tools

# it wants a specific directory structure, you may need to play with it
cd ~
mkdir .android_sdk
mkdir .android_sdk/cmdline-tools
mkdir .android_sdk/cmdline-tools/latest
unzip commandlinetools-linux-9477386_latest.zip -d ~/.android_sdk/cmdline-tools/latest

# export these env variables in the working terminal and/or add them to .bashrc
export ANDROID_SDK_ROOT="$HOME/.android_sdk"
# export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$PATH"
# export PATH="$ANDROID_SDK_ROOT/emulator:$PATH"

# make sure java is updated (>= Java 17)
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-25"
# also useful: sdkmanager --list

# For gpbench, 
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-14"
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-17"
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-19"
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-21"
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-22"
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-23"
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-24"
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platforms;android-25"

Ensure the following Android platform tools can be run from the command line:
adb 
apksigner 
aapt 

Other dependencies:

Install apktool (https://apktool.org/docs/install/)
apktool needs to be on the path.







