import sys
from PIL import Image

def main(imgpath: str) -> str:
    img = Image.open(imgpath)

    if img.height != 96:
        raise TypeError('Bitmap height not 96!')
    if img.width != 200:
        raise TypeError('Bitmap width not 200!')

    px = img.load()
    bitpack = bytearray(b'\x00' * 96 * (200 // 8))
        
    bpl = 200 // 8
    for y in range(96):
        i = -1
        for x in range(200):
            #print(f"x={x}, y={y}")
            if x % 8 == 0:
                i+=1
            val = 0 if px[x,y] else 1
            bitpack[(y*bpl)+i] |= val << (x % 8)

    ret = "img = bytearray(\n"
    for i in range(96):
        b = bytes(bitpack[(200//8)*i: ((200//8)*i) + 200//8])
        ret += f"\t{b}\n"
    ret += ")"

    return ret

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(1)
    
    print(main(sys.argv[1]))