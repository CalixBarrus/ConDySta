import re

def printStack(stack):
    for line in stack:
        print(line.strip())
        # print line.strip().split('W System.err: ')[1]


def printNode(node):
    print(
        "node: " + node.abstraction + ' ' + node.stmt + ' ' + node.location_method + ' ' + node.location_class + ' ' + node.location_lineNumber)


def findLeaf(trees):
    leafNodes = []
    for root in trees:
        nodeSet = set()
        stack = []
        nodeSet.add(root)
        stack.append(root)
        while len(stack) > 0:
            cur = stack.pop()
            for child in cur.children:
                if child not in nodeSet:
                    stack.append(cur)
                    stack.append(child)
                    nodeSet.add(child)
                    if len(child.children) == 0:
                        leafNodes.append(child)
                    break
    return leafNodes

def level_1_compare (PIIstack,leakStackTraces):

    # print "level_1_compare ..........."

    level_1_matched_callStacks = []

    if len(PIIstack) > 2:
        PIICallStack_location_method = re.search(r'(?<=at ).*?(?=\()', PIIstack[2]).group(0)
        # print 'PIICallStack_location_method: ' + PIICallStack_location_method
        temp = re.search(r'(?<=\().*(?=\))', PIIstack[2]).group(0)     # get the value in ()
        if temp == 'Unknown Source':
            PIICallStack_location_class = temp
            PIICallStack_location_lineNumber = temp
        else:
            PIICallStack_location_class = temp.split(':')[0].split('.')[0]

            temp_line = temp.split(':')
            if len(temp_line) > 1:
                PIICallStack_location_lineNumber = temp_line[1]
            else:
                PIICallStack_location_lineNumber = ' '

        # print 'PIICallStack_location_class: ' + PIICallStack_location_class
        # print 'PIICallStack_location_lineNumber: ' + PIICallStack_location_lineNumber

        for leakStackTrace in leakStackTraces:
            node = leakStackTrace[0]
            temp = node.location_method.split(' ')
            part1 = temp[0].rstrip(':').lstrip('<')
            part2 = temp[2].split('(')[0]
            method = part1 + '.' + part2
            # print 'leakStackTrace method: ' + method

            if method == PIICallStack_location_method:
                # if node.location_class == PIICallStack_location_class or PIICallStack_location_class == 'SourceFile':
                    if node.location_lineNumber == PIICallStack_location_lineNumber:
                        level_1_matched_callStacks.append(leakStackTrace)
                    else:
                        print("method and class match, but line number does not match!!!")
                        print(
                            "method in node: " + node.stmt + ' ' + node.location_method + ' ' + node.location_class + ' ' + node.location_lineNumber)
                        print(
                            "in callstack: " + PIICallStack_location_method + ' ' + PIICallStack_location_class + ' ' + PIICallStack_location_lineNumber)

    return level_1_matched_callStacks


def level_1_check(PIICallStacks, leakStackTraces):
    print("level 1 check ...........")
    # print len(PIICallStacks)
    level_1_matched = []    # each element is a list, the last element is the PII stack, the rest are matched leakTrace


    for PIIstack in PIICallStacks:
        level_1_matched_leakStack = level_1_compare(PIIstack,leakStackTraces)
        if len(level_1_matched_leakStack) > 0:
            # print len(level_1_matched_leakStack)
            level_1_matched_leakStack.append(PIIstack)    # the last element of this list will be the PII stack
            level_1_matched.append(level_1_matched_leakStack)
    return level_1_matched

def getAllCallStacks_level_1_match(PIIstack, allCallStack):
    print("getAllCallStacks_level_1_match.......")

    printStack(PIIstack)

    AllCallStacks_level_1_match = []
    for callStack in allCallStack:
        if len(callStack) > 2:
            # printStack(callStack)
            all_level_1 = re.search(r'(?<=W System.err: 	at ).*$', callStack[2]).group(0)
            PII_lelve_1 = re.search(r'(?<=W System.err: 	at ).*$', PIIstack[2]).group(0)
            # print all_level_1
            # print PII_lelve_1

            if all_level_1 == PII_lelve_1:
                AllCallStacks_level_1_match.append(callStack)

