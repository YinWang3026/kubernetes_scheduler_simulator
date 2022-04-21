from collections import deque
from enum import Enum, auto
import sys, getopt

import global_
from pods import *
from nodes import *
from schedulers import *


class Transition(Enum):
    TO_RUN = auto() 
    TO_WAIT = auto() # To waiting state
    TO_PREEMPT = auto() # Running to waiting
    TO_TERM = auto() # Termination


eventID = 0 # Global event ID tracker
class Event:
    def __init__(self, ts: int, pod: Pod, trans: Transition) -> None:
        global eventID
        self.id = eventID
        eventID += 1

        self.timeStamp = ts
        self.pod = pod
        self.transition = trans # Transition enum
    
    def __repr__(self) -> str:
        return "ID: %d, TimeStamp: %d, Pod: %s, Transition: %s" % (self.id, self.timeStamp, self.pod.name, self.transition.name)
    
class EventQueue:
    def __init__(self) -> None:
        self.queue = deque()
    
    def getEvent(self) -> Event: 
        if len(self.queue) == 0:
            return None

        return self.queue.popleft()
    
    def putEvent(self, evt: Event) -> None:
        index = 0
        while index < len(self.queue):
            if evt.timeStamp < self.queue[index].timeStamp:
                break
            index += 1
        self.queue.insert(index, evt)
    
    def getNextEvtTime(self) -> int:
        if len(self.queue) == 0:
            return None
        
        return self.queue[0].timeStamp
    
    def removeEvent(self, evt: Event) -> None:
        for i in range(0, len(self.queue)):
            if self.queue[i].id == evt.id:
                break

        del self.queue[i]

    def getEventByPod(self, pod: Pod) -> Event:
        for i in self.queue:
            if i.pod.name == pod.name:
                return i
        
        return None
    
    def __repr__(self) -> str:
        s = "Event Queue:\n"
        for i in self.queue:
            s += "\t" + i.__repr__() + "\n"
        return s


def userCallHelper():
    print('simulator.py -h -v -t -q -p <pods.txt> -n <nodes.txt> -s <scheduler> -d <node scheduler>')
    print('-p or --pfile for pod file')
    print('-n or --nfile for node file')
    print('-s or --sched for pod scheduler')
    print('-d or --nsched for node scheduler')
    print('-v for general debugging info')
    print('-q for scheduler debugging info')
    print('-t for showing simulation traces')
    print('-z for showing node traces')

def parseSchedulerInfo(arg: str) -> Scheduler:
    myScheduler = None
    arg = arg.split(":")

    preemptive = False
    try:
        preemptive = True if arg[1] == "1" else False
    except:
        preemptive = False

    quantum = 10000
    try:
        quantum = int(arg[2])
    except:
        quantum = 10000

    maxPrio = 4
    try:
        maxPrio = int(arg[3])
    except:
        maxPrio = 4

    if arg[0] == "FCFS": # FCFS:preemptive
        myScheduler = FCFS(preemptive=preemptive)
    elif arg[0] == "SRTF": # SRTF:preemptive
        myScheduler = SRTF(preemptive=preemptive)
    elif arg[0] == "SRF": # SRF:preemptive
        myScheduler = SRF(preemptive=preemptive)
    elif arg[0] == "RR": # RR:preemptive:quantum
        myScheduler = RR(quantum=quantum, preemptive=preemptive)
    elif arg[0] == "PRIO": # PRIO:preemptive:quantum:maxprio
        myScheduler = PRIO(quantum=quantum, preemptive=preemptive, maxprio=maxPrio)
    elif arg[0] == "DRF":
        myScheduler = DRF(preemptive=preemptive)
    elif arg[0] == "Lottery":
        myScheduler = Lottery(preemptive=preemptive)

    return myScheduler

