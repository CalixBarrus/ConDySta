import re

# lines = open(outLeakSourceSink + app + '.txt').readlines()

# seperate result into paths
def getPaths(lines):
    paths = []  # including all the paths, each element is a building path
    temp = []
    flag = 0

    for i in range (0, len(lines)):
        if lines[i]:
            lines[i] = lines[i].strip()
            if "[main] INFO soot.jimple.infoflow.data.pathBuilders.ContextSensitivePathBuilder - Building path " in lines[i] and flag == 0:
                flag += 1
                temp = []

            elif "INFO soot.jimple.infoflow.data.pathBuilders.ContextSensitivePathBuilder - Building path" in lines[i] and flag != 0:
                # print temp
                paths.append(temp)
                temp = []
                flag += 1

            elif i == (len(lines) - 1):
                paths.append(temp)

            elif flag != 0:
                temp.append(lines[i])
    return paths


# path[] for each tree/path, paths[], each element will be one tree/path

# travel the tree by dfs to find the node
def getNode(id, node):
    nodeSet = set()
    stack = []
    nodeSet.add(node)
    stack.append(node)
    while len(stack) > 0:
        cur = stack.pop()
        if cur.id == id:
            return cur
        for child in cur.children:
            if child not in nodeSet:
                stack.append(cur)
                stack.append(child)
                nodeSet.add(child)
                if child.id == id:
                    return child
                break

def turnToNodes(branch):
    nodes = []
    # turning each line into a node, connect them as an edge
    for line in branch:
        if line and "Thread id" in line:
            # print line
    # id
            id = re.search(r'(?<=Thread id: )\d*', line).group(0)

    # abstraction
            temp = re.search(r'(?<=abstraction.toString:).*?(?=;)', line)
            if temp:
                abstraction = temp.group(0)

    # stmt
            stmt = re.search(r'(?<=abstraction.getCurrentStmt: ).*?(?=;)', line).group(0)

    # parentId
            temp = re.search(r'(?<=Parent Thread id: )\d*', line)
            if temp:
                parentId = temp.group(0)
            else:
                parentId = ''

            location = re.search(r'(?<=location class and method = ).*?(?=;)', line).group(0)
    # location_class:
            location_class = location.split(': ')[0].split('.')[-1]

    # location_method
    #         location_method = location.split(': ')[1].rstrip('>')
            location_method = re.search(r'(?<=location class and method = ).*?(?=;)', line).group(0)

    # line Number
            location_lineNumber = re.search(r'(?<=JavaSourceStartLineNumber: )\d*', line).group(0)
            node = Node(id, stmt, abstraction, parentId, location_class, location_method, location_lineNumber, '')
            nodes.append(node)

    return nodes

def processMainBranch(branch, root):
    # print "main: " + branch[0]
    edge = turnToNodes(branch);

    root = edge[0]

    for i in range(1, len(edge)):
        if i == 1:
            root.addChild(edge[i])
            edge[i].parentNode = root
            # edge[i].addChild(edge[i+1])

        else:
            edge[i-1].addChild(edge[i])
            edge[i].parentNode = edge[i-1]

        # print edge[i].id + "'s parent id: " + edge[i].parentNode.id
        #
        # print edge[i-1].id + "'s child id: " + edge[i-1].getChildren()[0].id

    return root

# link all the nodes into an edge, the head's parent is root



    # print nodes[1].parentNode.getId()

    # #print out the branch
    # for i in range(1, len(edge)):
    #     print 'node: ' + edge[i].getId()
    #     print 'parent: ' + edge[i].getParentNode().getId()

# separete path into branches, don't know what it is, comments

# leakSourcesAndSinks = open('/Users/xueling/Desktop/hybrid/leakSourceSink.txt').readlines()
# leakSources = []
# for line in leakSourcesAndSinks:
#     if '-> _SOURCE_' in line:
#         source = re.search(r'<.*?>', line).group(0)
#         leakSources.append(source)


