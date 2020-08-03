import pandas as pd
import numpy as numpy
import os
import re
import sys
import json
import subprocess

metricFilter = [
    "lh:computed:first-contentful-paint",
    "lh:computed:first-meaningful-paint",
    "lh:audit:speed-index",
    "lh:audit:estimated-input-latency",
    "lh:audit:total-blocking-time",
    "lh:audit:max-potential-fid",
    "time-to-first-byte",
    "lh:audit:first-cpu-idle",
    "lh:audit:interactive"
]


def readTrial(df: pd.DataFrame, file_path: str) -> pd.DataFrame: 
    if 'batches.json' in file_path:
        return df
    with open(file_path) as f:
        j_obj = json.load(f)
        end_of_path = file_path.split('/')[-1]
        print(end_of_path)
        new_row = {'time': j_obj['fetchTime'], 'url': j_obj['requestedUrl'], 'batch': ''}
        if(end_of_path[0] == 'b'):
            new_row['batch'] = end_of_path.split('_')[0]
        for entry in j_obj['timing']['entries']:
            if entry['name'] not in metricFilter:
                continue
            # print(entry)
            start = entry['name'] + '_start'
            duration = entry['name'] + '_duration'
            new_row[start] = entry['startTime']
            new_row[duration] = entry['duration']
        return df.append(new_row, ignore_index=True)


def cleanFilePath(raw_path: str) -> str:
    clean_path = re.sub('\n', '', raw_path)
    return clean_path


def runTrial(url: str, batchName: str = '') -> str:
    if(batchName):
        command = ''.join(["node lh.js --silent --url ", url, " --batchName ", batchName])
    else:
        command = ''.join(["node lh.js --silent --url ", url])
    print(command)
    res = subprocess.run(command, check=True, stdout=subprocess.PIPE, shell=True).stdout
    clean_path = cleanFilePath(str(res))
    print(clean_path)
    return clean_path


def addTrial(df: pd.DataFrame, url: str) -> pd.DataFrame:
    try:
        file_path = runTrial(url)
        return readTrial(df, file_path)
    except Exception as e:
        print("Adding trial failed", e)
        return df
        
def initDfFromDir(df: pd.DataFrame, dir_name: str) -> pd.DataFrame:
    for file_name in os.listdir(dir_name):
        print(file_name)
        if (file_name[-5:] == ".json"):
            df = readTrial(df, dir_name + file_name)
    return df

def runNTrials(n: int, batchName: str, url: str):
    for _ in range(n):
        runTrial(url, batchName=batchName)
    print(f"Succesfully ran {n} trials.")
    
def getBatchMeans(df: pd.DataFrame):
    var_df = df.groupby('batch').mean()
    return var_df
    

def runBatch(batchName: str, url: str, file_root: str):
    batch_file_path = file_root + 'batches.json'
    if not os.path.exists(file_root):
        os.mkdir(file_root)
    if os.path.exists(batch_file_path):
        with open(batch_file_path, 'r+', encoding='utf-8') as f:
            batches = json.load(f)
            batches['batches'].append(batchName)
        os.remove(batch_file_path)
        with open(batch_file_path, 'w', encoding='utf-8') as f:
            json.dump(batches, f, indent=4)
    else:
        with open(batch_file_path, 'w', encoding='utf-8') as f:
            json.dump({"batches" : [batchName]}, f, indent=4)
    runNTrials(4, batchName, url)


def main():
    if len(sys.argv) < 3:
        print("URL needed")
        exit(0)
    df = pd.DataFrame()

    url = sys.argv[1]
    file_root = re.sub(r'https://', '', url)
    if sys.argv[2] == "run":
        if(len(sys.argv) != 4):
            print("URL needed")
            exit(0)

        batch_name = sys.argv[3]
        runBatch(batch_name, url, file_root)
    df = pd.DataFrame()
    try:
        df = initDfFromDir(df, file_root)
    except OSError as e:
        print(e)
    finally:
        return df

if __name__ == "__main__":
    df = main()

