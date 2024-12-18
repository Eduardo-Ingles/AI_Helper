# PosizionaDevice
import time
import os, sys, datetime

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.Operazioni_DB.dbDownloaders import confrontiYarot
from backend.scripts.SharedCode import sharedCode


# ----------------------------------- START COSTANTI -----------------------------------#  

x = datetime.datetime.now()
timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")

UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder") + f"{timeStamptFolder}\\"
DownloadsFileFolder = project_root + sharedCode.loadSettings("paths", "downloadsFolder") + f"Confronti Yarot\\{timeStamptFolder}\\"

os.makedirs(f"{DownloadsFileFolder}", exist_ok=True)

CpuCoreNumber = os.cpu_count() 
CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)

# ----------------------------------- END COSTANTI -----------------------------------# 


def process_files(sio, client_id, data, script, **kwargs):
    global CpuCoreNumber
    available_memory, cpu_usage, percent_ram = sharedCode.check_resources()
    nomeGalleria = data.get("galleria", None)
    chosenDB = data.get("database")
    collectionSelector = data.get("collection")    
    if(nomeGalleria and cpu_usage < 90):        
        start = time.time()  
        for output in confrontiYarot.mainCall(nomeGalleria, UploadsFileFolder, DownloadsFileFolder, CpuCoreNumber, chosenDB, collectionSelector, yieldFlag = True):
            yield output  
        end = time.time()
        processing_time_message = f"Tempo elaborazione: {sharedCode.elapsedTimeFormatted(start, end)}"
        yield processing_time_message
    else:
        error_message = f"No gallery found for {nomeGalleria}"
        yield error_message