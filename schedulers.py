from collections import deque
from pods import *
from nodes import *
from sys import exit
import global_

class Scheduler:
    def __init__(self, quantum: int = 10000, maxprio: int = 4, preemptive: bool = False) -> None:
        self.quantum = quantum
        self.maxprio = maxprio
        self.isPreemptive = preemptive
        self.podQueue = deque()
    
    def addPod(self, pod: Pod) -> None: 
        print("Derived class please implement addPod()")
        exit(1)

    def schedulePods(self, nodeList: NodeList) -> list[Pod]:
        print("Derived class please implement schedulePod()")
        exit(1)
    
    def getQueueLength(self) -> int:
        return len(self.podQueue)

    def getQuantum(self) -> int:
        return self.quantum
    
    def getMaxprio(self) -> int:
        return self.maxprio
    
    def getPodQueueStr(self) -> str:
        s = "SchedQ[%d]:" % (len(self.podQueue))
        for i in self.podQueue:
            s += i.name + " "
        return s
    
    def __repr__(self) -> str:
        return "Quantum: %d, Maxprio: %d, Preemption: %s"\
             % (self.quantum, self.maxprio, self.isPreemptive)
        
class FCFS(Scheduler): # First Come First Served
    def __init__(self) -> None:
        super().__init__()

    def addPod(self, pod: Pod) -> None:
        self.podQueue.append(pod)

    def schedulePods(self, myNodeList: NodeList) -> list[Pod]:
        # Not sure how this going to work yet
        scheduledPods = []
        while len(self.podQueue) > 0:
            currPod = self.podQueue[0]
            matchedNodes = myNodeList.getMatch(currPod, 1)
            if len(matchedNodes) > 0:
                # At least one Node can run this pod
                chosenNode = matchedNodes[0] # There is only one node here lol

                if global_.tFlag:
                    print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                chosenNode.addPod(currPod) # Add pod to node
                currPod.node = chosenNode # Link node to pod
                self.podQueue.popleft() # Remove this pod from queue
                scheduledPods.append(currPod)
            else:
                # No node can run this pod, we just wait and try schedule this pod again later
                if global_.tFlag:
                    print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
                break

        return scheduledPods

    def __repr__(self) -> str:
        return "Scheduler: FCFS " + super().__repr__()
    
class SRTF(Scheduler): # Shortest Remaining Time First
    def __init__(self) -> None:
        super().__init__()

    def addPod(self, pod: Pod) -> None: # put smallest usage time 
        addloc = -1
        for i in range(len(self.podQueue)):
            if pod.remainWork < self.podQueue[i].remainWork:
                self.podQueue.insert(i, pod)
                addloc = i
                break

        if addloc == -1:
            self.podQueue.append(pod)

    def schedulePods(self, myNodeList: NodeList) -> list[Pod]:
        # Not sure how this going to work yet
        scheduledPods = []
        while len(self.podQueue) > 0:
            currPod = self.podQueue[0]
            matchedNodes = myNodeList.getMatch(currPod, 1)
            if len(matchedNodes) > 0:
                # At least one Node can run this pod
                chosenNode = matchedNodes[0] # There is only one node here lol

                if global_.tFlag:
                    print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                chosenNode.addPod(currPod) # Add pod to node
                currPod.node = chosenNode # Link node to pod
                self.podQueue.popleft() # Remove this pod from queue
                scheduledPods.append(currPod)
            else:
                # No node can run this pod, we just wait and try schedule this pod again later
                if global_.tFlag:
                    print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
                break

        return scheduledPods

    def __repr__(self) -> str:
        return "SRTF"

class SRF(Scheduler): # Smallest Resource First
    def __init__(self) -> None:
        super().__init__()

    def addPod(self, pod: Pod) -> None:
        addloc = -1

        curr_score = (pod.cpu)**2 + (pod.gpu)**2 + (pod.ram)**2
        for i in range(len(self.podQueue)):
            aggregate_score = (self.podQueue[i].cpu)**2 + (self.podQueue[i].gpu)**2 + (self.podQueue[i].ram)**2

            if curr_score < aggregate_score:
                self.podQueue.insert(i, pod)
                addloc = i
                break

        if addloc == -1:
            self.podQueue.append(pod)
        

    def schedulePods(self, myNodeList: NodeList) -> list[Pod]:
        # Not sure how this going to work yet
        scheduledPods = []
        while len(self.podQueue) > 0:
            currPod = self.podQueue[0]
            matchedNodes = myNodeList.getMatch(currPod, 1)
            if len(matchedNodes) > 0:
                # At least one Node can run this pod
                chosenNode = matchedNodes[0] # There is only one node here lol

                if global_.tFlag:
                    print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                chosenNode.addPod(currPod) # Add pod to node
                currPod.node = chosenNode # Link node to pod
                self.podQueue.popleft() # Remove this pod from queue
                scheduledPods.append(currPod)
            else:
                # No node can run this pod, we just wait and try schedule this pod again later
                if global_.tFlag:
                    print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
                break

        return scheduledPods

    def __repr__(self) -> str:
        return "SRF"

