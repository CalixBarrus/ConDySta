import commands
SourceAndSinks_default = '/Users/xueling/Desktop/hybrid/SourceAndSinks_default.txt'
signaturePath = "/Users/xueling/Desktop/hybrid/PII_sourceSig_batch2/"


# remove the default source from detected sources

def generateSourceFile(app):
    newSource = []
    detectedSource = open(signaturePath + app).readlines();
    default = open(SourceAndSinks_default).readlines();
    for source in detectedSource:
        if source in default:
            print source + "exists.....";
        else:
            # print source
            newSource.append(source)


    # write newSource into the default sinks and generate souceAndSinks.txt for taint analysis:
    sink_default = open('/Users/xueling/Desktop/hybrid/sinks_default').readlines()
    for line in sink_default:
        newSource.append(line)


    fw = open('/Users/xueling/Desktop/hybrid/SourcesAndSinks_batch2/' + app + '.txt', 'w')
    for line in newSource:
        fw.writelines(line)


apps = commands.getoutput('ls ' + signaturePath).split('\n')
for app in apps:
    generateSourceFile(app)


