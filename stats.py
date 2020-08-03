import pandas as pd
import numpy as numpy
import os
import re
import math
import sys
import json
import subprocess

metrics = [
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

# Python program to print 
# colored text and background 
def prRed(skk): print("\033[91m {}\033[00m" .format(skk)) 
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk)) 
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk)) 
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk)) 
def prPurple(skk): print("\033[95m {}\033[00m" .format(skk)) 
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk)) 
def prLightGray(skk): print("\033[97m {}\033[00m" .format(skk)) 
def prBlack(skk): print("\033[98m {}\033[00m" .format(skk)) 

def readTrial(df: pd.DataFrame, file_path: str) -> pd.DataFrame: 
    if 'batches.json' in file_path:
        return df
    with open(file_path) as f:
        j_obj = json.load(f)
        end_of_path = file_path.split('/')[-1]
        # print(end_of_path)
        new_row = {'time': j_obj['fetchTime'], 'url': j_obj['requestedUrl'], 'batch': ''}
        if(end_of_path[0] == 'b'):
            new_row['batch'] = end_of_path.split('_')[0]
        for entry in j_obj['timing']['entries']:
            if entry['name'] not in metrics:
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
    # print(clean_path)
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
        if (file_name[-5:] == ".json"):
            df = readTrial(df, dir_name + file_name)
    return df

def runNTrials(n: int, batchName: str, url: str):
    for _ in range(n):
        runTrial(url, batchName=batchName)
    print(f"Succesfully ran {n} trials.")
    
def getBatchMeans(df: pd.DataFrame):
    df2 = df.groupby('batch').mean()
    return df2
    
def getBatchVars(df: pd.DataFrame):
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

def calcPercentageDiff(a, b):
    per = ((b - a) / a) * 100
    return math.floor(per * 100) / 100

def compareBatches(df: pd.DataFrame, batch_a: str, batch_b: str):
    means = df.groupby('batch').mean()
    for col in means.columns:
        percentageDiff = calcPercentageDiff(means[col][batch_a], means[col][batch_b])
        if percentageDiff < 0:
            prRed(f'{batch_a} was ${percentageDiff * -1} % slower than {batch_b}')
        elif percentageDiff == 0:
            prCyan("unchanged")
        else:
            prGreen(f'{batch_a} was ${percentageDiff} % faster than {batch_b}')
    return means

info = "python3 -i stats.py <url> \n run b[batch number] \n comp b[batch number 1] b[batch number 2]"

def main():
    if len(sys.argv) < 3:
        print(info)
        exit(0)
    df = pd.DataFrame()

    url = sys.argv[1]
    file_root = re.sub(r'https://', '', url)
    if sys.argv[2] == "run":
        if(len(sys.argv) != 4):
            print(info)
            exit(0)
        batch_name = sys.argv[3]
        runBatch(batch_name, url, file_root)

    
    df = pd.DataFrame()
    try:
        df = initDfFromDir(df, file_root)
        if sys.argv[2] == "comp":
            if(len(sys.argv) != 5):
                print(info)
                exit(1)
            batch_a = sys.argv[3]
            batch_b = sys.argv[4]
            compareBatches(df, batch_a, batch_b)
    except OSError as e:
        print(e)
    finally:
        return df

if __name__ == "__main__":
    df = main()