def processNeighborBranch(branch, root):
    parentID = re.search(r'(?<=Thread id: )\d*', branch[0]).group(0)
    # print 'parentID: ' + parentID
    parentNode = getNode(parentID, root)
    if parentNode:
        # print "found parentNode: " + parentNode.getId()

        edge = turnToNodes(branch[1:])

        # remove the edge whose leafnode is not leaksource
        # if any(s in edge[-1].stmt for s in leakSources):   # if the stmt contains any of the leaksouces

        if len(edge) == 1:
            parentNode.addChild(edge[0])
            edge[0].parentNode = parentNode
        else:
            for i in range(0, len(edge)):
                if i == 0:
                    parentNode.addChild(edge[i])
                    edge[i].parentNode = parentNode

                else:
                    edge[i - 1].addChild(edge[i])
                    edge[i].parentNode = edge[i - 1]

def processPath(path, root):
    branches = []
    temp = []
    for line in path:
        if 'Parent Thread id:' in line:
            branches.append(temp)
            temp = []
            temp.append(line)
        else:
            temp.append(line)
    branches.append(temp)
    root = processMainBranch(branches[0], root)

    for branch in branches[1:]:
        # print "branch: " + branch[0]
        processNeighborBranch(branch, root)

    return root




# paths[[path1[brach1[], branch2[]], path2[]]]


class Node:
    def __init__(self, id, stmt, abstraction, parentId, location_class, location_method, location_lineNumber, parentNode):
        self.id = id
        self.stmt = stmt
        self.abstraction = abstraction
        self.location_method = location_method
        self.location_class = location_class
        self.location_lineNumber = location_lineNumber
        self.parentId = parentId
        self.children = []
        self.parentNode = parentNode

    def getId(self):
        return self.id

    def getParentNode(self):
        return self.parentNode

    def addChild(self, node):
        self.children.append(node)

    def getChildren(self):
        return self.children

    def show(self,layer):
        print  "   |"*layer+self.id  + '  ' + self.stmt + '   ' + self.location_method + '(' + self.location_class + ".java:" + self.location_lineNumber + ')'
        map(lambda child:child.show(layer+1),self.children)



def findLeaf(trees):     # given a list of trees, found all the leafnode
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

def getStackTrace(leafNode):
    # print leafNode.stmt
    # print leafNode.id
    stackTrace = []
    # stackTrace.append(leafNode)    # the first element in stack is the source

    node = leafNode

    while (node):
        # print "node: " + node.id
        stackTrace.append(node)
        node = node.parentNode
        # print "node.parentNode: " + node.id
    return stackTrace


def turnTreesToStackTrace(trees):     # format all trees into a list of path, each path is a list of node
    leakStackTrace = []

    leafNodes = findLeaf(trees)

    for leafNode in leafNodes:
        # print leafNode.id
        stackTrace = getStackTrace(leafNode)
        leakStackTrace.append(stackTrace)

    return leakStackTrace

def buildTrees(app):
    # FlowDroidPath = '/Users/xueling/Desktop/hybrid/result_2/'
    # FlowDroidPath = '/Users/xueling/Desktop/hybrid/result_2_batch2_path/'
    FlowDroidPath = '/Users/xueling/Desktop/research/hybrid_paper2/result_2_batch2_path/'

    trees = []
    lines = open(FlowDroidPath + app).readlines()
    # lines = open('/Users/xueling/Desktop/hybrid/out').readlines()
    print 'len(lines)' + str(len(lines))
    paths = getPaths(lines)
    i = 0
    for path in paths:
        try:
            print 'print path:'
            if len(path) > 0:
                print path[0]
            i += 1
            print 'Processing path ' + str(i) + '.........'
            root = Node('', '', '', '', '', '', '','')
            tree = processPath(path, root)
            tree.show(0)
            trees.append(tree)
        except Exception as e:
            print "Exception"


    leakStackTrace = turnTreesToStackTrace(trees)    # turning the tree into a big list, each element is a list of node, indicate a path from source to sink

    # print "len(leakStackTrace): " + str(len(leakStackTrace))
    #
    # for node in leakStackTrace[30]:
    #     print node.id

    return leakStackTrace


