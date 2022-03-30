from collections import deque
from enum import Enum, auto
from random import randint
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

    def getEventByPod(self, pod: Pod) -> int:
        for i in range(0, len(self.queue)):
            if self.queue[i].pod.name == pod.name:
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
    print('-q for printing scheduler queue')
    print('-t for showing simulation traces')

def main(argv):
    pfile = ''
    nfile = ''
    myScheduler = None
    myNodeList = NodeList()
    myPodList = PodList()
    myEventQueue = EventQueue()

    try:
        opts, args = getopt.getopt(argv,"hvtqp:n:s:d:",["help, pfile=, nfile=, sched=, nsched="])
        # getopt.getopt(args, options, [long_options])
        # ":" indicates that an argument is needed, otherwise just an option, like -h
    except getopt.GetoptError:
        userCallHelper()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            userCallHelper()
            sys.exit()
        elif opt in ("-p", "--pfile"):
            pfile = arg
        elif opt in ("-n", "--nfile"):
            nfile = arg
        elif opt in ("-s", "--sched"):
            if arg == "FCFS":
                myScheduler = FCFS()
            elif arg == "SRTF":
                myScheduler = SRTF()
            elif arg == "SRF":
                myScheduler = SRF()
            # elif arg == "Lottery":
            #     myScheduler = Lottery()
        elif opt in ("-v"):
            global_.vFlag = True
        elif opt in ("-t"):
            global_.tFlag = True
        elif opt in ("-q"):
            global_.qFlag = True
    
    if pfile == "":
        print('Missing pod file, exiting')
        sys.exit(1)
    
    if nfile == "":
        print('Missing node file, exiting')
        sys.exit(1)
    
    if myScheduler == None:
        print('Missing scheduler or used invalid name')
        sys.exit(1)

    with open(pfile, 'r') as f:
        header = f.readline().strip()
        if global_.vFlag:
            print("Header: " + header)
        for line in f.readlines():
            line = line.strip().split()
            name = line[0]
            arrivalTime = int(line[1])
            work = int(line[2])
            prio = int(line[3])
            tickets = int(line[4])
            cpu = int(line[5])
            gpu = int(line[6])
            ram = int(line[7])

            p = Pod(name, arrivalTime, work, cpu, gpu, ram, prio, tickets, State.CREATED)
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
    
    if global_.vFlag:
        print(myPodList)
        print(myNodeList)
        print(myEventQueue)
        print(myScheduler)

    # Start simulation
    simulate(myEventQueue, myScheduler, myNodeList)

    if global_.vFlag:
        print(myPodList.getPodsBenchmarkStr())
    
def simulate(myEventQueue: EventQueue, myScheduler: Scheduler, myNodeList: NodeList) -> None:
    def printStateIntro(currentTime, proc, timeInPrevState, newState):
        if global_.tFlag:
            print("currentTime: %d, podName: %s, timeInPrevState: %d, from: %s to: %s" \
                % (currentTime, proc.name, timeInPrevState, proc.state, newState))

    event = myEventQueue.getEvent()

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

        # Process events
        if eventTrans == Transition.TO_WAIT:
            printStateIntro(currentTime, pod, timeInPrevState, State.WAIT)
            # Update state info
            pod.state = State.WAIT
            pod.stateTS = currentTime
            # Add to scheduler
            myScheduler.addPod(pod)

        elif eventTrans == Transition.TO_RUN:
            printStateIntro(currentTime, pod, timeInPrevState, State.RUN)
            # Update state info
            pod.state = State.RUN
            pod.stateTS = currentTime
            pod.execStartTime = currentTime
            pod.totalWaitTime += timeInPrevState
            # Create new event to fire off when proc is done, put the proc to DONE
            myEventQueue.putEvent(Event(currentTime+pod.work, pod, Transition.TO_TERM))

        # No blocking in this simulation :)
        # elif eventTrans == Transition.TO_BLOCK:
            # pass

        elif eventTrans == Transition.TO_PREEMPT:
            # No preemption in FCFS, Pod runs till the end
            pass

        elif eventTrans == Transition.TO_TERM:
            printStateIntro(currentTime, pod, timeInPrevState, State.TERM)
            # Update proc info
            pod.state = State.TERM
            pod.stateTS = currentTime
            pod.finishTime = currentTime
            # Return resouce to node
            node = pod.node
            pod.node = None
            node.removePod(pod)
        
        # Get next process
        # If another event of same time, process the next event before calling scheduler
        # If there are pods in the sched q and cannot be sched, then no point of running loop, exit
        # As long as a event happened, try to schedule some pods
        if myEventQueue.getNextEvtTime() != currentTime:
            if global_.qFlag:
                print(myScheduler.getPodQueueStr())

            scheduledPods = myScheduler.schedulePods(myNodeList)
            for p in scheduledPods:
                # There is a pod to run, create a new event
                myEventQueue.putEvent(Event(currentTime, p, Transition.TO_RUN))

        # Get the next event
        event = myEventQueue.getEvent()
    
    if global_.tFlag:
        print("\nSimulation End\nPods unable to schedule: %s\n###################\n" % (myScheduler.getPodQueueStr()))

if __name__ == "__main__":
   main(sys.argv[1:])
