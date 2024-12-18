import pymongo
import pandas as pd
from bson import ObjectId 
import os, sys
import re

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, mongoSearch 

# ----------------------------------- START COSTANTI -----------------------------------#  
errorsList = []
splitList = sharedCode.loadSettings("globalSettings", "dividers")
prefisso = sharedCode.loadSettings("profilesDeviceSettings", "prefix")

# ----------------------------------- END COSTANTI -----------------------------------# 


def mainCall(nomeGallerie, UploadsFileFolder, DownloadsFileFolder, auxName, chosenDB, elabChoice, **kwargs):
    links = []
    yield {"progress": 0}
    if not nomeGallerie:
        return None
    
    for item in splitList:
        if(item in nomeGallerie):
            nomeGallerie.replace(item, ",")    
    if(isinstance(nomeGallerie,str)):
        nomeGallerie = nomeGallerie.strip().split(",")
    else:
        nomeGallerie = nomeGallerie.strip().split()
        
    prefix = f"{elabChoice}_Q_"
    dbAddress = "MongoQualityClient"
    if(chosenDB.upper().startswith("PROD") or chosenDB.upper().startswith("P")):
        prefix = f"{elabChoice}_P_"
        dbAddress = "MongoProductionClient"
    
    savename = f"{prefisso}_{elabChoice}_{chosenDB}_{"-".join(nomeGallerie)}_{sharedCode.timeStamp(fullDate = True)}.xlsx"
        
    client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
    currDB = client["smartscada"] 
           
    dataHolder = []
    for galleria in nomeGallerie:
        galleria = galleria.strip().capitalize()          
        #dataHolder = []
        msg = f"Scaricamento {elabChoice} -> {galleria}\tdb:{chosenDB}\tdbAddress: {dbAddress}\tprefix: {prefix}"
        yield msg if kwargs.get("yieldFlag") else print(msg)
        
        if("profili" in elabChoice.lower()):
            collectionName = "deviceProfile"  
            #yield(f"collectionName: {collectionName}\tgalleria: {galleria}") if kwargs.get("yieldFlag") else print(f"galleria: {galleria}\n")
            extractedData = mongoSearch.readCollectionData(currDB, collectionName, name=galleria.strip(), regex = True)   
            
            if extractedData:
                for data in extractedData:
                    if galleria.strip().upper() in data["name"]:
                        #yield(currItem) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(currItem)
                        tempSignals = []
                        if "signals" in data.keys():
                            for signal in data["signals"]:
                                alrClass = {}
                                if "properties" in signal.keys() and signal["properties"]:
                                    if "alarm" in signal["properties"].keys() and signal["properties"]["alarm"]:
                                        if "name" in signal["properties"]["alarm"].keys() and signal["properties"]["alarm"]["name"]:
                                            alrClass["name"] = signal["properties"]["alarm"]["name"]
                                        if "description" in signal["properties"]["alarm"].keys() and signal["properties"]["alarm"]["description"]:
                                            alrClass["description"] = signal["properties"]["alarm"]["description"]
                                    if "thresholds" in signal["properties"].keys() and signal["properties"]["thresholds"]:
                                        for indx, thresholds in enumerate(signal["properties"]["thresholds"]):
                                            if "alarmLevel" in thresholds.keys() and thresholds["alarmLevel"]:
                                                alrClass[f"alarmLevel_{indx}"] = thresholds["alarmLevel"]
                                            if "label" in thresholds.keys() and thresholds["label"]:
                                                alrClass[f"label_{indx}"] = thresholds["label"]
                                            if "lower" in thresholds.keys() and thresholds["lower"]:
                                                alrClass[f"lower_{indx}"] = thresholds["lower"]
                                            if "upper" in thresholds.keys() and thresholds["upper"]:
                                                alrClass[f"upper_{indx}"] = thresholds["upper"]
    
                                tempSignal = {"name": signal["name"], "description": signal["description"], "alrClass": alrClass}
                                if tempSignal not in tempSignals:
                                    tempSignals.append(tempSignal)
    
                        tempDict = {"name": data["name"], "signals": tempSignals}
                        if tempDict and tempDict not in dataHolder:
                            dataHolder.append(tempDict)

            else:
                msg = (f"{galleria} non trovato all'interno del DB!")            
                yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
             
        elif("dispositivi" in elabChoice.lower()):
            collectionName = "device"
            yield(f"collectionName: {collectionName}\tgalleria: {galleria}") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(f"galleria: {galleria}\n")
            extractedData = mongoSearch.findCollectionData(currDB, collectionName, key = "name", value = galleria, regex = True)
            if extractedData:
                for data in extractedData:
                    #yield(data["name"]) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(data["name"])
                    if("profileName" in data.keys() and  galleria.strip().upper() in data["profileName"]):
                        #yield(currItem) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(currItem)
                        tempSignals = []
                        if("signalConfigurations" in data.keys() and data["signalConfigurations"]):
                            for signal in data["signalConfigurations"]:
                                attributi = signal["attributes"] if "attributes" in signal.keys() else None
                                signalName = signal["signalName"] if "signalName" in signal.keys() else ""
                                signalDescription = ""                                
                                disabled = signal.get("disabled", True)
                                if("signalStates" in data.keys()):
                                    signalDescription = data["signalStates"][signalName]["description"] if signalName in data["signalStates"].keys() else ""
                                driverInstance = signal["driverInstance"] if "driverInstance" in signal.keys() else ""  
                                tempSignal = {"name": signalName, "description": signalDescription, "driverInstance": driverInstance, "profileName": data["profileName"], "attributi": attributi, "disabled": disabled}
                               
                                if tempSignal not in tempSignals:
                                    tempSignals.append(tempSignal)
                        tempDict = {"device": data["name"], "signals": tempSignals}
                        if tempDict and tempDict not in dataHolder:
                            dataHolder.append(tempDict)
            else:
                msg = (f"{galleria} non trovato all'interno del DB!")
                yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
        else:
            yield f"Errore nel trovare i dati! {elabChoice}"
            
    if(dataHolder):
        msg = f"\nElaborazione {len(dataHolder)} elementi..."
        yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
        df = pd.DataFrame(dtype=str)
        rowCount = 0
        for indx, device in enumerate(dataHolder):
            if("profili" in elabChoice.lower()):
                df.loc[rowCount, "Profilo"] = device["name"]
                if "signals" in device.keys():
                    for signal in device["signals"]:
                        df.loc[rowCount, "Profilo"] = device["name"]
                        df.loc[rowCount, "Segnale"] = signal.get("name", "")
                        df.loc[rowCount, "Descrizione"] = signal.get("description", "")
                        df.loc[rowCount, "AlrClass"] = signal["alrClass"].get("name", "")
                        df.loc[rowCount, "AlrClassDescription"] = signal["alrClass"].get("description", "")
                        df.loc[rowCount, "soglia_0_allarme"] = signal["alrClass"].get("alarmLevel_0", "")
                        df.loc[rowCount, "soglia_0_tipo"] = signal["alrClass"].get("label_0", "")
                        df.loc[rowCount, "soglia_0_valoreMinimo"] = signal["alrClass"].get("lower_0", "")
                        df.loc[rowCount, "soglia_0_valoreMassimo"] = signal["alrClass"].get("upper_0", "")
                        df.loc[rowCount, "soglia_1_allarme"] = signal["alrClass"].get("alarmLevel_1", "")
                        df.loc[rowCount, "soglia_1_tipo"] = signal["alrClass"].get("label_1", "")
                        df.loc[rowCount, "soglia_1_valoreMinimo"] = signal["alrClass"].get("lower_1", "")
                        df.loc[rowCount, "soglia_1_valoreMassimo"] = signal["alrClass"].get("upper_1", "")
                        rowCount += 1
                else:
                    rowCount += 1
            if("dispositivi" in elabChoice.lower()):
                df.loc[rowCount, "Device"] = device["device"]                            
                if "signals" in device.keys():
                    for signal in device["signals"]:
                        df.loc[rowCount, "Profilo"] = signal.get("profileName", "")
                        df.loc[rowCount, "Device"] = device["device"]
                        df.loc[rowCount, "Segnale"] = signal.get("name", "")
                        df.loc[rowCount, "Descrizione"] = signal.get("description", "")
                        df.loc[rowCount, "dataSource"] = signal.get("driverInstance", "")
                        df.loc[rowCount, "disabled"] = signal.get("disabled", "")
                        attributi = signal.get("attributi")
                        if(attributi):
                            for attributo in attributi:
                                if("register" in attributo["name"]):
                                    df.loc[rowCount, "register"] = attributo["value"] if "value" in attributo.keys() else ""
                                if("dataType" in attributo["name"]):
                                    df.loc[rowCount, "dataType"] = attributo["value"] if "value" in attributo.keys() else ""
                                if("bitIndex" in attributo["name"]):
                                    df.loc[rowCount, "bitIndex"] = attributo["value"] if "value" in attributo.keys() else ""
                                if("registerType" in attributo["name"]):
                                    df.loc[rowCount, "registerType"] = attributo["value"] if "value" in attributo.keys() else ""                                            
                                if("offset" in attributo["name"]):
                                    df.loc[rowCount, "offset"] = attributo["value"] if "value" in attributo.keys() else ""
                                if("slaveId" in attributo["name"]):
                                    df.loc[rowCount, "slaveId"] = attributo["value"] if "value" in attributo.keys() else ""
                        rowCount += 1
                else:
                    rowCount += 1
            msg  = sharedCode.progressYield(indx+1, len(dataHolder))
            if(msg):
                yield msg
                
        msg = (f"Salvataggio...{savename}: {sharedCode.rw_xlsx(path = DownloadsFileFolder, file = savename, df = df , mode = "save")}")
        yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
                    
        pathMsg = f"""<a href="downloads/{savename+ ".xlsx"}">{savename}</a><br>""" #if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else "! Check Folder !"
        #yield(pathMsg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(pathMsg)  
        ylink = {"link": f"{DownloadsFileFolder}{savename}", "linkName": f"{savename}"}
        
        links.append(ylink) if ylink not in links else next
        yield  {"links": links} 
        yield ""
    
if __name__ == "__main__":     
    nomeGalleria = "donato"
    currUploadsFolder = project_root + "\\downloads\\"
    currDownloadsFolder =  currUploadsFolder#project_root + "\\scripts\\Analisi_Elaborazione\\MappaturaDragonfly\\File Elaborati\\"
    auxName = ""
    chosenDB = "Q"
    elabChoice = "device"
            
    for output in mainCall(nomeGalleria, currUploadsFolder, currDownloadsFolder, auxName, chosenDB, elabChoice, yieldFlag = True):
        print(f"{output}")