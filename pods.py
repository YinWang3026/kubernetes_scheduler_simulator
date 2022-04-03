from enum import Enum, auto
import global_

# Pod has 3 states - Waiting Running and Terminated
class State(Enum):
    CREATED =  auto()
    WAIT = auto() # Aka the waiting state
    RUN = auto()
    TERM = auto() # The done state

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

        # Node that I am running on
        self.node = None

        # State information
        self.state = state # Current state
        self.stateTS = arrivalTime # Time that entered current state
        self.remainWork = work # remaining time to finish work

        # Benchmarking values
        self.execStartTime = 0
        self.finishTime = 0
        self.totalWaitTime = 0
    
    def __repr__(self) -> str:
        return "Name: %s, AT: %d, Work: %d, CPU: %d, GPU: %d, RAM: %d, PRIO: %d, Tickets: %d" \
            % (self.name, self.at, self.work, self.cpu, self.gpu, self.ram, self.prio, self.tickets)
    
    def getStateInfoStr(self) -> str:
        return "State: %s, StateTS: %d" % (self.state.name, self.stateTS)
    
    def getBenchmarkStr(self) -> str:
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
    
    def getPodsBenchmarkStr(self) -> str:
        s = "Pod List Benchmarks:\n"
        for i in self.pods:
            s += "\t" + i.getBenchmarkStr() + "\n"
        return s