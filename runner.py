import subprocess

currency_bot = subprocess.Popen('python currency_bot.py', shell=True)
knuc_tats_bot = subprocess.Popen('python knuc_tats_bot.py', shell=True)

currency_bot.wait()
knuc_tats_bot.wait()

