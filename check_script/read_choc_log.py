import os

log_file = 'debug_v4.log'
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-16') as f:
        lines = f.readlines()
        in_choc = False
        for line in lines:
            if "QUESTION: top 1 selling in CHOCALATE" in line:
                in_choc = True
            if in_choc:
                print(line, end='')
                if "==========" in line and line.strip() != "==========": # End of section
                    # Check next few lines
                    pass
                if len(line.strip()) == 20 and line.strip().startswith("="):
                    if in_choc and "QUESTION" not in line: # Secondary separator
                         # Actually just print until next question
                         pass
            if in_choc and "QUESTION:" in line and "top 1 selling" not in line:
                break
else:
    print("Log file not found")