def main(argv):
    pfile = ''
    nfile = ''
    myScheduler = None
    myNodeList = NodeList()
    myPodList = PodList()
    myEventQueue = EventQueue()

    try:
        opts, args = getopt.getopt(argv,"hvtqzp:n:s:d:",["help, pfile=, nfile=, sched=, nsched="])
        # getopt.getopt(args, options, [long_options])
        # ":" indicates that an argument is needed, otherwise just an option, like -h
    except getopt.GetoptError:
        userCallHelper()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            userCallHelper()
            sys.exit(1)
        elif opt in ("-p", "--pfile"):
            pfile = arg
        elif opt in ("-n", "--nfile"):
            nfile = arg
        elif opt in ("-s", "--sched"):
            myScheduler = parseSchedulerInfo(arg)
        elif opt in ("-d", "--nsched"):
            if arg == "topK":
                myNodeList = NodeListByDistance()
            elif arg == "LRP":
                myNodeList = NodeListByLRP()
            elif arg == "BRA":
                myNodeList = NodeListByBRA()
        elif opt in ("-v"):
            global_.vFlag = True
        elif opt in ("-t"):
            global_.tFlag = True
        elif opt in ("-q"):
            global_.qFlag = True
        elif opt in ("-z"):
            global_.zFlag = True
    
    if pfile == "":
        print('Missing pod file, exiting')
        sys.exit(1)
    
    if nfile == "":
        print('Missing node file, exiting')
        sys.exit(1)
    
    if myScheduler == None:
        print('Missing scheduler or used invalid name')
        sys.exit(1)
    
    if myNodeList == None:
        print('Missing node list or used invalid name')
        sys.exit(1)

    with open(pfile, 'r') as f:
        header = f.readline().strip()
        if global_.vFlag:
            print("Header: " + header)
        for line in f.readlines():
            line = line.strip().split()
            user = line[0]
            name = line[1]
            arrivalTime = int(line[2])
            work = int(line[3])
            prio = int(line[4])
            tickets = int(line[5])
            cpu = int(line[6])
            gpu = int(line[7])
            ram = int(line[8])

            p = Pod(user, name, arrivalTime, work, cpu, gpu, ram, prio, tickets, State.CREATED)
            myPodList.addPod(p)
            myEventQueue.putEvent(Event(arrivalTime, p, Transition.TO_WAIT))
 
    with open(nfile, 'r') as f:
        header = f.readline().strip()
        if global_.vFlag:
            print("Header: " + header)
        for line in f.readlines():
            line = line.strip().split()
            name = line[0]
            cpu = int(line[1])
            gpu = int(line[2])
            ram = int(line[3])

            myNodeList.addNode(Node(name, cpu, gpu, ram))
    
    if myScheduler.name == "DRF":
        myScheduler.calculate_tot_resources(myNodeList)
        
    if global_.vFlag:
        print(myPodList)
        print(myNodeList)
        print(myEventQueue)
        print(myScheduler)

    # Start simulation
    simulate(myEventQueue, myScheduler, myNodeList)
    myPodList.calcAllJct()

    print("Summary:")
    print("Pod File: %s\tNode File:%s" %(pfile, nfile))
    print(myScheduler)
    print("Unable to schedule Pods: %s" % (myScheduler.getPodQueueStr()))
    print(myPodList.getPodsBenchmarkStr())
    print(myNodeList.getUsageLogs())
    print(myNodeList.getClusterLog())
    
