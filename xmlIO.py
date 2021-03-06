import xml.sax as xs
import copy
import gc
import random

class LoadCPT(xs.ContentHandler):
    # initialization function
    def __init__(self):
        self.currentTag = None      # store current tage name
        self.attrs = {}             # store attributes {attr: [type, outcome]}
        self.type = None            # store type of current VARIABLE
        self.name = None            # store name of current VARIABLE or node
        self.tableName = None       # name of table

        self.CPT = {}               # CPT {node: [[parents], [children], [value]]}
    
    # start of each element
    def startElement(self, tag, attributes):
        self.currentTag = tag
        if(tag == "VARIABLE"):
            self.type = attributes["TYPE"]

    # end of each element
    def endElement(self, tag):
        self.currentTag = " "
    
    # trigger
    def characters(self, content):
        #-------inside VARIABLE-------
        # name label
        if(self.currentTag == "NAME"):
            #table name
            if(self.tableName == None):
                self.tableName = content
            #attribute name
            else:
                self.name = content
                self.attrs[content] = [self.type]

        # outcome label / type of attribute
        if(self.currentTag == "OUTCOME"):
            self.attrs[self.name].append(content)

        #------inside DEFINITION-------
        # FOR label / node attribute
        if(self.currentTag == "FOR"):
            self.name = content
            # content already in CPT
            if(content not in self.CPT):
                self.CPT[content] = [[], [], []]
        
        # GIVEN label / parent attribute
        if(self.currentTag == "GIVEN"):
            # parent must in CPT
            if(content not in self.CPT):
                self.CPT[content] = [[], [], []]
            self.CPT[self.name][0].append(content)
            self.CPT[content][1].append(self.name)
        
        # TABLE label / CPT value
        if(self.currentTag == "TABLE"):
            # id follows certain order
            if(len(content) != 0):
                self.CPT[self.name][2] += [float(num) for num in content.split()]

