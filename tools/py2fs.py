import sys

def get_file_as_bytes(s: str) -> str:
    ret = "\tconst unsigned char file[] = {\n"
    with open(s, 'rb') as f:
        file_bytes = f.read()

        count = 0
        for i in range(len(file_bytes)):
            if count == 0:
                ret += '\t\t'

            if i == len(file_bytes)-1:
                ret += "0x{:02x}".format(file_bytes[i])
            else:
                ret += "0x{:02x}, ".format(file_bytes[i])
            count += 1

            if count == 25 and i != len(file_bytes)-1:
                ret += '\n'
                count = 0
    
    ret += "\n\t};"

    return ret

def main(s: str) -> str:
    file_bytes_str = get_file_as_bytes(s)
    try:
        friendly_name = s.rsplit('.', 1)[0].rsplit('/', 1)[1]
    except IndexError:
        friendly_name = s.rsplit('.', 1)[0]
    ending = s.rsplit('.', 1)[1]

    ret = "static void offsummit_make_{}(FATFS *fatfs)".format(friendly_name)
    ret += " {\n"
    ret += file_bytes_str
    ret += '\n\n'
    ret += f'\tmake_file_with_contents(fatfs, "/{friendly_name}.{ending}", file, sizeof(file));\n'
    ret += "}"

    return ret


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(1)
    
    print(main(sys.argv[1]))