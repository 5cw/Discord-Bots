import subprocess

cool_dollar_bot = subprocess.Popen('python cool_dollar_bot.py', shell=True)
knuc_tats_bot = subprocess.Popen('python knuc_tats_bot.py', shell=True)

cool_dollar_bot.wait()
knuc_tats_bot.wait()

