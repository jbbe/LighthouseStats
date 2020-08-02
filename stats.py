import pandas as pd
import numpy as numpy
import os
import json

def readTrial(df: pd.DataFrame, res_file: str) -> pd.DataFrame: 
    with open(res_file) as f:
        j_obj = json.load(f)
        new_row = {'time': j_obj['fetchTime'], 'url': j_obj['requestedUrl']}
        for entry in j_obj['timing']['entries']:
            print(entry)
            start = entry['name'] + '_start'
            duration = entry['name'] + '_duration'
            new_row[start] = entry['startTime']
            new_row[duration] = entry['duration']
        return df.append(new_row, ignore_index=True)

df = pd.DataFrame()
file_root = 'localhost:7777/'
for file_name in os.listdir(file_root):
    print(file_name)
    if (file_name[-5:] == ".json"):
        df = readTrial(df, file_root + file_name)


