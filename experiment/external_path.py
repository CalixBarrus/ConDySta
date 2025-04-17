import os
import configparser

import util.logger
logger = util.logger.get_logger(__name__)

# External Paths are defined in external_path.ini in project root. See external_path_template.ini for an example.

project_root = os.path.dirname(os.path.dirname(__file__))

config = configparser.ConfigParser()
if not os.path.exists(os.path.join(project_root, 'external_path.ini')):
    raise FileNotFoundError(f"external_path.ini not found in {project_root}. Please create it from external_path_template.ini.")
config.read(os.path.join(project_root, 'external_path.ini'))

home_dir = os.getenv("HOME")

# handle absolute paths or paths relative to home. 
def _validate_path(path: str):
    if os.path.isdir(path) or os.path.isfile(path):
        return path
    
    # Maybe it's a path relative to home?
    path_from_home = os.path.join(home_dir, path)
    if os.path.isdir(path_from_home) or os.path.isfile(path_from_home):
        return path_from_home
    else:
        logger.error(f"External Resources not found at {path}")
        return ""

# fossdroid_benchmark_apks_dir_path = home_dir + "/programming/benchmarks/wild-apps/data/fossdroid/fossdroid_apks"
fossdroid_benchmark_apks_dir_path = _validate_path(config['benchmark']['fossdroid_benchmark_apks_dir_path'])
# fossdroid_ground_truth_xml_path = home_dir + "/programming/benchmarks/wild-apps/fossdroid_ground_truth.xml"
fossdroid_ground_truth_xml_path = _validate_path(config['benchmark']['fossdroid_ground_truth_xml_path'])

# gpbench_apks_dir_path: str = home_dir + "/programming/benchmarks/wild-apps/data/gpbench/apks"
gpbench_apks_dir_path: str = _validate_path(config['benchmark']['gpbench_apks_dir_path'])
# gpbench_ground_truth_xml_path: str = home_dir + "/programming/benchmarks/wild-apps/gpbench_ground_truth.xml"
gpbench_ground_truth_xml_path: str = _validate_path(config['benchmark']['gpbench_ground_truth_xml_path'])

# droidbench_apks_dir_path: str = home_dir + "/programming/benchmarks/DroidBenchExtended/benchmark/apks"
# droidbench_apks_dir_path: str = home_dir + "/Documents/programming/research-programming/benchmarks/DroidBenchExtended/benchmark/apks"
droidbench_apks_dir_path: str = _validate_path(config['benchmark']['droidbench_apks_dir_path'])

# flowdroid_jar_path: str = home_dir + "/programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
# TODO: need to handle flowdroid versioning differently.
flowdroid_jar_path: str = _validate_path(config['flowdroid']['flowdroid_jar_path'])

# android_platforms_directory: str = home_dir + "/.android_sdk/platforms"
android_platforms_directory: str = _validate_path(config['flowdroid']['android_platforms_directory'])






# apksigner_path = home_dir + "/Android/Sdk/build-tools/33.0.0/apksigner"

# aapt_path = ""