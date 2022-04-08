from random import randint
from name_generator import iter_all_strings
import sys

def main(argv: list[str]):
    gen = iter_all_strings()
    N = 15
    outFile = argv[0] if len(argv) == 1 else "nodes.txt"

    with open(outFile, 'w') as f:
        f.write("nodeName cpu gpu ram\n")
        for i in range(0, N):
            if i != 0:
                f.write("\n")

            nodeName = "Node" + next(gen)
            cpu = randint(10,16)
            gpu = randint(10,32)
            ram = randint(32,128)

            f.write("%s %d %d %d" % (nodeName, cpu, gpu, ram))

if __name__ == "__main__":
   main(sys.argv[1:])