def simulate(myEventQueue: EventQueue, myScheduler: Scheduler, myNodeList: NodeList) -> None:
    def printStateIntro(currentTime, proc, timeInPrevState, newState):
        if global_.tFlag:
            print("currentTime: %d, podName: %s, timeInPrevState: %d, from: %s to: %s" \
                % (currentTime, proc.name, timeInPrevState, proc.state, newState))

    event = myEventQueue.getEvent()
    currentTime = -1
    if global_.tFlag:
        print("\n###################\nSimulation Start")

    # If there are events, then this simulator needs to continue running
    # Whether or not there are pods in the queue does not matter
    while (event != None):
        pod = event.pod
        eventTrans = event.transition
        currentTime = event.timeStamp
        timeInPrevState = currentTime - pod.stateTS
        event = None # Disconnect pointer to object
        myNodeList.updateClusterInfo(currentTime) # Sets current time and updates cluster usage

        if global_.tFlag:
            print(myScheduler.getRunPodStr())

        # Process events
        if eventTrans == Transition.TO_WAIT:
            printStateIntro(currentTime, pod, timeInPrevState, State.WAIT)
            # Update state info
            pod.state = State.WAIT
            pod.stateTS = currentTime
            # Add to scheduler
            myScheduler.addToQueue(pod)

        elif eventTrans == Transition.TO_RUN:
            printStateIntro(currentTime, pod, timeInPrevState, State.RUN)
            # Update state info
            pod.state = State.RUN
            pod.stateTS = currentTime
            if pod.execStartTime == -1:
                pod.execStartTime = currentTime
            pod.totalWaitTime += timeInPrevState
            myScheduler.addToRunList(pod)

            if pod.remainWork > myScheduler.quantum: #Remaining time to run is greater than the quantum
                # Create new event to preempt the proc after the quantum, put the proc to preempt
                if myScheduler.name == "Lottery":
                    myScheduler.update_comp_ticket(pod)
                myEventQueue.putEvent(Event(currentTime+myScheduler.quantum, pod, Transition.TO_PREEMPT))
                pod.remainWork -= myScheduler.quantum

            else: #Remaining time to run is smaller than the quantum
                # Create new event to fire off when proc is done, put the proc to DONE
                myEventQueue.putEvent(Event(currentTime+pod.remainWork, pod, Transition.TO_TERM))
                pod.remainWork = 0

        # No blocking in this simulation :)
        # elif eventTrans == Transition.TO_BLOCK:
            # pass

        elif eventTrans == Transition.TO_PREEMPT:
            printStateIntro(currentTime, pod, timeInPrevState, State.PREEMPT)
            # Update state info
            pod.state = State.PREEMPT
            pod.stateTS = currentTime
            pod.dynamicPrio -= 1
            pod.preempted = False
            myScheduler.rmFromRunList(pod)
            # Return resouce to node
            node = pod.node
            pod.node = None
            node.removePod(pod)
            # Add to scheduler
            myScheduler.addToQueue(pod)

        elif eventTrans == Transition.TO_TERM:
            printStateIntro(currentTime, pod, timeInPrevState, State.TERM)
            # Update proc info
            pod.state = State.TERM
            pod.stateTS = currentTime
            pod.finishTime = currentTime
            myScheduler.rmFromRunList(pod)
            # Return resouce to node
            node = pod.node
            pod.node = None
            node.removePod(pod)
            # update resource share
            if myScheduler.name == "DRF":
                myScheduler.update_res_shares(pod)
        # Get next process
        # If another event of same time, process the next event before calling scheduler
        # If there are pods in the sched q and cannot be sched, then no point of running loop, exit
        # As long as a event happened, try to schedule some pods
        if myEventQueue.getNextEvtTime() != currentTime:
            if global_.tFlag:
                print(myScheduler.getPodQueueStr())

            scheduledPods, preemptedPods = myScheduler.schedulePods(myNodeList)
            while len(scheduledPods) > 0:
                # There is a pod to run, create a new event
                myEventQueue.putEvent(Event(currentTime, scheduledPods.pop(), Transition.TO_RUN))
            while len(preemptedPods) > 0:
                # There is a pod to preempt, create a new event
                pod = preemptedPods.pop()
                futureEvent = myEventQueue.getEventByPod(pod)
                if futureEvent.timeStamp > (currentTime + 30):
                    remainingTime = futureEvent.timeStamp - (currentTime + 30)
                    pod.remainWork += remainingTime # Restore the amount of work didn't get to do
                    myEventQueue.removeEvent(futureEvent)
                    futureEvent = None
                    myEventQueue.putEvent(Event(currentTime+30, pod, Transition.TO_PREEMPT)) # Has 30 sec to run before termination

        # Get the next event
        event = myEventQueue.getEvent()
    
    myNodeList.updateClusterInfo(currentTime) # Sets current time and updates cluster usage
    
    if global_.tFlag:
        print("\nSimulation End\n####################################\n")

if __name__ == "__main__":
   main(sys.argv[1:])
