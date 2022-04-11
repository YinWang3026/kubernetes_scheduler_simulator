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
    
    def addToQueue(self, pod: Pod) -> None:
        # Adds Pod to queue
        print("Derived class please implement addToQueue()")
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
                currPod.preempted = True
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
    def __init__(self, preemptive: bool) -> None:
        # Does not care about quantum or maxprio, leaving as some large default
        super().__init__(preemptive=preemptive)

    def addToQueue(self, pod: Pod) -> None:
        # Queue needs to be sorted by Pod.stateTS and Pod.prio
        index = 0
        while index < len(self.podQueue):
            if pod.stateTS <= self.podQueue[index].stateTS:
                break
            index += 1
        while index < len(self.podQueue) and pod.stateTS == self.podQueue[index].stateTS:
            if pod.prio > self.podQueue[index].prio:
                break
            index += 1
        
        self.podQueue.insert(index, pod)

    def schedulePods(self, myNodeList: NodeList) -> Tuple[list[Pod],list[Pod]]:
        if len(self.podQueue) == 0:
            return [], []

        scheduledPods = []
        preemptedPods = []
        notScheduledPods = []
        currentTime = self.podQueue[0].stateTS
        while len(self.podQueue) > 0 and self.podQueue[0].stateTS == currentTime:
            # Try to schedule all the pods of current time
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
                    notScheduledPods.append(currPod)
                else: # Otherwise, put pod back into queue and wait ...
                    notScheduledPods.append(currPod)
                    if global_.qFlag:
                        print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
    
        while len(notScheduledPods) > 0:
            self.addToQueue(notScheduledPods.pop())

        return scheduledPods, preemptedPods

    def __repr__(self) -> str:
        return "Scheduler: FCFS " + super().__repr__()
    
class SRTF(Scheduler): # Shortest Remaining Time First
    def __init__(self, preemptive: bool) -> None:
        super().__init__(preemptive=preemptive)

    def addToQueue(self, pod: Pod) -> None: # put smallest usage time 
        # Queue needs to be sorted by Pod.remainingWork and Pod.prio
        index = 0
        while index < len(self.podQueue):
            if pod.remainWork <= self.podQueue[index].remainWork:
                break
            index += 1
        while index < len(self.podQueue) and pod.remainWork == self.podQueue[index].remainWork:
            if pod.prio > self.podQueue[index].prio:
                break
            index += 1
        
        self.podQueue.insert(index, pod)

    def schedulePods(self, myNodeList: NodeList) -> Tuple[list[Pod],list[Pod]]:
        if len(self.podQueue) == 0:
            return [], []

        scheduledPods = []
        preemptedPods = []
        notScheduledPods = []
        smallestWork = self.podQueue[0].remainWork
        while len(self.podQueue) > 0 and self.podQueue[0].remainWork == smallestWork:
            # Try to schedule all the pods of current time
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
                    notScheduledPods.append(currPod)
                else: # Otherwise, put pod back into queue and wait ...
                    notScheduledPods.append(currPod)
                    if global_.qFlag:
                        print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
    
        while len(notScheduledPods) > 0:
            self.addToQueue(notScheduledPods.pop())

        return scheduledPods, preemptedPods

    def __repr__(self) -> str:
        return "Scheduler: SRTF " + super().__repr__()

class SRF(Scheduler): # Smallest Resource First
    def __init__(self, preemptive: bool) -> None:
        super().__init__(preemptive=preemptive)

    def addToQueue(self, pod: Pod) -> None:
        index = 0
        currScore = (pod.cpu)**2 + (pod.gpu)**2 + (pod.ram)**2
        while index < len(self.podQueue):
            aggregateScore = (self.podQueue[index].cpu)**2 + (self.podQueue[index].gpu)**2 + (self.podQueue[index].ram)**2
            if currScore <= aggregateScore:
                break
            index += 1

        while index < len(self.podQueue):
            aggregateScore = (self.podQueue[index].cpu)**2 + (self.podQueue[index].gpu)**2 + (self.podQueue[index].ram)**2
            if currScore == aggregateScore:
                if pod.prio > self.podQueue[index].prio:
                    break
                index += 1
            else:
                break
        
        self.podQueue.insert(index, pod)
        

    def schedulePods(self, myNodeList: NodeList) -> Tuple[list[Pod],list[Pod]]:
        if len(self.podQueue) == 0:
            return [], []

        scheduledPods = []
        preemptedPods = []
        notScheduledPods = []
        currScore = (self.podQueue[0].cpu)**2 + (self.podQueue[0].gpu)**2 + (self.podQueue[0].ram)**2
        while len(self.podQueue) > 0:
            aggregateScore = (self.podQueue[0].cpu)**2 + (self.podQueue[0].gpu)**2 + (self.podQueue[0].ram)**2
            if currScore == aggregateScore: # Schedule every pod with the same smallest score
                # Try to schedule all the pods of current time
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
                        notScheduledPods.append(currPod)
                    else: # Otherwise, put pod back into queue and wait ...
                        notScheduledPods.append(currPod)
                        if global_.qFlag:
                            print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
            else:
                break
    
        while len(notScheduledPods) > 0:
            self.addToQueue(notScheduledPods.pop())

        return scheduledPods, preemptedPods

    def __repr__(self) -> str:
        return "Scheduler: SRF " + super().__repr__()

