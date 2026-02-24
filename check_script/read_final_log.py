import os

log_file = 'debug_v4.log'
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-16') as f:
        content = f.read()
        print(content)
else:
    print("Log file not found")
