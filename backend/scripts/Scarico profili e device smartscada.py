# PosizionaDevice
import time
import os, sys, datetime

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.Operazioni_DB.dbDownloaders import profileDeviceDownloader
from backend.scripts.SharedCode import sharedCode


# ----------------------------------- START COSTANTI -----------------------------------#  

x = datetime.datetime.now()
timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")
UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder") + f"{timeStamptFolder}\\"
DownloadsFileFolder = project_root + sharedCode.loadSettings("paths", "downloadsFolder") + f"Scarico Profili & Devices\\{timeStamptFolder}\\"

os.makedirs(f"{DownloadsFileFolder}", exist_ok=True)

CpuCoreNumber = os.cpu_count() 
CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)

# ----------------------------------- END COSTANTI -----------------------------------# 

# script
# database
# collection
# subCollection
# galleria
# files

def process_files(sio, client_id, data, script, **kwargs):
    global CpuCoreNumber
    available_memory, cpu_usage, percent_ram = sharedCode.check_resources()
    nomeGalleria = data.get("galleria", None)
    if(nomeGalleria and cpu_usage < 70):
        auxName = "dragonfly"
        chosenDB = data.get("database", None)
        yield {"stream": f"DEBUG - chosenDB ricevuto: '{chosenDB}'\n"}
        if chosenDB == "MomsTest": chosenDB = "MomsTest" 
        elabChoice = data.get("subCollection", "Dispositivi") # default = DEVICE
        nomeGalleria = nomeGalleria.replace("$PROD$","").strip() if("$PROD$" in nomeGalleria.upper()) else nomeGalleria.strip()
        start = time.time()  
        fileAnagrafica = None
        for output in profileDeviceDownloader.mainCall(nomeGalleria, UploadsFileFolder, DownloadsFileFolder, auxName, chosenDB, elabChoice, yieldFlag = True):
            yield output  # Yield output for further processing
        auxName += f"_{chosenDB}_"
        end = time.time()
        processing_time_message = f"Tempo elaborazione: {sharedCode.elapsedTimeFormatted(start, end)}"
        yield processing_time_message         
    else:        
        error_message = f"Nessuna galleria trovata per: {nomeGalleria}"
        yield error_message


       
