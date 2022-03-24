from collections import deque
from enum import Enum, auto
from random import randint
import sys, getopt

# Global variables
vFlag = False # General debug info
tFlag = False # Prints simulation trace
qFlag = False # Prints scheduler q

# Pod has 3 states - Waiting Running and Terminated
class State(Enum):
    CREATED =  auto()
    WAIT = auto() # Aka the waiting state
    RUN = auto()
    TERM = auto() # The done state

class Transition(Enum):
    TO_RUN = auto() 
    TO_WAIT = auto() # To waiting state
    TO_PREEMPT = auto() # Running to waiting
    TO_TERM = auto() # Termination

class Pod:
    def __init__(self, name: str, arrivalTime: int, work: int, cpu: int, gpu: int, ram: int, prio: int, tickets: int, state: State) -> None:
        # Basic info - DOES NOT CHANGE
        self.name = name
        self.at = arrivalTime
        self.work = work
        self.cpu = cpu
        self.gpu = gpu
        self.ram = ram
        self.prio = prio
        self.tickets = tickets

        # State information
        self.state = state # Current state
        self.stateTS = arrivalTime # Time that entered current state

        # Benchmarking values
        self.execStartTime = 0
        self.finishTime = 0
        self.totalWaitTime = 0
    
    def __repr__(self) -> str:
        return "Name: %s, AT: %d, Work: %d, CPU: %d, GPU: %d, RAM: %d, PRIO: %d, Tickets: %d" \
            % (self.name, self.at, self.work, self.cpu, self.gpu, self.ram, self.prio, self.tickets)
    
    def reprStateInfo(self) -> str:
        return "State: %s, StateTS: %d" % (self.state.name, self.stateTS)
    
    def reprBenchmark(self) -> str:
        return "ExecStartTime: %d, FinishTime: %d, TotalWaitTime: %d" \
            % (self.execStartTime, self.finishTime, self.totalWaitTime)

class PodList:
    def __init__(self) -> None:
        self.pods = []

    def addPod(self, pod: Pod) -> None:
        self.pods.append(pod)

    def __repr__(self) -> str:
        s = "Pod List:\n"
        for i in self.pods:
            s += "\t" + i.__repr__() + "\n"
        return s

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
        self.podSet.add(pod)

    def removePod(self, pod: Pod) -> None:
        self.curCpu += pod.cpu
        self.curGpu += pod.gpu
        self.curRam += pod.ram
        self.podSet.discard(pod)
    
    def __repr__(self) -> str:
        return "Name: %s, CPU: %d, GPU: %d, RAM: %d" \
            % (self.name, self.cpu, self.gpu, self.ram)
    
    def reprPodList(self) -> str:
        s = "Node[%s] Pod List: " % (self.name)
        for pod in self.podSet:
            s += pod.name + " "
        return s

class NodeList:
    def __init__(self) -> None:
        self.nodes = []

    def addNode(self, node: Node) -> None:
        self.nodes.append(node)

    def getMatch(self, pod: Pod) -> list[Node]:
        # Return a list of nodes that can run the given pod
        # Can use derived class and a custom policy
        # Default policy, return the first node that has enough resource to run this pod
        for i in self.nodes:
            if i.curCpu >= pod.cpu and i.curGpu >= pod.gpu and i.curRam >= pod.ram:
                return [i]
        
        return []

    def __repr__(self) -> str:
        s = "Node List:\n"
        for i in self.nodes:
            s += "\t" + i.__repr__() + "\n"

class NodeListSecretPolicy(NodeList):
    def __init__(self) -> None:
        super().__init__()
    
    def getMatch(self, pod: Pod) -> list[Node]:
        # return super().getMatch(pod)
        # SuPer secret policy
        pass


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

class Scheduler:
    def __init__(self, nodeList: NodeList, quantum: int = 10000, prio: int = 4) -> None:
        self.quantum = quantum
        self.maxprio = prio
        self.nodeList = nodeList

        self.podQueue = deque()
    
    def addPod(self, pod: Pod) -> None:
        print("Derived class please implement")

    def schedulePod(self):
        print("Derived class please implement")
        
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
        return "Quantum: %d, Maxprio: %d" % (self.quantum, self.maxprio)
        
class FCFS(Scheduler): # First Come First Served
    def __init__(self, nodeList: NodeList) -> None:
        super().__init__(nodeList=nodeList)

    def addPod(self, pod: Pod) -> None:
        pass

    def schedulePod(self):
        # Not sure how this going to work yet
        pass

    def __repr__(self) -> str:
        return "FCFS " + super().__repr__()
    
