import time
import os, sys, datetime


project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.Operazioni_DB.Update_AlrClass import updateDragonfly
from backend.scripts.SharedCode import sharedCode

# ----------------------------------- START COSTANTI -----------------------------------#  

x = datetime.datetime.now()
timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")
UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder") + f"{timeStamptFolder}\\"
DownloadsFileFolder = project_root + sharedCode.loadSettings("paths", "downloadsFolder") + f"Updates Dragonfly\\{timeStamptFolder}\\"

dbLogsPath = DownloadsFileFolder + f"db_update_logs\\"
    
os.makedirs(f"{dbLogsPath}", exist_ok=True)
os.makedirs(f"{DownloadsFileFolder}", exist_ok=True)

prefix = sharedCode.loadSettings("profilatorSettings", "filePrefix")

CpuCoreNumber = os.cpu_count() 
CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)

# ----------------------------------- END COSTANTI -----------------------------------# 

def process_files(sio, client_id, data, script, **kwargs):
    global CpuCoreNumber
    global UploadsFileFolder
    global DownloadsFileFolder
    fileName = data["files"][0].strip() if data["files"] and data["files"][0] else None
     
    available_memory, cpu_usage, percent_ram = sharedCode.check_resources() 
    if(fileName and cpu_usage < 90): 
        time.sleep(3)
        sharedCode.rw_xlsx(file = fileName, path = UploadsFileFolder)
        if(not sharedCode.fileExists(path = UploadsFileFolder, file = fileName) ):
            yield "\n...file non ancora caricato...aspetta..."
            time.sleep(3)
        if(not sharedCode.fileExists(path = UploadsFileFolder, file = fileName) ):
            yield "...aspetta...ancora (5s)... ç_ç"
            time.sleep(5)
        if(not sharedCode.fileExists(path = UploadsFileFolder, file = fileName) ):
            yield "...ultimo tentativo... (10s))"
            time.sleep(10)
            
        chosenDB = data.get("database", "Q")
        clientName = data.get("clientName", None)
        start = time.time()  
        for output in updateDragonfly.mainFunction(CpuCoreNumber, UploadsFileFolder, DownloadsFileFolder, dbLogsPath, fileName, chosenDB, yieldFlag = True, clientName = clientName):
            yield output  
        end = time.time()        
        processing_time_message = f"Tempo elaborazione: {sharedCode.elapsedTimeFormatted(start, end)}"
        
        yield processing_time_message
    else:
        error_message = f"No file found for {fileName}"
        yield error_message