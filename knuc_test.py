import re
wws = re.sub(r'\s', '', input("test string: "))
NUM = 3
if len(wws) > 0 and len(wws) % 8 == 0 and len(wws) // 8 <= NUM:
    out = ""
    for i in range(0,len(wws),8):
        out += f"{wws[i:i+4]} {wws[i+4:i+8]}\n".upper()
    print(out)