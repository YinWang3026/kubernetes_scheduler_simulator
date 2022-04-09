from sys import exit
from math import sqrt
from pods import *
import heapq
import global_


class Node:
    def __init__(self, name: str, cpu: int, gpu: int, ram: int) -> None:
        # Basic info - DOES NOT CHANGE
        self.name = name
        self.cpu = cpu
        self.gpu = gpu
        self.ram = ram

        # Remaining resource
        self.curCpu = cpu
        self.curGpu = gpu
        self.curRam = ram

        # Tracking system usage
        self.currentTime = 0
        self.log = [] # Tuple of (start, end, pod.name, cpu, gpu, ram usage)
        self.admission = {} # Map tracking pod.name starting time on this node 

        # Pods running on this node, not needed as self.admission can be used to track whats current on this Node
        # self.podSet = set() # For O(1) remove and add, but can use other data struct if needed
    
    def addPod(self, pod: Pod) -> None:
        if global_.zFlag:
            print("Time [%d] Adding Pod [%s] to Node [%s]\n\tBefore CPU: %d, GPU: %d, RAM: %d" \
                % (self.currentTime, pod.name, self.name, self.curCpu, self.curGpu, self.curRam))
        self.curCpu -= pod.cpu
        if self.curCpu < 0:
            print("Node %s CPU went negative" % (self.name))
            exit(1)
        self.curGpu -= pod.gpu
        if self.curGpu < 0:
            print("Node %s GPU went negative" % (self.name))
            exit(1)
        self.curRam -= pod.ram
        if self.curRam < 0:
            print("Node %s RAM went negative" % (self.name))
            exit(1)

        self.admission[pod.name] = self.currentTime
        if global_.zFlag:
            print("\tAfter CPU: %d, GPU: %d, RAM: %d" \
                % (self.curCpu, self.curGpu, self.curRam))

    def removePod(self, pod: Pod) -> None:
        if global_.zFlag:
            print("Time [%d] Removing Pod [%s] from Node [%s]\n\tBefore CPU: %d, GPU: %d, RAM: %d" \
                % (self.currentTime, pod.name, self.name, self.curCpu, self.curGpu, self.curRam))
        
        if pod.name not in self.admission:
            print("Removing non-existant pod [%s]" % (pod.name))
            exit(1)

        self.curCpu += pod.cpu
        self.curGpu += pod.gpu
        self.curRam += pod.ram

        # (startTime, endTime, cpu, gpu, ram usage)
        usage = (self.admission[pod.name], self.currentTime, pod.name, pod.cpu, pod.gpu, pod.ram)
        self.log.append(usage)
        
        del self.admission[pod.name]

        if global_.zFlag:
            print("\tAfter CPU: %d, GPU: %d, RAM: %d" \
                % (self.curCpu, self.curGpu, self.curRam))
    
    def __repr__(self) -> str:
        return "Name: %s, CPU: %d, GPU: %d, RAM: %d" \
            % (self.name, self.cpu, self.gpu, self.ram)

    def getCurResourceStr(self) -> str:
        return "Name: %s, CPU: %d, GPU: %d, RAM: %d" \
            % (self.name, self.curCpu, self.curGpu, self.curRam)
    
    def getPodListStr(self) -> str:
        s = "Node[%s] Pod List: " % (self.name)
        for pod in self.admission.values():
            s += pod.name + " "
        return s
    
    def getUsageLogStr(self) -> str:
        s = "Node[%s] Usage Log:" % (self.name)
        for i in self.log:
            s += " " + str(i)
        return s

class NodeList:
    def __init__(self) -> None:
        self.nodes = []

    def addNode(self, node: Node) -> None:
        self.nodes.append(node)
    
    def setCurrentTime(self, currentTime: int) -> None:
        for i in self.nodes:
            i.currentTime = currentTime

    def getMatch(self, pod: Pod, k: int) -> list[Node]:
        # Return a list of nodes that can run the given pod
        # Can use derived class and a custom policy
        # Default policy, return the first n nodes that has enough resource to run this pod
        matchedNodes = []
        count = 0
        if global_.zFlag:
            print("Matching Pod [%s] with nodes" % (pod.name))
        for i in self.nodes:
            if i.curCpu >= pod.cpu and i.curGpu >= pod.gpu and i.curRam >= pod.ram:
                matchedNodes.append(i)
                count += 1
                if count == k:
                    break
        
        return matchedNodes

    def __repr__(self) -> str:
        s = "Node List:\n"
        for i in self.nodes:
            s += "\t" + i.__repr__() + "\n"
        return s

    def getUsageLogs(self) -> str:
        s = "Usage Log: \n"
        for i in self.nodes:
            s += "\t" + i.getUsageLogStr() + "\n"
        return s

# Custom getMatch policies
class NodeListByDistance(NodeList):
    def __init__(self) -> None:
        super().__init__()
    
    def getMatch(self, pod: Pod, k: int) -> list[Node]:
        # Finds at most top k closest (in terms of resource) node to the pod
        potentialMatches = [] # Max heap

        for i in self.nodes:
            if i.curCpu >= pod.cpu and i.curGpu >= pod.gpu and i.curRam >= pod.ram:
                distance = sqrt((i.curCpu-pod.cpu)**2 + (i.curGpu-pod.cpu)**2 + (i.curRam-pod.ram)**2)
                heapq.heappush(potentialMatches, (-distance, i))
                if len(potentialMatches) > k:
                    # Remove the largest distance node
                    heapq.heappop(potentialMatches)
        
        matchedNodes = []
        while len(potentialMatches) > 0:
            matchedNodes.append(heapq.heappop(potentialMatches)[1])
        
        # Reverse list so that it is sorted from smallest distance to largest distance
        return matchedNodes[::-1]
