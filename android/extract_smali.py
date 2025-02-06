import os
import shutil
from typing import List

from intercept.decode import decode_apk
from util.input import ApkModel

def main():

    project_root = os.path.dirname(os.path.dirname(__file__))
    debug_apk_path = os.path.join(project_root, "android/TaintInsertion/app/build/outputs/apk/debug/app-debug.apk")
    decompiled_directory_path = os.path.join(project_root, "android/decompiledTaintInsertion/app-debug")

    apk = ApkModel(debug_apk_path)
    decode_apk(decompiled_directory_path, apk, clean=True) 

    # Pull desired smali files into data directory
    smali_files_directory = os.path.join(project_root, "data/intercept/smali-files/taint-insertion")

    # android/decompiledTaintInsertion/app-debug/smali_classes3/com/example/taintinsertion/TaintInsertion.smali
    input_directory_prefix = "smali_classes3"
    input_directory_suffix = "com/example/taintinsertion"
    files = ["TaintInsertion.smali"]

    extract_decompiled_smali_code(decompiled_apk_root_path=decompiled_directory_path, 
                                  input_directory_prefix=input_directory_prefix, 
                                  input_directory_suffix=input_directory_suffix, 
                                  files=files, 
                                  output_smali_dir=smali_files_directory)

    # delete decoded smali directory
    shutil.rmtree(decompiled_directory_path)


def extract_decompiled_smali_code(decompiled_apk_root_path: str, input_directory_prefix: str, input_directory_suffix: str, files: List[str], output_smali_dir: str):

    # output_smali_dir = "data/intercept/smali-files/heap-snapshot"

    # input_directory_prefix = "smali_classes3" 
    # input_directory_suffix = "edu/utsa/sefm/heapsnapshot" 
    # files = ["Snapshot.smali", "Snapshot$FieldInfo.smali"]

    dest_directory = os.path.join(output_smali_dir,
                        input_directory_suffix)
    
    src_files = [os.path.join(decompiled_apk_root_path, input_directory_prefix,
                              input_directory_suffix, file_name) for file_name in files]
    dest_files = [os.path.join(dest_directory, file_name) for file_name in files]

    if not os.path.isdir(dest_directory):
        os.makedirs(dest_directory, exist_ok=True)

    # overwrite the existing files
    for i in range(len(files)):
        shutil.copyfile(src_files[i], dest_files[i])


    


if __name__ == "__main__":
    main()