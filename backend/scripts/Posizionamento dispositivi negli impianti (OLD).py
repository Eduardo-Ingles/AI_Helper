
import time
import os, sys, datetime

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.Operazioni_DB.PosizionaDevice_OLD import subPlantDevicePositioner
from backend.scripts.SharedCode import sharedCode


# ----------------------------------- START COSTANTI -----------------------------------#  

x = datetime.datetime.now()
timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")

UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder") + f"{timeStamptFolder}\\"

# ----------------------------------- END COSTANTI -----------------------------------# 

# script
# database
# collection
# subCollection
# galleria
# files

def process_files(sio, client_id, data, script, **kwargs):

    fileName = data.get("files", None)
    chosenDB = data.get("database")        

    available_memory, cpu_usage, percent_ram = sharedCode.check_resources()
    if(fileName):
        start = time.time()  
        for output in subPlantDevicePositioner.mainFunCall(UploadsFileFolder, fileName[0], None, chosenDB, yieldFlag = True):            
            yield output  

        end = time.time()
        minuti = int((end - start)/60)
        secondi = int((end - start) - (minuti *60))
        if(secondi < 10):
            secondi = "0" + str(secondi)
        processing_time_message = f"Tempo elaborazione: {minuti}:{secondi} minuti"
        yield processing_time_message
    else:
        error_message = f"No file found for {fileName}"
        yield error_message
