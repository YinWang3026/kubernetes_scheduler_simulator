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

class Node:
    def __init__(self, name: str, cpu: int, gpu: int, ram: int) -> None:
        # Basic info - DOES NOT CHANGE
        self.name = name
        self.cpu = cpu
        self.gpu = gpu
        self.ram = ram

        # Pods running on this node
        self.podSet = set() # For O(1) remove and add
    
    def addPod(self, pod: Pod) -> None:
        self.podSet.add(pod)

    def removePod(self, pod: Pod) -> None:
        self.podSet.discard(pod)
    
    def __repr__(self) -> str:
        return "Name: %s, CPU: %d, GPU: %d, RAM: %d" \
            % (self.name, self.cpu, self.gpu, self.ram)
    
    def reprPodList(self) -> str:
        s = "Node[%s] Pod List:\n" % (self.name)
        for pod in self.podSet:
            s += "\t" + pod.name + "\n"
        return s

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
        return "ID: %d, TimeStamp: %d, Pod:%s, Transition: %s" % (self.id, self.timeStamp, self.pod.name, self.transition.name)
    
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
    def __init__(self, quantum=10000, prio=4) -> None:
        # Quantum, prio are not used for FCFS, SRTF, SRF, Lottery, just placeholders for future
        self.quantum = quantum
        self.maxprio = prio
        self.queue = deque()
    
    def getProcess(self) -> Process:
        if len(self.queue) == 0:
            return None
        return self.queue.popleft()
    
    def getQuantum(self) -> int:
        return self.quantum
    
    def printQueue(self) -> None:
        print("SchedQ[%d]:" % (len(self.queue)))
        s = ""
        for i in range(0,len(self.queue)):
            s += self.queue[i].name + " "
        print(s)
        
class FCFS(Scheduler): # First Come First Served
    def __init__(self) -> None:
        super().__init__()

    def addProcess(self, process) -> None:
        self.queue.append(process)

    def __repr__(self) -> str:
        return "FCFS"
    
class SRTF(Scheduler): # Shortest Remaning Time First
    def __init__(self) -> None:
        super().__init__()

    def addProcess(self, process) -> None:
        index = 0
        while index < len(self.queue):
            if process.work < self.queue[index].work:
                break
            index += 1
        self.queue.insert(index, process)

    def __repr__(self) -> str:
        return "SRTF"

class SRF(Scheduler): # Smallest Resource First
    def __init__(self) -> None:
        self.queue = deque()

    def addProcess(self, process) -> None:
        index = 0
        while index < len(self.queue):
            if process.resource < self.queue[index].resource:
                break
            index += 1
        self.queue.insert(index, process)

    def __repr__(self) -> str:
        return "SRF"

class Lottery(Scheduler): # Random
    def __init__(self) -> None:
        self.queue = deque()

    def addProcess(self, process) -> None:
        self.queue.append(process)

    def getProcess(self) -> Process:
        # Overriding parent method
        if len(self.queue) == 0:
            return None

        totalTickets = 0
        for i in range(0, len(self.queue)):
            totalTickets += self.queue[i].tickets
        winningTicket = randint(1, totalTickets) # Gotta have at least 1 ticket
        winner = None
        currTotal = 0
        for i in range(0, len(self.queue)):
            currTotal += self.queue[i].tickets
            if currTotal >= winningTicket:
                winner = self.queue[i]
                break
        
        if winner == None:
            print("No winner in lottery, something gone real bad")
            sys.exit(1)
        
        if tFlag:
            print("Winner: %s" % (winner.name))
        self.queue.remove(winner)
        return winner
                
    def __repr__(self) -> str:
        return "Lottery"

def main(argv):
    ifile = ''
    scheduler = None
    try:
        opts, args = getopt.getopt(argv,"hvtqi:s:",["help, ifile=, sched="])
        # getopt.getopt(args, options, [long_options])
        # ":" indicates that an argument is needed, otherwise just an option, like -h
    except getopt.GetoptError:
        print('simulator.py -h -v -t -q -i <jobs.txt> -s <scheduler>')
        print('-v for general debugging info')
        print('-q for printing scheduler queue')
        print('-t for showing simulation traces')
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('simulator.py -h -v -t -q -i <jobs.txt> -s <scheduler>')
            print('-v for general debugging info')
            print('-q for printing scheduler queue')
            print('-t for showing simulation traces')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            ifile = arg
        elif opt in ("-s", "--sched"):
            if arg == "FCFS":
                scheduler = FCFS()
            elif arg == "SRTF":
                scheduler = SRTF()
            elif arg == "SRF":
                scheduler = SRF()
            elif arg == "Lottery":
                scheduler = Lottery()
        elif opt in ("-v"):
            global vFlag
            vFlag = True
        elif opt in ("-t"):
            global tFlag
            tFlag = True
        elif opt in ("-q"):
            global qFlag
            qFlag = True
    
    if ifile == "":
        print('Missing input file, exiting')
        sys.exit()
    
    if scheduler == None:
        print('Missing scheduler or used invalid name')
        sys.exit()

    myProcessList = []
    myEventQueue = EventQueue()
    with open(ifile, 'r') as f:
        header = f.readline().strip()
        if vFlag:
            print("Header: " + header)
        for line in f.readlines():
            line = line.strip().split()
            name = line[0]
            arrivalTime = int(line[1])
            work = int(line[2])
            tickets = int(line[3])
            resource = int(line[4])
            p = Process(name, arrivalTime, work, tickets, resource, State.CREATED)
            e = Event(arrivalTime, p, Transition.TO_READY)
            myProcessList.append(p)
            myEventQueue.putEvent(e)
    
    if vFlag:
        print("Inital loadout")
        for i in range(0, len(myProcessList)):
            print(myProcessList[i])
        myEventQueue.printQueue()

    # Start simulation
    simulate(myEventQueue, scheduler)

    # Calculate JCT
    print("Results")
    totalJct = 0
    for i in range(0, len(myProcessList)):
        totalJct += myProcessList[i].jct
        print(myProcessList[i])
    print("Scheduler: %s, Average JCT: %.2f" % (scheduler, float(totalJct)/float(len(myProcessList))))
    
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
