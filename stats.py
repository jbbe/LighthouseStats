import pandas as pd
import numpy as numpy
import os
import re
import json
import subprocess


def readTrial(df: pd.DataFrame, file_path: str) -> pd.DataFrame: 
    with open(file_path) as f:
        j_obj = json.load(f)
        new_row = {'time': j_obj['fetchTime'], 'url': j_obj['requestedUrl']}
        for entry in j_obj['timing']['entries']:
            print(entry)
            start = entry['name'] + '_start'
            duration = entry['name'] + '_duration'
            new_row[start] = entry['startTime']
            new_row[duration] = entry['duration']
        return df.append(new_row, ignore_index=True)

def cleanFilePath(raw_path: str) -> str:
    clean_path = re.sub('\n', '', raw_path)
    return clean_path

def runTrial(url: str) -> str:
    command = ''.join(["node lh.js --silent --url ", url])
    # res = subprocess.check_output(command)
    print(command)
    res = subprocess.run(command, check=True, stdout=subprocess.PIPE, shell=True).stdout
    clean_path = cleanFilePath(res)
    print(clean_path)
    return clean_path


def addTrial(df: pd.DataFrame, url: str) -> pd.DataFrame:
    try:
        file_path = runTrial(url)
        return readTrial(df, file_path)
    except Exception as e:
        return df
        
def initDfFromDir(df: pd.DataFrame, dir_name: str) -> pd.DataFrame:
    for file_name in os.listdir(file_root):
        print(file_name)
        if (file_name[-5:] == ".json"):
            df = readTrial(df, file_root + file_name)
    return df

df = pd.DataFrame()
file_root = 'localhost:7777/'
url = 'https://localhost:7777/'

try:
    df = initDfFromDir(df, file_root)
except OSError as e:
    print(e)

try:
    addTrial(df, url)
except Exception as e:
    print(e)

