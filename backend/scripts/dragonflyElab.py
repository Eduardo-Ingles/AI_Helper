
import asyncio
 
import time
import os, sys, datetime

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.Analisi_Elaborazione.MappaturaDragonfly import dragonflyPorter
from backend.scripts.SharedCode import sharedCode


import datetime


# ----------------------------------- START COSTANTI -----------------------------------#  

x = datetime.datetime.now()
timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")
scriptFoldername = "Scarichi ed Elaborazione Dragonfly"

skipScriptExtraction = False
soloScarico = False

UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder") + f"{timeStamptFolder}\\"
DownloadsFileFolder = f"{project_root + sharedCode.loadSettings("paths", "downloadsFolder")}{scriptFoldername}\\{timeStamptFolder}\\"

os.makedirs(DownloadsFileFolder, exist_ok=True)
os.makedirs(f"{DownloadsFileFolder}\\scriptsFolder\\", exist_ok=True)

CpuCoreNumber = os.cpu_count() 
CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)

divider = sharedCode.loadSettings("globalSettings", "dividers")

# ----------------------------------- END COSTANTI -----------------------------------# 

def process_files(sio, client_id, data, script, **kwargs):
    global CpuCoreNumber
    nomeGalleria = data["galleria"]
    
    gallerie = None
    for divy in divider:
        if(divy in nomeGalleria):
            gallerie = nomeGalleria.strip().split(divy)
    if(not gallerie or (gallerie and len(gallerie) == 0)):
        gallerie = nomeGalleria.strip().split()
    
    for galleria in gallerie:         
        available_memory, cpu_usage, percent_ram = sharedCode.check_resources()
        if(galleria and cpu_usage < 70 and percent_ram < 70):
            auxName = "dragonfly" 
            chosenDB = data.get("database", "Q")
            start = time.time()  
            fileAnagrafica = None
            for output in dragonflyPorter.mainCall(galleria, UploadsFileFolder, DownloadsFileFolder, fileAnagrafica, auxName, CpuCoreNumber, chosenDB, soloScarico = False, yieldingFlag = True, client_id = client_id, sio = sio ):
                yield output
            end = time.time()
            processing_time_message = f"Tempo elaborazione: {sharedCode.elapsedTimeFormatted(start, end)}"
            yield processing_time_message
            yield {"status": "completed"}
        else:
            error_message = f"No gallery found for {galleria}"
            yield error_message
            yield({"status": f"failed: {error_message}"})


       

       
