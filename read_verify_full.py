with open("verify_multi_fact_count.py.out", "w") as out:
    pass # create empty

import subprocess
res = subprocess.run(["python", "verify_multi_fact_count.py"], capture_output=True, text=True)
print(res.stdout)
