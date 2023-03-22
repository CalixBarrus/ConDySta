import os
import re
from typing import List

from intercept import intercept_config


# def instrument(method):
#     localsNumber = 0
#     locals_index = 0
#     v1 = ""
#     v2 = ""
#     newMethod = []
#     cond_index = 0
#     parameterCount = 0
#     paraNumberList = []
#
#     # print method[0]
#
#     for i in range(len(method)):  # get number of locals
#         line = method[i]
#         if ".locals" in line:
#             locals_index = i
#             localsNumber = int(line.split()[1])
#             break
#
#     for line in method:  # get number of parameter registers
#         paraRegList = re.findall(r'p\d+', line)
#         for item in paraRegList:
#             number = re.findall(r'\d+', item)
#             paraNumberList.append(int(number[0]))
#
#     if len(paraNumberList) > 0:
#         parameterCount = max(paraNumberList) + 1
#     print("parameterCount: {}".format(parameterCount))
#
#     print(paraNumberList)
#
#     print(parameterCount)
#     print(localsNumber)
#
#     # max of 16 locals/parameters? registers?
#     if (16 - localsNumber - parameterCount) >= 1:
#         locals_new = "    .locals " + str(localsNumber + 1)
#         v1 = "v" + str(localsNumber)
#     # v2 = "v" + str(localsNumber + 1)
#
#     else:
#         # Don't instrument method if not enough locals for us to use?
#         return method
#
#     for line in method:
#         if "return-object" in line:
#             # print "return index: %d" %i
#             returnVar = line.split()[1]
#
#             # if flag_moreReturns == 0:
#
#             # text_toBeAdd_cond = "    if-eqz " + returnVar + ", :cond_returnStringDetection" + str(cond_index)
#             # newMethod.append(text_toBeAdd_cond)
#             #
#             # text_toBeAdd_tag = "    const-string " + v1 + ", \"Return string detection printStackTrace and parameter:\""
#             # newMethod.append(text_toBeAdd_tag)
#             #
#             # text_toBeAdd_s4 = "    invoke-static{" + v1 + "," + returnVar + "},Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I"
#             # newMethod.append(text_toBeAdd_s4)
#             #
#             # text_toBeAdd_s1 = "    new-instance " + v2 + ", Ljava/lang/Exception;"
#             # newMethod.append(text_toBeAdd_s1)
#             #
#             # text_toBeAdd_s2 = "    invoke-direct {" + v2 + "," + v1 + "}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V"
#             # newMethod.append(text_toBeAdd_s2)
#             #
#             # text_toBeAdd_s3 = "    invoke-virtual {" + v2 + "}, Ljava/lang/Exception;->printStackTrace()V"
#             # newMethod.append(text_toBeAdd_s3)
#             #
#             # text_toBeAdd_s5 = "    :cond_returnStringDetection" + str(cond_index) + "\n"
#             # newMethod.append(text_toBeAdd_s5)
#
#             text_toBeAdd_cond = "    if-nez " + returnVar + ", " \
#                                                             ":cond_returnStringDetection_" + str(
#                 cond_index)
#             newMethod.append(text_toBeAdd_cond)
#
#             text_toBeAdd_s1 = "    new-instance " + v1 + ", Ljava/lang/Exception;"
#             newMethod.append(text_toBeAdd_s1)
#
#             text_toBeAdd_s2 = "    invoke-direct {" + v1 + "," + returnVar + "}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V"
#             newMethod.append(text_toBeAdd_s2)
#
#             text_toBeAdd_s3 = "    invoke-virtual {" + v1 + "}, Ljava/lang/Exception;->printStackTrace()V"
#             newMethod.append(text_toBeAdd_s3)
#             text_toBeAdd_s5 = "    :cond_returnStringDetection" + str(
#                 cond_index) + "\n"
#             newMethod.append(text_toBeAdd_s5)
#
#             newMethod.append(line)
#
#             # flag_moreReturns = 1
#             cond_index += 1
#
#
#
#
#         else:
#             newMethod.append(line)
#             # print "else: %s" %line
#
#     # print "xxxxxxxxxxxxxxxxxxxxxx new method: "
#
#     # for line in newMethod:
#     #         print line.strip()
#
#     newMethod[locals_index] = locals_new
#
#     return newMethod


