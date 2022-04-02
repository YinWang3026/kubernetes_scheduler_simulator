# Kubernetes Scheduler Simulator

## Basic Information

1. nodes.txt contains a list of randomly generated nodes
2. pods.txt contains a list of randomly generated pods
3. pod_gen.py generates pods.txt
4. node_gen.py generates nodes.txt
5. Running the simulator

- `py simulator.py -h -v -t -q -p <pods.txt> -n <nodes.txt> -s <scheduler> -d <node scheduler>`
  - -p or --pfile for pod file
    - Required arg
  - -n or --nfile for node file
    - Required arg
  - -s or --sched for pod scheduler
    - Required arg
  - -d or --nsched for node scheduler
    - Not implemented yet
  - -v for general debugging info
  - -q for printing scheduler queue
  - -t for showing simulation traces

## Sample Trace of Current Setup

```Trace
Header: podName arrivalTime work prio tickets cpu gpu ram
Header: nodeName cpu gpu ram
Pod List:
        Name: PodA, AT: 0, Work: 452, CPU: 12, GPU: 21, RAM: 60, PRIO: 2, Tickets: 95
        Name: PodB, AT: 5, Work: 644, CPU: 8, GPU: 16, RAM: 69, PRIO: 4, Tickets: 65
        Name: PodC, AT: 5, Work: 671, CPU: 8, GPU: 4, RAM: 21, PRIO: 4, Tickets: 86
        Name: PodD, AT: 5, Work: 580, CPU: 7, GPU: 27, RAM: 62, PRIO: 1, Tickets: 76
        Name: PodE, AT: 10, Work: 545, CPU: 5, GPU: 18, RAM: 103, PRIO: 2, Tickets: 46

Node List:
        Name: NodeA, CPU: 10, GPU: 29, RAM: 94
        Name: NodeB, CPU: 15, GPU: 17, RAM: 70
        Name: NodeC, CPU: 15, GPU: 31, RAM: 97
        Name: NodeD, CPU: 11, GPU: 25, RAM: 44
        Name: NodeE, CPU: 14, GPU: 17, RAM: 122
        Name: NodeF, CPU: 10, GPU: 23, RAM: 92
        Name: NodeG, CPU: 16, GPU: 27, RAM: 120
        Name: NodeH, CPU: 15, GPU: 32, RAM: 89
        Name: NodeI, CPU: 12, GPU: 24, RAM: 94
        Name: NodeJ, CPU: 13, GPU: 27, RAM: 113
        Name: NodeK, CPU: 12, GPU: 11, RAM: 33
        Name: NodeL, CPU: 11, GPU: 15, RAM: 106
        Name: NodeM, CPU: 14, GPU: 10, RAM: 36
        Name: NodeN, CPU: 16, GPU: 19, RAM: 109
        Name: NodeO, CPU: 12, GPU: 30, RAM: 52

Event Queue:
        ID: 0, TimeStamp: 0, Pod: PodA, Transition: TO_WAIT
        ID: 1, TimeStamp: 5, Pod: PodB, Transition: TO_WAIT
        ID: 2, TimeStamp: 5, Pod: PodC, Transition: TO_WAIT
        ID: 3, TimeStamp: 5, Pod: PodD, Transition: TO_WAIT
        ID: 4, TimeStamp: 10, Pod: PodE, Transition: TO_WAIT

Scheduler: FCFS Quantum: 10000, Maxprio: 4

###################
Simulation Start
currentTime: 0, podName: PodA, timeInPrevState: 0, from: State.CREATED to: State.WAIT
SchedQ[1]:PodA
Matched Pod [PodA] with Node [NodeC]
Time [0] Adding Pod [PodA] to Node [NodeC]
        Before CPU: 15, GPU: 31, RAM: 97
        After CPU: 3, GPU: 10, RAM: 37
currentTime: 0, podName: PodA, timeInPrevState: 0, from: State.WAIT to: State.RUN
SchedQ[0]:
currentTime: 5, podName: PodB, timeInPrevState: 0, from: State.CREATED to: State.WAIT
currentTime: 5, podName: PodC, timeInPrevState: 0, from: State.CREATED to: State.WAIT
currentTime: 5, podName: PodD, timeInPrevState: 0, from: State.CREATED to: State.WAIT
SchedQ[3]:PodB PodC PodD
Matched Pod [PodB] with Node [NodeA]
Time [5] Adding Pod [PodB] to Node [NodeA]
        Before CPU: 10, GPU: 29, RAM: 94
        After CPU: 2, GPU: 13, RAM: 25
Matched Pod [PodC] with Node [NodeB]
Time [5] Adding Pod [PodC] to Node [NodeB]
        Before CPU: 15, GPU: 17, RAM: 70
        After CPU: 7, GPU: 13, RAM: 49
Matched Pod [PodD] with Node [NodeG]
Time [5] Adding Pod [PodD] to Node [NodeG]
        Before CPU: 16, GPU: 27, RAM: 120
        After CPU: 9, GPU: 0, RAM: 58
currentTime: 5, podName: PodB, timeInPrevState: 0, from: State.WAIT to: State.RUN
currentTime: 5, podName: PodC, timeInPrevState: 0, from: State.WAIT to: State.RUN
currentTime: 5, podName: PodD, timeInPrevState: 0, from: State.WAIT to: State.RUN
SchedQ[0]:
currentTime: 10, podName: PodE, timeInPrevState: 0, from: State.CREATED to: State.WAIT
SchedQ[1]:PodE
Matched Pod [PodE] with Node [NodeJ]
Time [10] Adding Pod [PodE] to Node [NodeJ]
        Before CPU: 13, GPU: 27, RAM: 113
        After CPU: 8, GPU: 9, RAM: 10
currentTime: 10, podName: PodE, timeInPrevState: 0, from: State.WAIT to: State.RUN
SchedQ[0]:
currentTime: 452, podName: PodA, timeInPrevState: 452, from: State.RUN to: State.TERM
Time [452] Removing Pod [PodA] from Node [NodeC]
        Before CPU: 3, GPU: 10, RAM: 37
        After CPU: 15, GPU: 31, RAM: 97
SchedQ[0]:
currentTime: 555, podName: PodE, timeInPrevState: 545, from: State.RUN to: State.TERM
Time [555] Removing Pod [PodE] from Node [NodeJ]
        Before CPU: 8, GPU: 9, RAM: 10
        After CPU: 13, GPU: 27, RAM: 113
SchedQ[0]:
currentTime: 585, podName: PodD, timeInPrevState: 580, from: State.RUN to: State.TERM
Time [585] Removing Pod [PodD] from Node [NodeG]
        Before CPU: 9, GPU: 0, RAM: 58
        After CPU: 16, GPU: 27, RAM: 120
SchedQ[0]:
currentTime: 649, podName: PodB, timeInPrevState: 644, from: State.RUN to: State.TERM
Time [649] Removing Pod [PodB] from Node [NodeA]
        Before CPU: 2, GPU: 13, RAM: 25
        After CPU: 10, GPU: 29, RAM: 94
SchedQ[0]:
currentTime: 676, podName: PodC, timeInPrevState: 671, from: State.RUN to: State.TERM
Time [676] Removing Pod [PodC] from Node [NodeB]
        Before CPU: 7, GPU: 13, RAM: 49
        After CPU: 15, GPU: 17, RAM: 70
SchedQ[0]:

Simulation End
Pods unable to schedule: SchedQ[0]:
###################

Pod List Benchmarks:
        Name: PodA, ExecStartTime: 0, FinishTime: 452, TotalWaitTime: 0
        Name: PodB, ExecStartTime: 5, FinishTime: 649, TotalWaitTime: 0
        Name: PodC, ExecStartTime: 5, FinishTime: 676, TotalWaitTime: 0
        Name: PodD, ExecStartTime: 5, FinishTime: 585, TotalWaitTime: 0
        Name: PodE, ExecStartTime: 10, FinishTime: 555, TotalWaitTime: 0

Usage Log:
        Node[NodeA] Usage Log:  (5, 649, 'PodB', 8, 16, 69)
        Node[NodeB] Usage Log:  (5, 676, 'PodC', 8, 4, 21)
        Node[NodeC] Usage Log:  (0, 452, 'PodA', 12, 21, 60)
        Node[NodeD] Usage Log:
        Node[NodeE] Usage Log:
        Node[NodeF] Usage Log:
        Node[NodeG] Usage Log:  (5, 585, 'PodD', 7, 27, 62)
        Node[NodeH] Usage Log:
        Node[NodeI] Usage Log:
        Node[NodeJ] Usage Log:  (10, 555, 'PodE', 5, 18, 103)
        Node[NodeK] Usage Log:
        Node[NodeL] Usage Log:
        Node[NodeM] Usage Log:
        Node[NodeN] Usage Log:
        Node[NodeO] Usage Log:
```
