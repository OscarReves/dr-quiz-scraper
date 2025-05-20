import json

def collect_quizzes(load_dir, range=range(1,15+1)):
    with open(f"{load_dir}/2025.jsonl", "w") as out_f:
        for i in range:
            file_path = f"{load_dir}/week{i}_2025.jsonl"
            with open(file_path) as in_f:
                for line in in_f:
                    obj = json.loads(line)
                    obj["week"] = i  
                    obj["id"] = int(str(i) + str(obj['id']))
                    out_f.write(json.dumps(obj) + "\n")

