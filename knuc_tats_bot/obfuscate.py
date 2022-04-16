"""
Use to make banned words list not look like a bunch of slurs.
"""
OBFUSCATE_TOKEN = '%'

def obfuscate(word):
    out = ""
    for chr in word:
        out += f"{OBFUSCATE_TOKEN}{ord(chr.upper()):x}"
    return out

def deobfuscate(word):
    letters = word.split(OBFUSCATE_TOKEN)
    out = ""
    for letter in letters:
        if letter:
            out += chr(int(letter, 16))
    return out

if __name__ == "__main__":
    banned_words = "%41%42%42%4f,%41%42%4f,%43%48%49%4e%41%4d%41%4e,%43%48%49%4e%41%4d%45%4e,%43%48%49%4e%4b,%43%4f%4f%4c%49%45,%45%53%4b%49%4d%4f,%47%4f%4c%4c%49%57%4f%47,%47%4f%4f%4b,%47%59%50,%47%59%50%53%59,%48%45%45%42,%4a%41%50,%4b%41%46%46%45%52,%4b%41%46%46%49%52,%4b%41%46%46%49%52,%4b%41%46%46%52%45,%4b%41%46%49%52,%4b%49%4b%45,%4e%45%47%52%45%53%53,%4e%45%47%52%4f,%4e%49%47,%4e%49%47%2d%4e%4f%47,%4e%49%47%47%41,%4e%49%47%47%45%52,%4e%49%47%47%55%48,%50%41%4a%45%45%54,%50%41%4b%49,%50%49%43%4b%41%4e%49%4e%4e%49%45,%50%49%43%4b%41%4e%49%4e%4e%59,%52%41%47%48%45%41%44,%52%45%54%41%52%44,%53%41%4d%42%4f,%53%50%45%52%47,%53%50%49%43,%53%50%4f%4f%4b,%53%51%55%41%57,%54%41%52%44,%57%45%54%42%41%43%4b,%57%49%47%47%45%52,%5a%4f%47,%52%41%50%45,%52%41%50%49%53%54,%54%48%41%4e%4b%59%4f%55,%49%27%4d%53%4f%52%52%59,%4f%46%43%4f%55%52%53%45"
    #banned_words = open("banned_words.txt").read() #uncomment if you want to read from a file
    if type(banned_words) == str:
        banned_words = banned_words.split(",")

    fixed_str = ""

    for word in banned_words:
        fixed_str += f"{obfuscate(word)},"

    print(fixed_str[:-1])
    print()
    #open("obfuscated_banned_words.txt","w").write(fixed_str[:-1]) #uncomment if you want output in a file.
