import re
import os
out_1 = '/Users/xueling/Desktop/research/hybrid_paper2/result_1/'
out_1 = '/Users/xueling/Desktop/research/hybrid_paper2/result_1_batch2/'


apps = os.listdir(out_1)


for app in apps:
    # print app
    leakResult = []
    lines = open(out_1 + app).readlines()
    lines.reverse()

    source_count_UI = 0
    source_count_PII = 0

    # get the result block
    for line in lines:
        line = line.strip()
        if "[main] INFO soot.jimple.infoflow.android.SetupApplication" in line:
            leakResult.append(line)
        else:
            break

    for line in leakResult:
        stmt_1 = line.split("on line")[0]
        # print stmt_1

        if "The sink" in line:
            sink = re.search(r'<.*?>', stmt_1).group(0)
            # print 'sink: ' + sink

        else:
            match = re.search(r'<.*?>', stmt_1)
            if match:
                source = match.group(0)

                # print source
                if 'android.widget' in source:
                    source_count_UI += 1
                    # print 'IU source ' + str(source_count_UI) + ': ' + source
                else:
                    source_count_PII += 1
                    # print 'PII source ' + str(source_count_PII) + ': ' + source
    print(app + '      PII source ' + str(source_count_PII))
