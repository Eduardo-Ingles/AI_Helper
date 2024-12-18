
import sys, os, os.path
import pymongo
import pandas as pd

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, mongoSearch

# ----------------------------------- START COSTANTI -----------------------------------#  

# ----------------------------------- END COSTANTI -----------------------------------# 


def mainCall(nomeGalleria, **kwargs):
    prefix = "_Q_"
    dbAddress = "MongoQualityClient"
    if(("db" in kwargs.keys() and kwargs["db"]) and (kwargs.get("db").upper().startswith("PROD") or kwargs.get("db").upper().startswith("P"))):
        prefix = "_P_"
        dbAddress = "MongoProductionClient" 
        
    client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 

    # YAROT 

    dragonFlyData = []
    currDB = client["scada"] 
    DragonFlyDbData = mongoSearch.readCollectionData(currDB, "scada_widget", name = nomeGalleria, regex = True)
    # DRAGONFLY 

    yarotData = []
    currDB = client["yarot"] 
    YarotDbData = mongoSearch.readCollectionData(currDB, "assets", name = nomeGalleria, regex = True)

    
    for dfData in DragonFlyDbData:
        dragonFlyData.append(dfData["device"]) if "device" in dfData.keys() and dfData["device"] not in dragonFlyData else next

    for dfData in YarotDbData:
        if("lifeCycle" in dfData.keys() and dfData["lifeCycle"] and "READY" in dfData["lifeCycle"].upper()):
            yarotData.append(dfData["name"]) if "name" in dfData.keys() and dfData["name"] not in yarotData else next
        else:
            print(f"Errore: {dfData["name"]}")

    common, uniqA, uniqB = (sharedCode.compareLists(dragonFlyData, yarotData))

    dfCommon = pd.DataFrame(dtype=str)
    dfDF = pd.DataFrame(dtype=str)
    dfYR = pd.DataFrame(dtype=str)

    for index, value in enumerate(common):
        dfCommon.loc[index,"common"] = value

    for index, value in enumerate(uniqA):
        dfDF.loc[index,"OnlyDragonly"] = value

    for index, value in enumerate(uniqB):
        dfYR.loc[index,"OnlyYarot"] = value

    print(f"df: {len(dragonFlyData)}\t-\tyr: {len(yarotData)}\ncomm:{len(common)}\tuniqA: {len(uniqA)}\tuniqB: {len(uniqB)}")
    print("Salvataggio...", sharedCode.rw_xlsx(file = nomeGalleria + prefix, df = {"common": dfCommon, "dragonflyOnly": dfDF, "yarotOnly": dfYR}, mode = "save"))
    

if __name__ == "__main__":      
    #nomeGalleria = "donato"
    #db = "prod"

    #mainCall(nomeGalleria)
    galleria = "start"
    db = input("da quale DB scaricare? (prod / quality):\n").strip()
    while(galleria):
        galleria = input("inserire nome galleria: (end/fine per uscire)\n").strip()
        if(not galleria.lower().startswith("end") and not galleria.lower().startswith("fine")):
            mainCall(galleria, db = db) 
        else:
            galleria = None