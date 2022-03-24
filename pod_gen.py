from random import randint
from name_generator import iter_all_strings

currentTime = 0
gen = iter_all_strings()
N = 52
outFile = "pods.txt"

with open(outFile, 'w') as f:
    f.write("podName arrivalTime work prio tickets cpu gpu ram\n")
    for i in range(0, N):
        if i != 0:
            f.write("\n")

        podName = "Pod" + next(gen)
        arrivalTime = randint(0, 5)
        work = randint(100, 1000)
        prio = randint(1, 4)
        tickets = randint(10, 100)
        cpu = randint(1,16)
        gpu = randint(1,32)
        ram = randint(1,128)

        currentTime += arrivalTime
        f.write("%s %d %d %d %d %d %d %d" % (podName, currentTime, work, prio, tickets, cpu, gpu, ram))
