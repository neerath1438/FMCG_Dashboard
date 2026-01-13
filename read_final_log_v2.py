with open('final_results.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    for line in lines[:100]:
        print(line, end='')
