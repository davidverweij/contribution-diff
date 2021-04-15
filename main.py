
from pathlib import Path
import json
import os

def read_json(filepath: Path):
    with open(filepath, "r") as f:
        data = f.read()
    return json.loads(data)

def write_json(filepath: Path, data: dict):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

folder = Path(__file__).parent
we_are = os.getenv("OUR_ID")

if __name__ == "__main__":
    
    us = {}
    them = {}
    data = read_json(Path(f'{folder}/all_records.json'))
    for item in data:
        d = json.loads(item["description"])
        
        key = d["participantId"]
        value = d["deviceId"]
        if key[0] != "K" or "BTF" not in value:
            continue
        
        if item["uploadedBy"] == wp3:
            us.setdefault(key,set()).add(value)
        else:
            them.setdefault(key,set()).add(value)

    result_us = {}
    for patient in us:
        if patient in them:
            #  in us but not in them:
            us_not_them = us[patient] - them[patient]
            if len(us_not_them) > 0:
                result_us[patient] = us_not_them
        else:
            result_us[patient] = us[patient]

    result_them = {}
    for patient in them:
        if patient in us:
            #  in us but not in them:
            them_not_us = them[patient] - us[patient]
            if len(them_not_us) > 0:
                result_them[patient] = them_not_us
        else:
            result_them[patient] = them[patient]


    print("us not them: ")
    print(json.dumps(result_us,cls=SetEncoder,sort_keys=True, indent=4))
    print("them not us: ")
    print(json.dumps(result_them,cls=SetEncoder,sort_keys=True, indent=4))
    

    