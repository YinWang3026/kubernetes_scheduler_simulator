from random import randint
from name_generator import iter_all_strings

gen = iter_all_strings()
N = 76
outFile = "nodes.txt"

with open(outFile, 'w') as f:
    f.write("nodeName cpu gpu ram\n")
    for i in range(0, N):
        if i != 0:
            f.write("\n")

        nodeName = "Node" + next(gen)
        cpu = randint(1,16)
        gpu = randint(1,32)
        ram = randint(1,128)

        f.write("%s %d %d %d" % (nodeName, cpu, gpu, ram))
