from random import randint
from name_generator import iter_all_strings
import sys

def main(argv):
    currentTime = 0
    gen = iter_all_strings()
    N = 5
    outFile = argv[0] if len(argv) == 1 else "pods.txt"

    with open(outFile, 'w') as f:
        f.write("UserName podName arrivalTime work prio tickets cpu gpu ram\n")
        for i in range(0, N):
            if i != 0:
                f.write("\n")

            userName = "User" + next(gen)
            podName = "Pod" + next(gen)
            arrivalTime = randint(0, 5)
            work = randint(100, 1000)
            prio = randint(1, 4)
            tickets = randint(10, 100)
            cpu = randint(1,16)
            gpu = randint(1,32)
            ram = randint(1,128)

            currentTime += arrivalTime
            f.write("%s %s %d %d %d %d %d %d %d" % (userName, podName, currentTime, work, prio, tickets, cpu, gpu, ram))

if __name__ == "__main__":
   main(sys.argv[1:])