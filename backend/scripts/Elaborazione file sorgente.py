import time
import os, sys, datetime


project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.Analisi_Elaborazione.MappaturaRMT import analisiSorgente
from backend.scripts.SharedCode import sharedCode

import datetime

# ----------------------------------- START COSTANTI -----------------------------------#  

x = datetime.datetime.now()
timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")

scriptFoldername = "Elaborazione sorgente RMT"

UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder")+ f"{timeStamptFolder}\\"

DownloadsFileFolder = f"{project_root + sharedCode.loadSettings("paths", "downloadsFolder")}{scriptFoldername}\\{timeStamptFolder}\\"

os.makedirs(DownloadsFileFolder, exist_ok=True)

prefix = sharedCode.loadSettings("profilatorSettings", "filePrefix")

CpuCoreNumber = os.cpu_count() 
CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)

# ----------------------------------- END COSTANTI -----------------------------------# 

def process_files(sio, client_id, data, script, **kwargs):
    files = data.get("files", None)
    available_memory, cpu_usage, percent_ram = sharedCode.check_resources()
    if(files and cpu_usage < 90):
        start = time.time()  
        for output in analisiSorgente.mainCall(files, UploadsFileFolder, DownloadsFileFolder, CpuCoreNumber, yieldFlag = True):
            yield output  
        end = time.time()
        processing_time_message = f"Tempo elaborazione: {sharedCode.elapsedTimeFormatted(start, end)}"
        yield processing_time_message
    else:
        error_message = f"No file found for {files}"
        yield error_message