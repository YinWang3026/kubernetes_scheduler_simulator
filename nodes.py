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
    
    def __lt__(self, nextnode):
        return self.name < nextnode.name

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
        # Cluster node list
        self.nodes = []

        # Basic info, does not change
        self.totalCpu = 0
        self.totalGpu = 0
        self.totalRam = 0

        # Log 
        # Maps (currentTime) -> (cpu usage, gpu usage, ram usage)
        self.log = {} 

    def addNode(self, node: Node) -> None:
        self.totalCpu += node.cpu
        self.totalGpu += node.gpu
        self.totalRam += node.ram
        self.nodes.append(node)
    
    def updateClusterInfo(self, currentTime: int) -> None:
        cpuUsed = 0
        gpuUsed = 0
        ramUsed = 0
        for i in self.nodes:
            i.currentTime = currentTime
            cpuUsed += (i.cpu - i.curCpu)
            gpuUsed += (i.gpu - i.curGpu)
            ramUsed += (i.ram - i.curRam)
        self.log[currentTime] = (cpuUsed, gpuUsed, ramUsed)

    def getMatch(self, pod: Pod, k: int) -> list[Node]:
        # Return a list of nodes that can run the given pod
        # Can use derived class and a custom policy
        # Default policy, return the first n nodes that has enough resource to run this pod
        
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

    def __repr__(self) -> str:
        s = "Node List:\n"
        for i in self.nodes:
            s += "\t" + i.__repr__() + "\n"
        s += "\tTotal CPU: %d\n" % (self.totalCpu)
        s += "\tTotal GPU: %d\n" % (self.totalGpu)
        s += "\tTotal RAM: %d\n" % (self.totalRam)
        return s

    def getUsageLogs(self) -> str:
        s = "Node Usage Log:\n"
        for i in self.nodes:
            s += "\t" + i.getUsageLogStr() + "\n"
        return s
    
    def getClusterLog(self) -> str:
        s = "Cluster Log:\n"
        s += "time,cpuUsed,gpuUsed,ramUsed,cpuPercent,gpuPercent,ramPercent\n"
        for time in sorted(self.log.keys()):
            cpu, gpu, ram = self.log[time]
            s += "%d,%d,%d,%d,%.2f,%.2f,%.2f\n" \
            % (time, cpu, gpu, ram, cpu/self.totalCpu, gpu/self.totalGpu, ram/self.totalRam)
        
        return s

class NodeListByLRP(NodeList): #LeastRequestedPriority
    def __init__(self) -> None:
        super().__init__()

    def addNode(self, node: Node) -> None:
        self.nodes.append(node)

    def getMatch(self, pod: Pod, k: int) -> list[Node]:
        #favors nodes with fewer requested resources
        potentialMatches = [] # Max heap

        for i in self.nodes:
            if i.curCpu >= pod.cpu and i.curGpu >= pod.gpu and i.curRam >= pod.ram:
                score = ((i.curCpu * 10 / i.cpu) + (i.curGpu * 10 / i.gpu) + (i.curRam * 10 / i.ram)) / 3
                heapq.heappush(potentialMatches, (-score, i))
                if len(potentialMatches) > k:
                    # Remove the largest usage rate node
                    heapq.heappop(potentialMatches)
        
        matchedNodes = []
        while len(potentialMatches) > 0:
            matchedNodes.append(heapq.heappop(potentialMatches)[1])

        return matchedNodes[::-1]


class NodeListByBRA(NodeList): #BalancedResourceAllocation, always used with LeastRequestedPriority
    def __init__(self) -> None:
        super().__init__()

    def addNode(self, node: Node) -> None:
        self.nodes.append(node)
    
    def getBRAScore(self, pod:Pod, node:Node) -> float:
        cpuFraction = pod.cpu / node.curCpu
        gpuFraction = pod.gpu / node.curGpu
        ramFraction = pod.ram / node.curRam

        distance = sqrt((node.curCpu-pod.cpu)**2 + (node.curGpu-pod.cpu)**2 + (node.curRam-pod.ram)**2)
        bra_score = 10 - distance*10

        return bra_score

    def getMatch(self, pod: Pod, k: int) -> list[Node]:
        #favors nodes with balanced resource usage rate
        potentialMatches = []
        
        #First priority : favors nodes with fewer requested resources
        for i in self.nodes:
            if i.curCpu >= pod.cpu and i.curGpu >= pod.gpu and i.curRam >= pod.ram:
                lrpscore = ((i.curCpu * 10 / i.cpu) + (i.curGpu * 10 / i.gpu) + (i.curRam * 10 / i.ram)) / 3
                brascore = self.getBRAScore(pod, i) #Second priority : favors node with higher bra score
                heapq.heappush(potentialMatches, (-lrpscore, brascore, i))
                if len(potentialMatches) > k:
                    # Remove the largest usage rate node
                    heapq.heappop(potentialMatches)

        matchedNodes = []
        while len(potentialMatches) > 0:
            matchedNodes.append(heapq.heappop(potentialMatches)[2])

        return matchedNodes[::-1]