from random import randint, choice
from name_generator import iter_all_strings

gen = iter_all_strings()
N = 15
outFile = "nodes.txt"

with open(outFile, 'w') as f:
    f.write("nodeName cpu gpu ram\n")
    for i in range(0, N):
        if i != 0:
            f.write("\n")

        nodeName = "Node" + next(gen)
        cpu = choice([4,8,16,32,64,128])
        gpu = choice([1,2,4,8])
        ram = choice([4,8,16,32,64,128])

        f.write("%s %d %d %d" % (nodeName, cpu, gpu, ram))
