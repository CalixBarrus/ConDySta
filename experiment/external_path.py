import os

home_dir = os.getenv("HOME")

fossdroid_benchmark_apks_dir_path = home_dir + "/programming/benchmarks/wild-apps/data/fossdroid/fossdroid_apks"
fossdroid_ground_truth_xml_path = home_dir + "/programming/benchmarks/wild-apps/fossdroid_ground_truth.xml"

gpbench_apks_dir_path: str = home_dir + "/programming/benchmarks/wild-apps/data/gpbench/apks"
gpbench_ground_truth_xml_path: str = home_dir + "/programming/benchmarks/wild-apps/gpbench_ground_truth.xml"

droidbench_apks_dir_path: str = home_dir + "/programming/benchmarks/DroidBenchExtended/benchmark/apks"

android_platforms_directory: str = home_dir + "/.android_sdk/platforms"

flowdroid_jar_path: str = home_dir + "/programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"




# apksigner_path = home_dir + "/Android/Sdk/build-tools/33.0.0/apksigner"

# aapt_path = ""