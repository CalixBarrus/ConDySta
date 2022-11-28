import buildTrees
import processLog
import contextMatch_PII
import sys
import time


def process(app):
    start_time = time.time()
    leakStackTraces = buildTrees.buildTrees(app)        # build trees for each path, turning the trees into a list of stackTrace, each element is a stackTrace from source node to sink node

    print 'len(leakStackTraces)' + str(len(leakStackTraces))


    # for stack in leakStackTraces:
    #     for node in stack:
    #         print node.id + ' ' + node.stmt + ' ' + node.location_method + ' ' + node.location_class + ':' +  node.location_lineNumber

    PIIstackTraces = processLog.processLog(app)    # callstacklist contains 2 elelment, PIIcallStack and full callStack
    # print 'len(PIIstackTraces)' + str(len(PIIstackTraces))

    # for line in PIIstackTraces:
    #     print line

    contextMatch_PII.contextMatch(leakStackTraces, PIIstackTraces)   # match the leakStackTraces and callStack

    print app
    print("--- %s seconds ---" % (time.time() - start_time))


apps = open('/Users/xueling/Desktop/hybrid/temp').readlines()
for app in apps:
    app = app.strip()
    process(app)
