from random import randint
from name_generator import iter_all_strings
import sys
import random

def main(argv):
    # outFile = argv[0] if len(argv) == 1 else "pods.txt"
    N = 2500 # number of pods
    MAXTIME = 120
    NUMUSERS = 100 # number of users

    userNames = []
    userPriorities = dict()
    genUserNames = iter_all_strings()
    for _ in range(NUMUSERS):
        name = "User" + next(genUserNames)
        userNames.append(name)
        userPriorities[name] = randint(1,10)

    cpus = [4,8,16]
    rams = [8,16,32]
    gpus = [1,2,4]

    # Large pods
    outFile = "pods_large.txt"
    genPodNames = iter_all_strings()
    # currentTime = 0
    with open(outFile, 'w') as f:
        f.write("UserName podName arrivalTime work prio tickets cpu gpu ram tickets\n")
        for i in range(0, N):
            if i != 0:
                f.write("\n")

            userName = random.choice(userNames)
            podName = "Pod" + next(genPodNames)
            arrivalTime = randint(0, MAXTIME) # Generate pods between 0 to 60 s
            work = randint(100, 1000)
            prio = randint(1, 4)
            tickets = userPriorities[userName] * 10
            cpu = randint(cpus[0],cpus[2]) # Only has cpus from 8 to 16
            gpu = randint(gpus[0],gpus[2])
            ram = randint(rams[0],rams[2])

            # currentTime += arrivalTime
            f.write("%s %s %d %d %d %d %d %d %d" % (userName, podName, arrivalTime, work, prio, tickets, cpu, gpu, ram))
    
    # Small pods
    outFile = "pods_small.txt"
    genPodNames = iter_all_strings()
    with open(outFile, 'w') as f:
        f.write("UserName podName arrivalTime work prio tickets cpu gpu ram tickets\n")
        for i in range(0, N):
            if i != 0:
                f.write("\n")

            userName = random.choice(userNames)
            podName = "Pod" + next(genPodNames)
            arrivalTime = randint(0, MAXTIME) # Generate pods between 0 to 60 s
            work = randint(100, 1000)
            prio = randint(1, 4)
            tickets = userPriorities[userName] * 10
            cpu = randint(1,cpus[1]) # Only has cpus from 1 to 8
            gpu = randint(0,gpus[1]) # Can have no gpu
            ram = randint(1,rams[1]) # has 1 to 16 ram

            f.write("%s %s %d %d %d %d %d %d %d" % (userName, podName, arrivalTime, work, prio, tickets, cpu, gpu, ram))
    
    # mix pods
    outFile = "pods_mix.txt"
    genPodNames = iter_all_strings()
    with open(outFile, 'w') as f:
        f.write("UserName podName arrivalTime work prio tickets cpu gpu ram tickets\n")
        for i in range(0, N):
            if i != 0:
                f.write("\n")

            userName = random.choice(userNames)
            podName = "Pod" + next(genPodNames)
            arrivalTime = randint(0, MAXTIME) # Generate pods between 0 to 60 s
            work = randint(100, 1000)
            prio = randint(1, 4)
            tickets = userPriorities[userName] * 10
            cpu = randint(1,cpus[2]) # Has cpus from 1 to 16
            gpu = randint(0,gpus[2])
            ram = randint(1,rams[2])

            f.write("%s %s %d %d %d %d %d %d %d" % (userName, podName, arrivalTime, work, prio, tickets, cpu, gpu, ram))

if __name__ == "__main__":
   main(sys.argv[1:])