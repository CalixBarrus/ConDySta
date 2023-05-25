import re
import os

# first run result

def genLeakSource(app):
    """
    This function seems to read a flowdroid input_log_path from a hard coded folder, and
    writes down all the sources associated with found
    leaks into a file in a different hard coded folder.
    The sources and sinks written into this output folder seem to be usable as
    input for flowdroid.
    :param app: The name of the input text file and output text file (each found
    in different hard coded folders).
    """

    out_1 = '/Users/xueling/Desktop/research/hybrid_paper2/result_1_batch2/' + app
    leakSourceSink = open('/Users/xueling/Desktop/hybrid/Leak_SourcesAndSinks_batch2/' + app + '.txt', 'w');
    leakResult = []
    lines = open(out_1).readlines()
    # TODO: why does this double reverse happen here
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
    leakResult.reverse() # TODO: and here?
    for line in leakResult:
        stmt_1 = line.split("on line")[0]
        # TODO: there is no "on line" in a Flowdroid input_log_path from
        #  running flowdroid on a compiled app. Is out_1 a input_log_path from the
        #  instrumented app?
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