def level_2_compare (PIIstack,leakStackTraces):
    level_2_matched_callStacks = []


    PIICallStack_location_method = re.search(r'(?<=System.err: 	at ).*?(?=\()', PIIstack[3]).group(0)
    temp = re.search(r'(?<=\().*(?=\))', PIIstack[3]).group(0)
    if temp == 'Unknown Source':
        PIICallStack_location_class = temp
        PIICallStack_location_lineNumber = temp
    else:
        PIICallStack_location_class = temp.split('.')[0]
        PIICallStack_location_lineNumber = temp.split(':')[1]

    for leakStackTrace in leakStackTraces:
        node = leakStackTrace[2]
        temp = node.location_method.split(' ')
        part1 = temp[0].rstrip(':').lstrip('<')
        part2 = temp[2].split('(')[0]
        method = part1 + '.' + part2

        if method == PIICallStack_location_method:
            if node.location_class == PIICallStack_location_class:
                if node.location_lineNumber == PIICallStack_location_lineNumber:
                    level_2_matched_callStacks.append(leakStackTrace)
                else:
                    print("method and class match, but line number does not match!!!")
                    print(
                        "method in node: " + node.stmt + ' ' + node.location_method + ' ' + node.location_class + ' ' + node.location_lineNumber)
                    print(
                        "in callstack: " + PIICallStack_location_method + ' ' + PIICallStack_location_class + ' ' + PIICallStack_location_lineNumber)

    return level_2_matched_callStacks




def level_2_check(level_1_matched):
    print("level 2 check ...........")
    level_2_matched = []
    for match in level_1_matched:
        PIIstack = match[-1]
        level_2_matched_leakStack = level_2_compare(PIIstack, match[:-2])
        if len(level_2_matched_leakStack) > 0:
            level_2_matched_leakStack.appen(PIIstack)
            level_2_matched.append(level_2_matched_leakStack)
    return level_2_matched


#
# def level_2_check(level_1_matched, leakStackTraces):
#     print "level 2 check............."
#
#     # for PIIstack in level_1_matched:
#     #     allCallStacks_level_1_match = getAllCallStacks_level_1_match(PIIstack, allCallStack)
#
#     if allCallStacks_level_1_match:
#         print "len(allCallStacks_level_1_match): " + str(len(allCallStacks_level_1_match))
#     else:
#         print "allCallStacks_level_1_match == null"

    # get stack info
    # PII_location_method = re.search(r'(?<=System.err: 	at ).*?(?=\()', stack[3]).group(0)
    # temp = re.search(r'(?<=\().*(?=\))', stack[3]).group(0)
    # if temp == 'Unknown Source':
    #     PII_location_class = temp
    #     PII_location_lineNumber = temp
    # else:
    #     PII_location_class = temp.split('.')[0]
    #     PII_location_lineNumber = temp.split(':')[1]
    #
    #
    # PII_level_1 = re.search(r'(?<=W System.err: 	at ).*$', stack[2]).group(0)
    #
    #
    # allStack_level_1_match = []
    #
    # for stack in callStackList[0]:    # pick all stacks that have same level 1 with PII stack
    #     level_1 =  re.search(r'(?<=W System.err: 	at ).*$', stack[2]).group(0)
    #     if level_1 == PII_level_1:
    #         allStack_level_1_match.append(stack)




    # level_2_matched = compare(location_method, location_class, location_lineNumber, level_2_nodes)
    # return level_2_matched



    # print stack[0]
    # value = re.search(r'(?<=W System.err: java.lang.Exception: ).*', stack[0]).group(0)
    # print value

    # print "current stack.........................."
    # printStack(stack)



def contextMatch(leakStackTraces, PIIstackTraces):

    level_1_matched = level_1_check(PIIstackTraces, leakStackTraces) # each element is a list, in sub list, the last ele is the callstack, the first ones are matched leak traces

    if len(level_1_matched) == 0:
        print("level 1 check fail")

    else:
        print("after level_1 compare, %d sources matched:" % len(level_1_matched))
        for match in level_1_matched:
            PIICallStack = match[-1]
            for line in PIICallStack:
                print(line.strip().split('W System.err: ')[1])

            # print PIICallStack[0].strip().split('W System.err: ')[1]
            # print PIICallStack[1].strip().split('W System.err: ')[1]
            # print PIICallStack[2].strip().split('W System.err: ')[1]
            # print PIICallStack[3].strip().split('W System.err: ')[1]

            print('Matched path: ')
            for i in range(0, len(match)-1):
                print('path: ' + str(i + 1))
                for node in match[i]:
                    printNode(node)

        # level_2_matched = level_2_check(level_1_matched)
        #
        # if len(level_2_matched) == 0:
        #     print "level 2 check fail"
        #
        # else:
        #     print "after level_2 compare, %d sources matched:" % len(level_1_matched)










