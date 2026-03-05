import time
import os, sys, datetime

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.Miscelanea import mergeXlsx
from backend.scripts.SharedCode import sharedCode

import datetime

# ----------------------------------- START COSTANTI -----------------------------------#  

x = datetime.datetime.now()
timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")
UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder") + f"{timeStamptFolder}\\"
DownloadsFileFolder = project_root + sharedCode.loadSettings("paths", "downloadsFolder") + f"Unisci file excel\\{timeStamptFolder}\\"

os.makedirs(f"{DownloadsFileFolder}", exist_ok=True)

prefix = sharedCode.timeStamp()

CpuCoreNumber = os.cpu_count() 
CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)

dividers = ["/", "\\", ",", ";"]

# ----------------------------------- END COSTANTI -----------------------------------# 


def process_files(sio, client_id, data, script, **kwargs):
    global CpuCoreNumber
    global UploadsFileFolder
    global DownloadsFileFolder
    
    files = data.get("files", None)  
    if(UploadsFileFolder != "" and not UploadsFileFolder.endswith("\\")):
        UploadsFileFolder += "\\"
    if(DownloadsFileFolder != "" and not DownloadsFileFolder.endswith("\\")):
        DownloadsFileFolder += "\\"
    available_memory, cpu_usage, percent_ram  = sharedCode.check_resources()
    if(files and cpu_usage < 90):
        time.sleep(3)
        sharedCode.rw_xlsx(file = files[0], path = UploadsFileFolder)
        if(not sharedCode.fileExists(path = UploadsFileFolder, file = files[0]) ):
            yield "\n...file non ancora caricato...aspetta..."
            time.sleep(3)
        if(not sharedCode.fileExists(path = UploadsFileFolder, file = files[0]) ):
            yield "...aspetta...ancora (5s)... ç_ç"
            time.sleep(5)
        if(not sharedCode.fileExists(path = UploadsFileFolder, file = files[0]) ):
            yield "...ultimo tentativo... (10s))"
            time.sleep(10)
        yield data, percent_ram
        excludedSheets = data.get("galleria", "")
        excludeSheetsList = []      
        #yield(f"Sheet da escludere: {str(excludedSheets)}\n\nFile da elaborare: {files}\n")
        start = time.time()          
        if(excludedSheets.strip() != "" and excludedSheets.strip() != "  "):
            for divier in dividers:
                if(divier in excludedSheets):
                    excludedSheets = excludedSheets.replace(divier, ";")
            if(";") in excludedSheets:
                excludeSheetsList = excludedSheets.strip().split(";")  
            elif(excludedSheets != ""):
                excludeSheetsList.append(excludedSheets)
        
        for output in mergeXlsx.mainCall(UploadsFileFolder, DownloadsFileFolder, files, prefix, yieldFlag = True, excludeSheets = excludeSheetsList):
            yield output  
        end = time.time()
        processing_time_message = f"Tempo elaborazione: {sharedCode.elapsedTimeFormatted(start, end)}"
        yield processing_time_message
    else:
        error_message = f"No file found for {files}"
        yield error_message