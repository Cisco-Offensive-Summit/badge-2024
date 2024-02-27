import sys

def main(s: str) -> str:
    ret = "char file[] = {\n"
    with open(s, 'rb') as f:
        file_bytes = f.read()

        count = 0
        for i in range(len(file_bytes)):
            if count == 0:
                ret += '\t'

            if i == len(file_bytes)-1:
                ret += "0x{:02x}".format(file_bytes[i])
            else:
                ret += "0x{:02x}, ".format(file_bytes[i])
            count += 1

            if count == 25 and i != len(file_bytes)-1:
                ret += '\n'
                count = 0
    
    ret += "\n};"

    return ret

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(1)
    
    print(main(sys.argv[1]))
