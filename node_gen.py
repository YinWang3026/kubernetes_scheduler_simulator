from random import randint
from name_generator import iter_all_strings
import sys

def main(argv: list[str]):
    gen = iter_all_strings()
    N = 100
    outFile = argv[0] if len(argv) == 1 else "nodes.txt"

    cpus = [4,8,16]
    rams = [8,16,32]
    gpus = [1,2,4]

    with open(outFile, 'w') as f:
        f.write("nodeName cpu gpu ram\n")

        # Small Nodes
        for i in range(0, int(N*0.3)):
            if i != 0:
                f.write("\n")
            nodeName = "Node" + next(gen)
            # cpu = randint(10,16)
            # gpu = randint(10,32)
            # ram = randint(32,128)
            f.write("%s %d %d %d" % (nodeName, cpus[0], gpus[0], rams[0]))
        f.write("\n")

        # Medium Nodes
        for i in range(0, int(N*0.3)):
            if i != 0:
                f.write("\n")
            nodeName = "Node" + next(gen)
            f.write("%s %d %d %d" % (nodeName, cpus[1], gpus[1], rams[1]))
        f.write("\n")

        # Large Nodes
        for i in range(0, int(N*0.4)):
            if i != 0:
                f.write("\n")

            nodeName = "Node" + next(gen)
            f.write("%s %d %d %d" % (nodeName, cpus[2], gpus[2], rams[2]))

if __name__ == "__main__":
   main(sys.argv[1:])
