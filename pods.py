from enum import Enum, auto
import global_

# Pod has 3 states - Waiting Running and Terminated
class State(Enum):
    CREATED =  auto()
    WAIT = auto() # Aka the waiting state
    RUN = auto()
    TERM = auto() # The done state
    PREEMPT = auto()

class Pod:
    def __init__(self, user: str, name: str, arrivalTime: int, work: int, cpu: int, gpu: int, ram: int, prio: int, tickets: int, state: State) -> None:
        # Basic info - DOES NOT CHANGE
        self.user = user
        self.name = name
        self.at = arrivalTime
        self.work = work
        self.cpu = cpu
        self.gpu = gpu
        self.ram = ram
        self.prio = prio
        self.tickets = tickets

        # Node that I am running on
        self.node = None

        # State information
        self.state = state # Current state
        self.stateTS = arrivalTime # Time that entered current state
        self.preempted = False # Did I get preempted signaled?
        self.remainWork = work # remaining time to finish work
        self.dynamicPrio = prio # Current prio

        # Benchmarking values
        self.execStartTime = -1
        self.finishTime = 0
        self.totalWaitTime = 0

        # JCT
        self.jct = -1.00
    
    def calcJct(self) -> None:
        self.jct = (self.work + self.totalWaitTime) / self.work
    
    def __repr__(self) -> str:
        return "Name: %s, AT: %d, Work: %d, CPU: %d, GPU: %d, RAM: %d, PRIO: %d, Tickets: %d" \
            % (self.name, self.at, self.work, self.cpu, self.gpu, self.ram, self.prio, self.tickets)
    
    def getStateInfoStr(self) -> str:
        return "Name: %s, State: %s, StateTS: %d" % (self.name, self.state.name, self.stateTS)
    
    def getBenchmarkStr(self) -> str:
        return "Name: %s, ArrivalTime: %d, ExecStartTime: %d, FinishTime: %d, TotalWaitTime: %d, JCT: %.2f" \
            % (self.name, self.at, self.execStartTime, self.finishTime, self.totalWaitTime, self.jct)

class PodList:
    def __init__(self) -> None:
        self.pods = []
        self.avgJct = -1.00
    
    def calcAllJct(self) -> None:
        totalJct = 0
        for pod in self.pods:
            pod.calcJct()
            totalJct += pod.jct
        self.avgJct = totalJct / len(self.pods)

    def addPod(self, pod: Pod) -> None:
        self.pods.append(pod)

    def __repr__(self) -> str:
        s = "Pod List:\n"
        for i in self.pods:
            s += "\t" + i.__repr__() + "\n"
        return s
    
    def getPodsBenchmarkStr(self) -> str:
        s = "Pod Benchmarks:\n"
        for i in self.pods:
            s += "\t" + i.getBenchmarkStr() + "\n"
        s += "\tAverage JCT: %.2f" % (self.avgJct)
        return s