def stringReturnDetection(config: intercept_config.InterceptConfig):
    print("Instrumenting smali code...")

    instrument_smali_code(config.decoded_apks_path, StringReturnInstrumenter())
    return

    # decoded_apks_path = config.decoded_apks_path
    #
    # apkPath = decoded_apks_path
    # flag = 0
    #
    # v1 = " "
    # v2 = " "
    #
    # cmd = "find {} -iname *.smali ".format(apkPath)
    # smali_paths = os.popen(cmd).readlines()
    #
    # print(str(len(smali_paths)) + " smali files found!")
    #
    # for smali_path in smali_paths:
    #     smali_path = smali_path.strip()
    #     smali_file = open(smali_path)
    #     text_orig = smali_file.readlines()
    #     text_new = []
    #     method = []
    #     # print len(text_orig)
    #
    #     for lines in text_orig:
    #         line = lines.rstrip()
    #
    #         # Start method collection for any string return functions that are
    #         # not abstract, contructors, or native.
    #         if ".method" in line and "abstract" in line:
    #             text_new.append(line)
    #             continue
    #
    #         elif ".method" in line and "constructor" in line:
    #             text_new.append(line)
    #             continue
    #
    #
    #         elif ".method" in line and "native" in line:
    #             text_new.append(line)
    #             continue
    #
    #         elif ".method" in line and ")Ljava/lang/String;" in line:  # method return string
    #             print(smali_path)
    #             print(line)
    #             flag = 1
    #             method.append(line)
    #             continue
    #
    #         # When an appropriate string return method is detected, collect all
    #         # the code until ".end method" into the "method" variable. When
    #         # ".end method" gets hit, pass it to "instrument" and begin scanning
    #         # for more methods.
    #         if flag == 1:
    #             if ".end method" in line:
    #                 method.append(line)
    #                 flag = 0
    #                 newMethod = instrument(method)
    #                 method = []
    #                 for line in newMethod:
    #                     text_new.append(line)
    #             else:
    #                 method.append(line)
    #         else:
    #             text_new.append(line)
    #
    #     smali_file.close()
    #     # Replace the smali code with the instrumented code
    #     os.remove(smali_path)
    #     fw = open(smali_path, 'w+')
    #     for line in text_new:
    #         fw.write(line + '\n')


class InformalInstrumenterInterface(object):
    def instrument(self, contents: List[str]) -> List[str]:
        """Scan through contents of smali file and return the instrumented
        smali code"""
        raise NotImplementedError("Interface not implemented")


def instrument_smali_code(target_folder_path,
                          instrumenter: InformalInstrumenterInterface):
    # Find the names of all the smali files in the target folder
    cmd = "find {} -iname *.smali ".format(target_folder_path)
    smali_paths = os.popen(cmd).readlines()
    # print(str(len(smali_paths)) + " smali files found!")

    for smali_path in smali_paths:
        smali_path = smali_path.strip()

        with open(smali_path, "r") as f:
            contents = f.readlines()

        # contents.insert(index, value)
        # instrumenter.instrument(contents)

        with open(smali_path, "w") as f:
            contents = "".join(instrumenter.instrument(contents))
            f.write(contents)