class RR(Scheduler): # Round Robin
    def __init__(self, quantum: int) -> None:
        super().__init__(quantum=quantum)

    def addPod(self, pod: Pod) -> None:
        self.podQueue.append(pod)

    def schedulePods(self, myNodeList: NodeList) -> list[Pod]:
        # Not sure how this going to work yet
        scheduledPods = []
        while len(self.podQueue) > 0:
            currPod = self.podQueue[0]
            matchedNodes = myNodeList.getMatch(currPod, 1)
            if len(matchedNodes) > 0:
                # At least one Node can run this pod
                chosenNode = matchedNodes[0] # There is only one node here lol

                if global_.tFlag:
                    print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                chosenNode.addPod(currPod) # Add pod to node
                currPod.node = chosenNode # Link node to pod
                self.podQueue.popleft() # Remove this pod from queue
                scheduledPods.append(currPod)
            else:
                # No node can run this pod, we just wait and try schedule this pod again later
                if global_.tFlag:
                    print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
                break

        return scheduledPods

    def __repr__(self) -> str:
        return "Scheduler: RR " + super().__repr__()

class PRIO(Scheduler): # Priority scheduling
    def __init__(self, maxprio: int, quantum: int) -> None:
        super().__init__(maxprio=maxprio, quantum=quantum)
        self.expireQ = []
        self.activeQ = []

        for _ in range(self.maxprio):
            self.activeQ.append(deque())
            self.expireQ.append(deque())

    def addPod(self, pod: Pod) -> None:
        if pod.dynamicPrio == -1: #when dynamic priority reaches -1, add to the expire queue
            pod.dynamicPrio = pod.prio 
            self.expireQ[pod.dynamicPrio-1].append(pod)
        else: #add to active queue
            self.activeQ[pod.dynamicPrio-1].append(pod)

    def schedulePods(self, myNodeList: NodeList) -> list[Pod]:
        scheduledPods = []
        notScheduledPods = deque()

        while True:
            # Try to get a pod for scheduling
            currPod = None
            for i in range(self.maxprio - 1, -1, -1):
                if len(self.activeQ[i]) > 0:
                    currPod = self.activeQ[i].popleft()
                    break

            if currPod == None:
                tmp = self.activeQ
                self.activeQ = self.expireQ
                self.expireQ = tmp
                if global_.tFlag:
                    print("Swapped active and expire Queue")

                for i in range(self.maxprio - 1, -1, -1):
                    if len(self.activeQ[i]) > 0:
                        currPod = self.activeQ[i].popleft()
                        break

            # Find a matching pod
            if currPod != None:
                matchedNodes = myNodeList.getMatch(currPod, 1) # Find 1 matching node
                if len(matchedNodes) > 0:
                    # At least one Node can run this pod
                    chosenNode = matchedNodes[0] # There is only one node here lol

                    if global_.tFlag:
                        print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                    chosenNode.addPod(currPod) # Add pod to node
                    currPod.node = chosenNode # Link node to pod
                    scheduledPods.append(currPod)
                else:
                    # No node can run this pod, we just wait and try schedule this pod again later
                    notScheduledPods.append(currPod)
                    if global_.tFlag:
                        print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
            else:
                # Scheduled all the possible pods
                break
        
        while notScheduledPods:
            self.addPod(notScheduledPods.popleft()) # Put the not scheduled pods back into queue

        return scheduledPods

    def __repr__(self) -> str:
        return "Scheduler: PRIO " + super().__repr__()

# class DRF(Scheduler): # DRF
#     def __init__(self) -> None:
#         super().__init__()

#     def addPod(self, pod: Pod) -> None:
#         pass

#     def __repr__(self) -> str:
#         return "Scheduler: DRF " + super().__repr__()

# class Lottery(Scheduler): # Random
#     def __init__(self) -> None:
#         self.queue = deque()

#     def addPod(self, pod: Pod) -> None:
#         pass
                
#     def __repr__(self) -> str:
#         return "Lottery" + super().__repr__()

# class OurNovelSolution(Scheduler):
#     def __init__(self) -> None:
#         self.queue = deque()

#     def addPod(self, pod: Pod) -> None:
#         pass
                
#     def __repr__(self) -> str:
#         return "Lottery" + super().__repr__()
