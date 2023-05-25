import re
logPath = "/Users/xueling/Desktop/hybrid/log_batch2/"
app = 'com.bbm'


def processPramDroidLog(app):
    lines = open(logPath+app).readlines()
    print('Log Activities: ')

    for line in lines:
        if 'ActivityManager' in line and app +'/' in line:
            # print line.strip()
            activities = re.findall(r'(?<=com.bbm/).*', line)
            print(activities)


def processFlowDroidLeak(app):
    out_1 = '/Users/xueling/Desktop/hybrid/comparision_result_batch2/'

    leakResult = []
    lines = open(out_1 + app).readlines()
    lines.reverse()

    # get the result block
    for line in lines:
        line = line.strip()
        if "[main] INFO soot.jimple.infoflow.android.SetupApplication" in line:
            leakResult.append(line)
        else:
            break

    leakResult.reverse()

    activities = set()
    for line in leakResult:
        if 'The sink' not in line and 'in method' in line:
            line = line.strip()
            activity = re.search(r'(?<=in method <).*(?=:)', line).group(0)
            activities.add(activity)

    print('FlowDroidLeak Activities: ')
    for activity in activities:
        print(activity)


processFlowDroidLeak(app)

processPramDroidLog(app)