class StringReturnInstrumenter(InformalInstrumenterInterface):
    def instrument(self, contents: List[str]) -> List[str]:
        """Print out stack traces right before
        the return statement of all functions that return strings"""
        is_reading_method = False
        method_start_index = 0
        new_contents = None
        method_number = 1
        i = 0
        while i < len(contents):
            line = contents[i].rstrip()

            # Start method collection for any string return functions that are
            # not abstract, contructors, or native.
            if ".method" in line and "abstract" in line:
                i += 1
                continue

            elif ".method" in line and "constructor" in line:
                i += 1
                continue

            elif ".method" in line and "native" in line:
                i += 1
                continue

            elif ".method" in line and ")Ljava/lang/String;" in line:  # method return string
                method = []
                is_reading_method = True
                method_start_index = i
                method.append(line)
                i += 1
                continue

            # When an appropriate string return method is detected, collect all
            # the code until ".end method" into the "method" variable. When
            # ".end method" gets hit, pass it to "instrument" and begin scanning
            # for more methods.
            if is_reading_method == True:
                if ".end method" in line:
                    is_reading_method = False
                    new_contents = self._instrument_method(contents,
                                                     method_start_index, i,
                                                           method_number)
                    method_number += 1

            i += 1

        if new_contents is None:
            return contents
        else:
            return new_contents

    def _instrument_method(self, contents, method_start_index,
                           method_end_index, method_number):
        localsNumber = 0
        locals_index = 0
        parameterCount = 0
        paraNumberList = []
        paraRegList = []

        for i in range(method_start_index, method_end_index + 1):
            # get number of locals
            line = contents[i]
            if ".locals" in line:
                locals_index = i
                localsNumber = int(line.split()[1])

            paraRegList = paraRegList + re.findall(r'p\d+', line)

        for item in paraRegList:
            number = re.findall(r'\d+', item)
            paraNumberList.append(int(number[0]))

        if len(paraNumberList) > 0:
            parameterCount = max(paraNumberList) + 1

        # Most dalvik opcodes can only use first 16 registers
        # Distinction between local registers and parameter registers (vX and
        # pX) is virtual. In reality there is only one set of registers and
        # locals are first, then parameters
        if (16 - localsNumber - parameterCount) >= 1:
            # Overwrite locals declaration to reflect the additional local
            # used by the inserted code
            contents[locals_index] = "    .locals " + str(localsNumber + 1)
            v1 = "v" + str(localsNumber)
        else:
            # Don't instrument method if not enough locals for us to use
            # TODO: modify function to stick required local into a local
            #  register
            return contents

        return_statement_number = 1

        i = method_start_index
        while i < method_end_index:
        # for i in range(method_start_index, method_end_index + 1):
            line = contents[i]

            if "return-object" in line:
                # line will be "return-object v[#]"
                returnVar = line.split()[1]
                text_to_insert = [log_stacktrace(returnVar, v1,
                                                 method_number,
                                                 return_statement_number)]

                # insert text_to_insert before the "return-object" line
                return_statement_number += 1

                contents[i:i] = text_to_insert

                # increment relevant loop indices
                i += 1
                method_end_index += 1

            i += 1

        return contents


def log_stacktrace(return_register, empty_register_1,
                   method_number, return_statement_number):

    v1 = empty_register_1
    return f"""
if-nez {return_register}, :cond_returnStringDetection{str(method_number)}_{str(return_statement_number)}
    new-instance {v1}, Ljava/lang/Exception;
    invoke-direct {{{v1}, {return_register}}}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V
    invoke-virtual {{{v1}}}, Ljava/lang/Exception;->printStackTrace()V
:cond_returnStringDetection{str(method_number)}_{str(return_statement_number)}

"""

def log_string_return_and_stacktrace(return_register, empty_register_1,
                                     empty_register_2, method_number,
                                     return_statement_number):
    """
    :param return_register: str
    :param empty_register_1: str
    :param empty_register_2: str
    :param method_number: str
    :param return_statement_number: str
    :return: smali code to be inserted
    """
    v1 = empty_register_1
    v2 = empty_register_2
    return f"""
# if return is a null string, skip the inserted code
if-eqz {return_register}, :cond_returnStringDetection_{method_number}_{return_statement_number}

# Create logging message with return value
new-instance {v2} ,Ljava/lang/StringBuilder;
invoke-direct {{{v2}}}, Ljava/lang/StringBuilder;-><init>()V

const-string {v1}, "ReturnValue:"

invoke-virtual {{{v2},{v1}}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

invoke-virtual {{{v2}, {return_register}}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

invoke-virtual {{{v2}}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

move-result-object {v2}

const-string {v1}, "DySta-Instrumentation"

# Log return value with a tag
invoke-static {{{v1},{v2}}}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

const-string {v2},"StackTrace:"

invoke-static {{{v1},{v2}}}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

new-instance {v2}, Ljava/lang/Exception;

invoke-direct {{{v2}}}, Ljava/lang/Exception;-><init>()V

invoke-virtual {{{v2}}}, Ljava/lang/Exception;->printStackTrace()V

:cond_returnStringDetection_{method_number}_{return_statement_number}

"""


if __name__ == '__main__':
    config = intercept_config.get_default_intercept_config()

    stringReturnDetection(config)


