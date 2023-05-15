# this script pick the senstive methods which returns email address from ststem input_log_path

import os

def find_methods_containing_PII(input_path, output_path, PII_list):
    setMethods = set()     # remove the duplicated methods from input_log_path

    flag = 0

    with open(input_log_path) as input_file:
        lines = input_file.readlines()
        for line in lines:
            line = line.strip()
            if "W System.err: java.lang.Exception:" in line:
                if any(s in line for s in PII):
                    print(line)
                    flag = 1
                    continue

            if flag == 1:
                if "W System.err: 	at" in line:
                    method = line.split("(")[0].split("W System.err: 	at ")[1]
                    setMethods.add(method)
                    flag = 0
                    continue
                else:
                    print("Error! The next line is not correct!")

    with open(output_path + input_path, 'a') as output_file:
        for method in setMethods:
            output_file.writelines(method + '\n')

if __name__ == '__main__':
    # AdsID  ce3b1e33-8e03-4664-aafc-8d50f474a442
    # device_serial	ZX1G22KHQK
    IMEI = "355458061189396"
    Serial = "ZX1G22KHQK"
    Email = "utsaresearch2018@gmail.com"
    AndroidID = "757601f43fe6cab0"

    PII = (IMEI, Serial, Email, AndroidID)

    input_log_path = "/home/xueling/researchProjects/sourceDetection/input_log_path/"
    methods_output_path = "/home/xueling/researchProjects/sourceDetection/methods/"

    log_file_names = os.listdir(input_log_path)
    for log_file_name in log_file_names:
        if log_file_name.endswith(".log"):
            find_methods_containing_PII(os.path.join(input_log_path,
                                        log_file_name), os.path.join(
                methods_output_path, log_file_name),
                                        PII)