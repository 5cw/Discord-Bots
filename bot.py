import subprocess

p1 = subprocess.Popen('python cool_dollar_bot.py', shell=True)
p2 = subprocess.Popen('python knuc_tats_bot.py', shell=True)

p1.wait()
p2.wait()