# class SRTF(Scheduler): # Shortest Remaning Time First
#     def __init__(self) -> None:
#         super().__init__()

#     def addPod(self, pod: Pod) -> None:
#         pass

#     def __repr__(self) -> str:
#         return "SRTF"

# class SRF(Scheduler): # Smallest Resource First
#     def __init__(self) -> None:
#         self.queue = deque()

#     def addPod(self, pod: Pod) -> None:
#         pass

#     def __repr__(self) -> str:
#         return "SRF"

# class Lottery(Scheduler): # Random
#     def __init__(self) -> None:
#         self.queue = deque()

#     def addPod(self, pod: Pod) -> None:
#         pass
                
#     def __repr__(self) -> str:
#         return "Lottery"

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
                myScheduler = FCFS(nodeList = myNodeList)
            # elif arg == "SRTF":
            #     myScheduler = SRTF()
            # elif arg == "SRF":
            #     myScheduler = SRF()
            # elif arg == "Lottery":
            #     myScheduler = Lottery()
        elif opt in ("-v"):
            global vFlag
            vFlag = True
        elif opt in ("-t"):
            global tFlag
            tFlag = True
        elif opt in ("-q"):
            global qFlag
            qFlag = True
    
    if pfile == "":
        print('Missing pod file, exiting')
        sys.exit()
    
    if nfile == "":
        print('Missing node file, exiting')
        sys.exit()
    
    if myScheduler == None:
        print('Missing scheduler or used invalid name')
        sys.exit()

    with open(pfile, 'r') as f:
        header = f.readline().strip()
        if vFlag:
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
        if vFlag:
            print("Header: " + header)
        for line in f.readlines():
            line = line.strip().split()
            name = line[0]
            cpu = int(line[1])
            gpu = int(line[2])
            ram = int(line[3])

            myNodeList.addNode(Node(name, cpu, gpu, ram))
    
    if vFlag:
        print(myPodList)
        print(myEventQueue)

    # Start simulation
    # simulate(myEventQueue, scheduler)

    
def simulate(myEventQueue, myScheduler) -> None:
    def printStateIntro(currentTime, proc, timeInPrevState, newState):
        if tFlag:
            print("currentTime: %d, procName: %s, timeInPrevState: %d, from: %s to: %s" \
                % (currentTime, proc.name, timeInPrevState, proc.state, newState))

    event = myEventQueue.getEvent()
    runningProc = None
    callScheduler = False

    while (event != None):
        proc = event.process
        eventTrans = event.transition
        currentTime = event.timeStamp
        timeInPrevState = currentTime - proc.stateTS
        event = None # Disconnect pointer to object

        # Process events
        if eventTrans == Transition.TO_READY:
            printStateIntro(currentTime, proc, timeInPrevState, State.READY.name)
            # Update state info
            proc.state = State.READY
            proc.stateTS = currentTime
            # Add to scheduler
            myScheduler.addProcess(proc)
            callScheduler = True

        elif eventTrans == Transition.TO_RUN:
            printStateIntro(currentTime, proc, timeInPrevState, State.RUN.name)
            # Update state info
            proc.state = State.RUN
            proc.stateTS = currentTime
            proc.execStartTime = currentTime
            proc.waitTime += timeInPrevState
            # Create new event to fire off when proc is done, put the proc to DONE
            myEventQueue.putEvent(Event(currentTime+proc.work, proc, Transition.TO_DONE))

        elif eventTrans == Transition.TO_BLOCK:
            # No blocking in this simulation :)
            pass

        elif eventTrans == Transition.TO_PREEMPT:
            # No preemption in FCFS SRTF SRF LOTTERY
            pass

        elif eventTrans == Transition.TO_DONE:
            printStateIntro(currentTime, proc, timeInPrevState, State.DONE.name)
            # Update proc info
            proc.state = State.DONE
            proc.stateTS = currentTime
            proc.finishTime = currentTime
            proc.setJct() # Calculate the jct
            # Call scheduler for a new proc to run
            callScheduler = True
            runningProc = None
        
        # Get next process
        # If another event of same time, process the next event before calling scheduler
        if callScheduler and myEventQueue.getNextEvtTime() != currentTime:
            # Reset the flag
            callScheduler = False
            # No proc running
            if runningProc == None:
                if qFlag:
                    myScheduler.printQueue()

                runningProc = myScheduler.getProcess()
                if runningProc != None:
                    # There is a process to run, create a new event
                    myEventQueue.putEvent(Event(currentTime, runningProc, Transition.TO_RUN))

        # Get next event
        event = myEventQueue.getEvent()

if __name__ == "__main__":
   main(sys.argv[1:])
