This directory contains source code for an Android App that is used for developing instrumentation code that gets
used during Dynamic Analysis.

I open the HeapSnapshot directory in Android studio, develop, and use the APK from the Debug build. Out of this
APK, the Snapshot class is extracted into data/intercept/smali-files. These smali files are used during instrumentation.

See build-setup-notes.txt