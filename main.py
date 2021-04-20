
import sys
from pathlib import Path
import json
import csv
from datetime import date, timedelta
from collections import defaultdict
from dataclasses import dataclass

def read_json(filepath: Path):
    with open(filepath, "r") as f:
        data = f.read()
    return json.loads(data)

def write_json(filepath: Path, data: dict):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

class SetEncoder(json.JSONEncoder):
    """Custom encoder to transform set() to list()"""
    def default(self, obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        return json.JSONEncoder.default(self, obj)

folder = Path(__file__).parent

def diff(study_site, device):
    settings = read_json(Path(f'{folder}/src/settings.json'))
    we_are = settings["our_id"]
    
    us = {}
    them = {}
    data = read_json(Path(f'{folder}/src/all_records.json'))["data"]["getStudy"]["files"]
    for item in data:
        d = json.loads(item["description"])
        
        key = d["participantId"]
        value = d["deviceId"]
        
        if key[0] != study_site or device not in value:
            continue
        
        if item["uploadedBy"] == we_are:
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
            #  in them but not in us:
            them_not_us = them[patient] - us[patient]
            if len(them_not_us) > 0:
                result_them[patient] = them_not_us
        else:
            result_them[patient] = them[patient]

    print(f"focussing on studysite {study_site} and device {device}")
    print("\nour account uploaded these sets, where others did not: ")
    print(json.dumps(result_us,cls=SetEncoder,sort_keys=True, indent=4))
    print("\nother uploaded these sets, where we did not: ")
    print(json.dumps(result_them,cls=SetEncoder,sort_keys=True, indent=4))



def view(study_site):
    settings = read_json(Path(f'{folder}/src/settings.json'))
    
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    data = read_json(Path(f'{folder}/src/all_records.json'))["data"]["getStudy"]["files"]
    for item in data:
        d = json.loads(item["description"])
        
        key = d["participantId"]
        
        if key[0] != study_site:
            continue

        value = d["deviceId"]
        
        # get all days which include data (less granular overview...)
        start = date.fromtimestamp(int(d["startDate"])/1000)
        end = date.fromtimestamp(int(d["endDate"])/1000)
        delta = end - start
       
        days_covered = [start + timedelta(days=i) for i in range(delta.days + 1)]
        for day in days_covered:
            result[key][value[:3]][value].add(day.isoformat())
    
    # print(json.dumps(result,cls=SetEncoder,sort_keys=True, indent=4))
    sub_cell = {
        'f' : '',
        't' : '',
        '#' : 0,
    }

    ideafast_patient = {
        'AX6' : sub_cell.copy(),
        'BED' : sub_cell.copy(),
        'BTF' : sub_cell.copy(),
        'DRM' : sub_cell.copy(),
        'IDE' : sub_cell.copy(),
        'MMM' : sub_cell.copy(),
        'SMA' : sub_cell.copy(),
        'TFA' : sub_cell.copy(),
        'VTP' : sub_cell.copy(),
        'YSM' : sub_cell.copy(),
    }

    filtered = defaultdict(lambda: ideafast_patient.copy())
    for patient in result:
        for device_type in result[patient]:
            dates_all = set()
            for device in result[patient][device_type]:
                dates_all.update(result[patient][device_type][device])
            
            dates = sorted(dates_all)
            filtered[patient][device_type] = {
                'f' : dates[0],
                't' : dates[-1],
                '#' : len(result[patient][device_type])
            }

    
    # print(json.dumps(filtered,cls=SetEncoder,sort_keys=True, indent=4))

    # to csv
    csv_file = open(Path(f'{folder}/output/view_{study_site}.csv'), 'w')
    csvwriter = csv.writer(csv_file)

    top_header = ['']
    headers = ['patient_id']
    for key in ideafast_patient.keys():
        top_header.extend(['',key,''])
        headers.extend(['f','t','#'])
    
    csvwriter.writerow(top_header)
    csvwriter.writerow(headers)
    for patient in filtered:
        row = [patient]
        for device in filtered[patient]:
            row.extend(filtered[patient][device].values())

        csvwriter.writerow(row)

    csv_file.close()

    # write_json(Path(f'{folder}/output/view_{study_site}.json'),filtered)
    
if __name__ == "__main__":
    """
    Store a copy of the DMP graphql response (see browser inspector) as all_records.json

    To get an overview of all data on the portal per patient, run     
    
    $ python main.py view [studysite]
    $ python main.py view K      (for example)

    If you want to get the diff between your uploads and others, copy and
    update the 'settings.json' and use

    $ python main.py diff [studysite] [devicetype]
    $ python main.py diff K BTF  (for example)
    """

    task = sys.argv[1]
    study_site = sys.argv[2].upper()

    if task == "view":
        view(study_site)
    elif task == "diff":
        device = sys.argv[3].upper()
        diff(study_site, device)
    else:
        print('unknown command')
    