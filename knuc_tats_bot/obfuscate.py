"""
Use to make banned words list not look like a bunch of slurs.
"""
OBFUSCATE_TOKEN = '%'

def obfuscate(word):
    out = ""
    for chr in word:
        out += f"{OBFUSCATE_TOKEN}{ord(chr.upper()):x}"
    return out

if __name__ == "__main__":
    banned_words = ""
    #banned_words = open("banned_words.txt").read() #uncomment if you want to read from a file
    if type(banned_words) == str:
        banned_words = banned_words.split(",")

    fixed_str = ""

    for word in banned_words:
        fixed_str += f"{obfuscate(word)},"


    print(fixed_str[:-1])
    #open("obfuscated_banned_words.txt","w").write(fixed_str[:-1]) #uncomment if you want output in a file.
