import os

# Run the command and capture output directly to a file that we can read safely
os.system("python final_verify.py > final_results.log 2>&1")

with open('final_results.log', 'r', encoding='utf-8', errors='ignore') as f:
    print(f.read())
