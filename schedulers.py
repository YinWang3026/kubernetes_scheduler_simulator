from collections import deque
from typing import Tuple
from pods import *
from nodes import *
from sys import exit
import global_

class Scheduler:
    def __init__(self, quantum: int = 10000, maxprio: int = 4, preemptive: bool = False) -> None:
        self.quantum = quantum
        self.maxprio = maxprio
        self.isPreemptive = preemptive
        self.runningPods = [] # Pods currently running in nodes
        self.podQueue = deque() # Pods in the queue waiting to be scheduled
    
    def addPod(self, pod: Pod) -> None:
        # Adds Pod to queue
        print("Derived class please implement addPod()")
        exit(1)

    def schedulePods(self, myNodeList: NodeList) -> Tuple[list[Pod],list[Pod]]:
        # Schedule Pods in queue to Node
        # Return value 1 = scheduled pods
        # Return value 2 = preempted pods
        print("Derived class please implement schedulePods()")
        exit(1)

    def rmFromRunList(self, pod: Pod) -> None:
        index = 0
        while index < len(self.runningPods):
            if self.runningPods[index].name == pod.name:
                break
            index += 1
        if index == len(self.runningPods):
            print("Fatal: attempting to remove pod not in runingPods")
            exit(1)
        self.runningPods.pop(index)
    
    def addToRunList(self, pod: Pod) -> None:
        index = 0
        while index < len(self.runningPods):
            if self.runningPods[index].dynamicPrio < pod.dynamicPrio:
                break
            index += 1
        self.runningPods.insert(index, pod)
    
    def preemptPod(self, highPrioPod: Pod) -> Pod:
        if len(self.runningPods) == 0:
            return None
        for currPod in self.runningPods:
            if currPod.dynamicPrio < highPrioPod.dynamicPrio \
                and currPod.cpu + currPod.node.curCpu >= highPrioPod.cpu \
                and currPod.gpu + currPod.node.curGpu >= highPrioPod.gpu \
                and currPod.ram + currPod.node.curRam >= highPrioPod.ram \
                and currPod.preempted == False:
                return currPod
        return None
    
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

    def getRunPodStr(self) -> str:
        s = "RunningPods[%d]:" % (len(self.runningPods))
        for i in self.runningPods:
            s += i.name + " "
        return s
    
    def __repr__(self) -> str:
        return "Quantum: %d, Maxprio: %d, Preemptive: %s"\
             % (self.quantum, self.maxprio, self.isPreemptive)
        
class FCFS(Scheduler): # First Come First Served
    def __init__(self, preemptive: bool = False) -> None:
        # Does not care about quantum or maxprio, leaving as some large default
        super().__init__(preemptive=preemptive)

    def addPod(self, pod: Pod) -> None:
        # Queue needs to be sorted by Pod.stateTS and Pod.prio
        self.podQueue.append(pod)

    def schedulePods(self, myNodeList: NodeList) -> Tuple[list[Pod],list[Pod]]:
        scheduledPods = []
        preemptedPods = []
        while len(self.podQueue) > 0:
            currPod = self.podQueue.popleft()
            matchedNodes = myNodeList.getMatch(currPod, 1)
            if len(matchedNodes) > 0: # At least one Node can run this pod
                # Not sure how this going to work yet. TODO FIND A BETTER WAY TO PICK CHOSEN NODE
                chosenNode = matchedNodes[0] # There is only one node here lol
                if global_.qFlag:
                    print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                chosenNode.addPod(currPod) # Take the resource now, so that no other nodes can take the resource
                currPod.node = chosenNode # Link node to pod
                scheduledPods.append(currPod)
            else:
                # No node can run this pod
                if self.isPreemptive: # If preemptive, then try removing a pod
                    preemptedPod = self.preemptPod(currPod)
                    if preemptedPod != None:
                        preemptedPods.append(preemptedPod)
                        if global_.qFlag:
                            print("Pod [%s] w/ Prio [%d] is preempted by Pod [%s] w/ Prio [%d]" \
                                % (preemptedPod.name, preemptedPod.prio, currPod.name, currPod.prio))
                    else:
                        if global_.qFlag:
                            print("Unable to Preempt Pods for Pod [%s]" % (currPod.name))
                    # Put pod back into queue and wait ...
                    self.podQueue.appendleft(currPod)
                else: # Otherwise, put pod back into queue and wait ...
                    self.podQueue.appendleft(currPod)
                    if global_.qFlag:
                        print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
                break

        return scheduledPods, preemptedPods

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
            currPod = self.podQueue.popleft()
            matchedNodes = myNodeList.getMatch(currPod, 1)
            if len(matchedNodes) > 0: # At least one Node can run this pod
                chosenNode = matchedNodes[0] # There is only one node here lol
                if global_.qFlag:
                    print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                chosenNode.addPod(currPod) # Take the resource now, so that no other nodes can take the resource
                currPod.node = chosenNode # Link node to pod
                scheduledPods.append(currPod)
            else:
                # No node can run this pod, we just wait and try schedule this pod again later
                self.podQueue.appendleft(currPod)
                if global_.qFlag:
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
            currPod = self.podQueue.popleft()
            matchedNodes = myNodeList.getMatch(currPod, 1)
            if len(matchedNodes) > 0: # At least one Node can run this pod
                chosenNode = matchedNodes[0] # There is only one node here lol
                if global_.qFlag:
                    print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                chosenNode.addPod(currPod) # Take the resource now, so that no other nodes can take the resource
                currPod.node = chosenNode # Link node to pod
                scheduledPods.append(currPod)
            else:
                # No node can run this pod, we just wait and try schedule this pod again later
                self.podQueue.appendleft(currPod)
                if global_.qFlag:
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
            currPod = self.podQueue.popleft()
            matchedNodes = myNodeList.getMatch(currPod, 1)
            if len(matchedNodes) > 0: # At least one Node can run this pod
                chosenNode = matchedNodes[0] # There is only one node here lol
                if global_.qFlag:
                    print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                chosenNode.addPod(currPod) # Take the resource now, so that no other nodes can take the resource
                currPod.node = chosenNode # Link node to pod
                scheduledPods.append(currPod)
            else:
                # No node can run this pod, we just wait and try schedule this pod again later
                self.podQueue.appendleft(currPod)
                if global_.qFlag:
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
                if global_.qFlag:
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

                    if global_.qFlag:
                        print("Matched Pod [%s] with Node [%s]" % (currPod.name, chosenNode.name))

                    chosenNode.addPod(currPod) # Add pod to node
                    currPod.node = chosenNode # Link node to pod
                    scheduledPods.append(currPod)
                else:
                    # No node can run this pod, we just wait and try schedule this pod again later
                    notScheduledPods.append(currPod)
                    if global_.qFlag:
                        print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
            else:
                # Scheduled all the possible pods
                break
        
        while notScheduledPods:
            self.addPod(notScheduledPods.popleft()) # Put the not scheduled pods back into queue

        return scheduledPods

    def __repr__(self) -> str:
        return "Scheduler: PRIO " + super().__repr__()

# class PRIO(Scheduler): # Preemptive Priority scheduling
#     def __init__(self, maxprio: int, quantum: int) -> None:
#         super().__init__(maxprio=maxprio, quantum=quantum, preemptive=True)
    
#     def __repr__(self) -> str:
#         return "Scheduler: PREEMPT PRIO " + super().__repr__()

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