class GetCPT:
    # initialization function
    def __init__(self, fileName):
        self.attrs = None   # store attributes {attr: [type, outcome]}
        self.CPT = None     # CPT {node: [[parents], [children], [[[attr value, ...], value], ...]}  the last on of [attr value, ...] is ndoe
        self.tableName = None # name of table
        self.count = 0      # count of probability used

        # get fileName 
        if(type(fileName) == int):
            self.__createExtreCPT(fileName)
        else:
            self.__getCPT(fileName)

    # create extreme CPT
    def __createExtreCPT(self, number):
        self.attrs = {str(i):["normal", "true", "false"] for i in range(number)}
        self.attrList = [str(i) for i in list(range(number))]
        self.CPT = {}
        for attrId, attr in enumerate(self.attrList):
            if(int(attr) < 2):
                parents = copy.deepcopy(self.attrList[:attrId])
            else:
                parents = copy.deepcopy(self.attrList[attrId - 2:attrId])
            children = copy.deepcopy(self.attrList[attrId + 1: attrId + 3])
            self.CPT[attr] = [parents, children, []]

            # randomly get probability
            for value in range(2 ** (len(parents))): 
                CPTValue = [[[], 0], [[], 0]]
                valueTemp = value
                tempValueList = []
                for valueId in range(len(parents)):
                    tempValueList.append(valueTemp % 2)
                    valueTemp = valueTemp >> 1
                tempValueList.reverse()
                CPTValue[0][0] = copy.deepcopy(tempValueList)
                CPTValue[0][0].append(0)
                CPTValue[0][1] = round(random.random(), 3)
                CPTValue[1][0] = copy.deepcopy(tempValueList)
                CPTValue[1][0].append(1)
                CPTValue[1][1] = round(1 - CPTValue[0][1], 3)
                self.CPT[attr][2].append(CPTValue[0])
                self.CPT[attr][2].append(CPTValue[1])

    # update CPT
    def __updateCPT(self):
        for nodeAttr in self.CPT:
            # get CPT value
            CPTvalues = self.CPT[nodeAttr][2]
            CPRdict = [[[], value] for value in CPTvalues]

            # get values of each attribute
            for CPRId in range(len(CPRdict)):
                tempCPRId = CPRId
                # get value
                CPRdict[CPRId][0].append(tempCPRId % (len(self.attrs[nodeAttr]) - 1))
                tempCPRId = tempCPRId // (len(self.attrs[nodeAttr]) - 1)

                for parentId in range(len(self.CPT[nodeAttr][0]) - 1, -1, -1):
                    parent = self.CPT[nodeAttr][0][parentId]
                    CPRdict[CPRId][0].append(tempCPRId % (len(self.attrs[parent]) - 1))
                    tempCPRId = tempCPRId // (len(self.attrs[parent]) - 1)
                # match value and parent attribute order
                CPRdict[CPRId][0].reverse()

            # update CPT
            self.CPT[nodeAttr][2] = CPRdict

    # update CPT
    def __updateCPT2(self):
        for nodeAttr in self.CPT:
            # get CPT value
            CPTvalues = self.CPT[nodeAttr][2]

            # build matrix and save value
            CPRdict = [[[], value] for value in CPTvalues]

            # get values of each attribute
            for CPRId in range(len(CPRdict)):
                tempCPRId = CPRId
                # get value
                CPRdict[CPRId][0].append(tempCPRId % (len(self.attrs[nodeAttr]) - 1))
                tempCPRId = tempCPRId // (len(self.attrs[nodeAttr]) - 1)

                for parentId in range(len(self.CPT[nodeAttr][0]) - 1, -1, -1):
                    parent = self.CPT[nodeAttr][0][parentId]
                    CPRdict[CPRId][0].append(tempCPRId % (len(self.attrs[parent]) - 1))
                    tempCPRId = tempCPRId // (len(self.attrs[parent]) - 1)
                # match value and parent attribute order
                CPRdict[CPRId][0].reverse()

            # update CPT
            self.CPT[nodeAttr][2] = CPRdict

    # get CPT from file
    def __getCPT(self, fileName):
        # create XMLReader
        parser = xs.make_parser()
        # turn off namespaces
        parser.setFeature(xs.handler.feature_namespaces, 0)

        # rewrite
        handler = LoadCPT()
        parser.setContentHandler(handler)
        
        # get CPT
        parser.parse(fileName)
        self.attrs = copy.deepcopy(handler.attrs)
        self.CPT = copy.deepcopy(handler.CPT)
        self.tableName = copy.deepcopy(handler.tableName)

        # update CPT
        self.__updateCPT()

        #delete objects
        del handler.attrs
        del handler.CPT
        del handler
        del parser
        gc.collect()

    # get ordered attributes in Bayesian Network
    def orderAttrCPT(self):
        # find root
        CPTvars = [attr for attr in self.CPT if(len(self.CPT[attr][0]) == 0)]
        Queue = [attr for attr in CPTvars]

        # get children
        while(len(Queue) != 0):
            # for each attribute store their children
            curAttr = Queue.pop()
            childRen = self.CPT[curAttr][1]
            Queue += childRen
            for childAttr in childRen:
                # add attribute to be next of current attribute
                if(childAttr not in CPTvars):
                    CPTvars.insert(CPTvars.index(curAttr) + 1, childAttr)
                # check the order
                elif(CPTvars.index(childAttr) < CPTvars.index(curAttr)):
                    CPTvars.pop(CPTvars.index(childAttr))
                    CPTvars.insert(CPTvars.index(curAttr) + 1, childAttr)

        return CPTvars

    # get probability according to evidence from CPT
    def getProbability(self, attrName, evidence):
        self.count += 1
        # empty evidence
        if(len(evidence) == 0):
            print("evidence should not be empty")
            exit(1)

        # calculate the id for value
        idList = [evidence[attrName]]
        for parentId in range(len(self.CPT[attrName][0]) - 1, -1, -1):
            idList.append(evidence[self.CPT[attrName][0][parentId]])
        idList.reverse()

        # get value
        for valueCell in self.CPT[attrName][2]:
            if(valueCell[0] == idList):
                return valueCell[1]

    # get factor according to current attribute and evidence
    def getFactor(self, attrName, evidence):
        # get CPT
        curCPT = []

        # get parent name id
        eviParents = {}
        for parentId, parent in enumerate(self.CPT[attrName][0]):
            # filter according evidence
            if(parent in evidence):
                eviParents[parentId] = parent

        # get current name id
        if(attrName in evidence):
            eviParents[-1] = attrName

        # get value of attributes
        parentIds = sorted(list(eviParents.keys()), reverse = True)
        for cell in self.CPT[attrName][2]:
            check = True
            for parentId in eviParents:
                if(cell[0][parentId] != evidence[eviParents[parentId]]):
                    check = False
                    break
            if(check):
                curCPT.append(copy.deepcopy(cell))
                for parentId in parentIds:
                    curCPT[-1][0].pop(parentId)

        self.count += len(curCPT)
        return curCPT

    # get Markov Blanket
    def getMarBlan(self, attrName):
        # get parents
        marBlan = [parent for parent in self.CPT[attrName][0]]

        # get children
        children = [child for child in self.CPT[attrName][1]]
        marBlan += children

        # get children's parents
        marBlan += [childParent for child in children for childParent in self.CPT[child][0] if(childParent != attrName)]
        marBlan = list(set(marBlan))

        return marBlan
        