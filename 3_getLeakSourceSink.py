import re
import os

# first run result

def genLeakSource(app):
    out_1 = '/Users/xueling/Desktop/research/hybrid_paper2/result_1_batch2/' + app
    leakSourceSink = open('/Users/xueling/Desktop/hybrid/Leak_SourcesAndSinks_batch2/' + app + '.txt', 'w');
    leakResult = []
    lines = open(out_1).readlines()
    lines.reverse()

    # get the result block
    for line in lines:
        line = line.strip()
        if "[main] INFO soot.jimple.infoflow.android.SetupApplication" in line:
            leakResult.append(line)
        else:
            break

    # get the source and sink list
    sinks = set()
    sources = set()
    leakResult.reverse()
    for line in leakResult:
        stmt_1 = line.split("on line")[0]
        if "The sink" in line:
            sink = re.search(r'<.*?>', stmt_1).group(0)
            print("\n" + "sink: " + str(sink))
            sinks.add(sink)
        else:
            source = re.search(r'<.*?>', stmt_1)
            if source:
                print("source: " + str(source.group(0)))
                sources.add(source.group(0))

    # add label
    for sink in sinks:
        sink = sink + ' -> _SINK_'
        leakSourceSink.writelines(sink + '\n')
        print(sink)

    for source in sources:
        source = source + ' -> _SOURCE_'
        leakSourceSink.writelines(source + '\n')
        print(source)


#
# genLeakSource('com.adobe.reader')
path = '/Users/xueling/Desktop/hybrid/result_1_batch2'
files = os.listdir(path)
for app in files:
    print(app)
    genLeakSource(app)


