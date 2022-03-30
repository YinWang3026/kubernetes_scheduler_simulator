from pods import *
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

        # Pods running on this node
        self.podSet = set() # For O(1) remove and add, but can use other data struct if needed
    
    def addPod(self, pod: Pod) -> None:
        if global_.tFlag:
            print("Adding Pod [%s] to Node [%s]\n\tCPU: %d, GPU: %d, RAM: %d" \
                % (pod.name, self.name, self.curCpu, self.curGpu, self.curRam))
        self.curCpu -= pod.cpu
        if self.curCpu < 0:
            print("Node %s CPU went negative" % (self.name))
            sys.exit(1)
        self.curGpu -= pod.gpu
        if self.curGpu < 0:
            print("Node %s GPU went negative" % (self.name))
            sys.exit(1)
        self.curRam -= pod.ram
        if self.curRam < 0:
            print("Node %s RAM went negative" % (self.name))
            sys.exit(1)

        self.podSet.add(pod)
        if global_.tFlag:
            print("\tCPU: %d, GPU: %d, RAM: %d" \
                % (self.curCpu, self.curGpu, self.curRam))

    def removePod(self, pod: Pod) -> None:
        if global_.tFlag:
            print("Removing Pod [%s] from Node [%s]\n\tCPU: %d, GPU: %d, RAM: %d" \
                % (pod.name, self.name, self.curCpu, self.curGpu, self.curRam))
        self.curCpu += pod.cpu
        self.curGpu += pod.gpu
        self.curRam += pod.ram
        self.podSet.discard(pod)
        if global_.tFlag:
            print("\tCPU: %d, GPU: %d, RAM: %d" \
                % (self.curCpu, self.curGpu, self.curRam))
    
    def __repr__(self) -> str:
        return "Name: %s, CPU: %d, GPU: %d, RAM: %d" \
            % (self.name, self.cpu, self.gpu, self.ram)

    def getCurResourceStr(self) -> str:
        return "Name: %s, CPU: %d, GPU: %d, RAM: %d" \
            % (self.name, self.curCpu, self.curGpu, self.curRam)
    
    def getPodListStr(self) -> str:
        s = "Node[%s] Pod List: " % (self.name)
        for pod in self.podSet:
            s += pod.name + " "
        return s

class NodeList:
    def __init__(self) -> None:
        self.nodes = []

    def addNode(self, node: Node) -> None:
        self.nodes.append(node)

    def getMatch(self, pod: Pod, n: int) -> list[Node]:
        # Return a list of nodes that can run the given pod
        # Can use derived class and a custom policy
        # Default policy, return the first n nodes that has enough resource to run this pod
        matchedNodes = []
        count = 0

        for i in self.nodes:
            if i.curCpu >= pod.cpu and i.curGpu >= pod.gpu and i.curRam >= pod.ram:
                matchedNodes.append(i)
                count += 1
                if count == n:
                    break
        
        return matchedNodes

    def __repr__(self) -> str:
        s = "Node List:\n"
        for i in self.nodes:
            s += "\t" + i.__repr__() + "\n"
        return s

# Custom getMatch policies
class NodeListSecretPolicy(NodeList):
    def __init__(self) -> None:
        super().__init__()
    
    def getMatch(self, pod: Pod) -> list[Node]:
        # return super().getMatch(pod)
        # SuPer secret policy
        pass