class RR(FCFS): # Round Robin
    def __init__(self, quantum: int, preemptive: bool) -> None:
        # FCFS with a quantum lol
        super().__init__(preemptive=preemptive)
        self.quantum = quantum

    def __repr__(self) -> str:
        return "Scheduler: RR " + super().__repr__()

class PRIO(Scheduler): # Priority scheduling
    def __init__(self, quantum: int, maxprio: int, preemptive: bool) -> None:
        super().__init__(maxprio=maxprio, quantum=quantum, preemptive=preemptive)
        self.expireQ = []
        self.activeQ = []

        for _ in range(self.maxprio):
            self.activeQ.append(deque())
            self.expireQ.append(deque())
    
    def getPodQueueStr(self) -> str:
        s = "Prio SchedQ:"
        s += "\n\tActive Queue:\n"
        for q in range(0, len(self.activeQ)):
            s += "\t\t" + "[%d] " % (q)
            for i in self.activeQ[q]:
                s += i.name + " "
        
        s += "\n\tExpire Queue:\n"
        for q in range(0, len(self.expireQ)):
            s += "\t\t" + "[%d] " % (q)
            for i in self.expireQ[q]:
                s += i.name + " "
        return s

    def addToQueue(self, pod: Pod) -> None:
        if pod.dynamicPrio == -1: #when dynamic priority reaches -1, add to the expire queue
            pod.dynamicPrio = pod.prio 
            self.expireQ[pod.dynamicPrio-1].append(pod)
        else: #add to active queue
            self.activeQ[pod.dynamicPrio-1].append(pod)

    def schedulePods(self, myNodeList: NodeList) -> Tuple[list[Pod],list[Pod]]:
        scheduledPods = []
        preemptedPods = []
        notScheduledPods = []

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
                        notScheduledPods.append(currPod)
                    else: # Otherwise, put pod back into queue and wait ...
                        notScheduledPods.append(currPod)
                        if global_.qFlag:
                            print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
            else:
                # Scheduled all the possible pods
                break
        
        while notScheduledPods:
            self.addToQueue(notScheduledPods.pop()) # Put the not scheduled pods back into queue

        return scheduledPods, preemptedPods

    def __repr__(self) -> str:
        return "Scheduler: PRIO " + super().__repr__()

class DRF(Scheduler): # DRF
    def __init__(self, nodelist: NodeList) -> None:
        super().__init__()
        self.tot_cpu = 0
        self.tot_gpu = 0
        self.tot_ram = 0

        for node in nodelist:
            self.tot_cpu += node.cpu
            self.tot_gpu += node.gpu
            self.tot_ram += node.ram

        self.res_shares = dict() #resource share per user

    def addPod(self, pod: Pod) -> None:
        addloc = -1

        if pod.user is not in self.res_shares: #cur dominant resource share is zero
            self.res_shares[pod.user] = [0, 0, 0] #cpu gpu ram
            self.podQueue.insert(0, pod) #add to the front
            addloc = 0

        else:
            curr_cpu = self.res_shares[pod.user][0]
            curr_gpu = self.res_shares[pod.user][1]
            curr_ram = self.res_shares[pod.user][2]
            curr_dominant_share = max(curr_cpu / self.tot_cpu, curr_gpu / self.tot_gpu, curr_ram / self.tot_ram)

            for i in range(len(self.podQueue)):
                next_cpu = self.res_shares[self.podQueue[i].user][0]
                next_gpu = self.res_shares[self.podQueue[i].user][1]
                next_ram = self.res_shares[self.podQueue[i].user][2]

                next_dominant_share = max(next_cpu / self.tot_cpu, next_gpu / self.tot_gpu, next_ram / self.tot_ram)
                
                if curr_dominant_share < next_dominant_share:
                    self.podQueue.insert(i, pod)
                    addloc = i
                    break

        if addloc == -1:
            self.podQueue.append(pod)

    def schedulePods(self, myNodeList: NodeList) -> Tuple[list[Pod],list[Pod]]:
        if len(self.podQueue) == 0:
            return [], []

        scheduledPods = []
        preemptedPods = []
        notScheduledPods = []
        currentTime = self.podQueue[0].stateTS
        while len(self.podQueue) > 0 and self.podQueue[0].stateTS == currentTime:
            # Try to schedule all the pods of current time
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

                #update current resource shares
                self.res_shares[currPod.user][0] += currPod.cpu
                self.res_shares[currPod.user][1] += currPod.gpu
                self.res_shares[currPod.user][2] += currPod.ram
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
                    notScheduledPods.append(currPod)
                else: # Otherwise, put pod back into queue and wait ...
                    notScheduledPods.append(currPod)
                    if global_.qFlag:
                        print("Unable to Match Pod [%s] with Nodes" % (currPod.name))
    
        while len(notScheduledPods) > 0:
            self.addToQueue(notScheduledPods.pop())

        return scheduledPods, preemptedPods

    def __repr__(self) -> str:
        return "Scheduler: DRF " + super().__repr__()


# class Lottery(Scheduler): # Random
#     def __init__(self) -> None:
#         self.queue = deque()

#     def addToQueue(self, pod: Pod) -> None:
#         pass
                
#     def __repr__(self) -> str:
#         return "Lottery" + super().__repr__()

# class OurNovelSolution(Scheduler):
#     def __init__(self) -> None:
#         self.queue = deque()

#     def addToQueue(self, pod: Pod) -> None:
#         pass
                
#     def __repr__(self) -> str:
#         return "Lottery" + super().__repr__()
