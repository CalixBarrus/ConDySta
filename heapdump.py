import os


process_name = "com.bignerdranch.android.buttonwithtoast"
dump_path = "/data/local/tmp/heap_dump_test.hprof"
cmd = "adb shell am dumpheap {} {}".format(process_name, dump_path)
print(cmd)
os.system(cmd)

