#posizionatore
from bson import json_util
import pandas as pd
import traceback 
import sys, os
import re

from datetime import datetime
from bson.dbref import DBRef
from bson import ObjectId
import pymongo
import random

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, mongoSearch


# ----------------------------------- START COSTANTI -----------------------------------#  


#dictFileName = sharedCode.loadSettings("globalSettings", "mainDictionary")
dictFileName = sharedCode.loadSettings("files", "dizionarioMain")

#UploadsFileFolder =  project_root + "\\uploads\\"
#auxFilesFolder = sharedCode.loadSettings("globalSettings", "auxFolderPath") 
#dictFolder = sharedCode.loadSettings("globalSettings", "dictionaryFolderPath")
dictFolder = sharedCode.loadSettings("paths", "dictFolder") 

#dictionary = (sharedCode.dataLoaderJson(project_root + dictFolder, dictFileName, False))
dictionary = (sharedCode.rw_file(path = dictFolder, file = dictFileName))
splitRule = sharedCode.loadSettings("globalSettings", "splitRule")

globalMsg = ""
# ----------------------------------- END COSTANTI -----------------------------------# 


def getDeviceListV2(df):    
    def natural_sort_key(text):
        """Function to extract numerical parts from the device string for natural sorting."""
        return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', text)]
            
    itemList = []
    tempCheckDevice = ""
    tempShow = True
    for index, row in df.iterrows():
        if("NewDevice" in df.columns):
            tempCheckDevice = str(df.at[index, "NewDevice"]) if df.at[index, "NewDevice"] else ""
        elif("deviceName" in df.columns):
            tempCheckDevice = str(df.at[index, "deviceName"]) if df.at[index, "deviceName"] else ""
        elif("device" in df.columns):
            tempCheckDevice = str(df.at[index, "device"]) if df.at[index, "device"] else ""
        tempCheckSubPlant = str(df.at[index, "newSubplant"]) if "newSubplant" in df.columns else ""
        tempX = str(df.at[index, "posX_old"]) if "posX_old" in df.columns and str(df.at[index, "posX_old"]) != "nan" else None
        tempY = str(df.at[index, "posY_old"]) if "posY_old" in df.columns and str(df.at[index, "posY_old"]) != "nan" else None
        tempWidth = str(df.at[index, "width"]) if "width" in df.columns and str(df.at[index, "width"]) != "nan" else None
        tempHeight = str(df.at[index, "height"]) if "height" in df.columns and str(df.at[index, "height"]) != "nan" else None  

        currPk = str(df.at[index, "PK"]) if "PK" in df.columns and str(df.at[index, "PK"]) != "nan" else -1  
        
        # implementare per Edu così non piange e pensa che do priorità a Riccardo. "True" or "False"
        #if("hidden" in df.columns):
        #    tempShow = False if str(df.at[index, "hidden"]) != "nan" and str(df.at[index, "hidden"]) != "" else True   
        if("show" in df.columns or "hidden" in df.columns):
            tempShow = False if str(df.at[index, "hidden"]) != "nan" and str(df.at[index, "hidden"]) != ""  else True
        tempCheckDict = { "device": tempCheckDevice, "newSubplant": tempCheckSubPlant,
                          "posX": tempX, "posY": tempY, "width": tempWidth, "height": tempHeight,
                          "show": tempShow, "pk": currPk} if tempCheckDevice != "" else None
        itemList.append(tempCheckDict) if tempCheckDict not in itemList else next 
        
    itemList.sort(key=lambda x: natural_sort_key(x["device"]) if x["device"] else "")   # se non va colpa di Younes
    return itemList


def devicePlantExtractor(df):
    deviceColumn = "device"
    subPlantColumn = "subplant"
    devicesList = []
    for index, row in df.iterrows():
        tempCheckDevice = str(df.at[index, deviceColumn]) if df.at[index, deviceColumn] else ""
        tempCheckSubPlant = str(df.at[index, subPlantColumn]) if subPlantColumn in df.columns else ""
        tempCheckDict = { deviceColumn: tempCheckDevice, subPlantColumn: tempCheckSubPlant} if tempCheckDevice != "" else None  
        devicesList.append(tempCheckDict) if tempCheckDict not in devicesList else next


def checkDeviceInSP(deviceList, deviceId):
    if(deviceList):
        for itemDevice in deviceList:
            if(deviceId == str(itemDevice["deviceId"])):
                #print(f"found: {device["name"]} [{device["_id"]} | {itemDevice["deviceId"]}] ---> {itemDevice}")
                return True


def mainFunCall(filePath, fileName, sheet, chosenDB, **kwargs):
    yield fileName if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(fileName)
    try: 
        yield("Cercando...") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("Cercando")
        if(chosenDB and chosenDB == "" and "produzione" in fileName.lower()):
            chosenDB = "prod"
        if(filePath != "" and not filePath.endswith("\\")):
            filePath += "\\"    
        df = sharedCode.rw_xlsx(path = filePath, file = fileName, sheets = sheet)

        if("newSubplant" in df.columns):
            devicesArrayDf = getDeviceListV2(df)
            dbAddress = "MongoProductionClient" if chosenDB and "prod" in chosenDB.lower() else "MongoQualityClient"                  
            client = pymongo.MongoClient(sharedCode.loadSettings("dbSettings", dbAddress)) 
            currDB = client["smartscada"] 

            nomeGalleria = fileName.upper().split(" ")[0].strip()
            currPlant = mongoSearch.readCollectionData(currDB, "plant", name = nomeGalleria)
            
            counterSP = 0
            if(currPlant):                
                nomeGalleria = currPlant["name"] if currPlant else None       
                
                for prgrss, PlantSubPlant in enumerate(currPlant["subPlants"]):
                    tempOffset = {"x": 10, "y": 10}
                    currDevPos = {"top": "10", "left": "10"}
                    currIndexes = {"current": 0, "maxElem": len(devicesArrayDf)}
                    subPlant = mongoSearch.readCollectionData(currDB, "subPlant", id = PlantSubPlant.id)
                    counterSP += 1

                    if subPlant:
                        ymex = (f"{counterSP}|{len(currPlant["subPlants"])}: {subPlant["name"]}")
                        yield ymex if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(ymex)

                    if(subPlant and "devicePositions" in subPlant.keys()):
                        tempDevicePositions = subPlant["devicePositions"]               
                        for deviceDf in devicesArrayDf:
                            if(deviceDf["newSubplant"] != None and deviceDf["newSubplant"] != "nan"):
                                tempSubPlantsDf = re.split(r"[,;/]", str(deviceDf["newSubplant"]))
                                for tempSubPlantDf in tempSubPlantsDf:
                                    if(nomeGalleria not in tempSubPlantDf):
                                        tempSubPlantDf = nomeGalleria + "-" + tempSubPlantDf 
                                    if(tempSubPlantDf in subPlant["name"]):                                        
                                        tempDevice = mongoSearch.readCollectionData(currDB, "device", name = deviceDf["device"])
                                        if(tempDevice):                                            
                                            currIndexes["current"] += 1
                                            if(checkDeviceInSP(tempDevicePositions, str(tempDevice["_id"]))):
                                                0#print(f"\tesiste già: {tempDevice["name"]} --->\t{subPlant["name"]}") 
                                            else:                                               
                                                tempGroup = mongoSearch.readCollectionData(currDB, "group", id = ObjectId(subPlant["group"].id))
                                                if(tempGroup):
                                                    tempDevice["associatedGroups"].append(str(tempGroup["name"])) if str(tempGroup["name"]) not in tempDevice["associatedGroups"] else next
                                                    tempDevice["associatedGroupIds"].append(str(tempGroup["_id"])) if str(tempGroup["_id"]) not in tempDevice["associatedGroupIds"] else next
                                                    
                                                    tempPos = devicePositionTemplate_new(currDevPos, str(tempDevice["_id"]), subPlant["name"], deviceDf, currIndexes, yieldFlag = kwargs.get("yieldFlag")) 
                                                    global globalMsg
                                                    if globalMsg != "":
                                                        yield globalMsg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(globalMsg)
                                                        globalMsg = ""
                                                   
                                                    tempDevicePositions.append(tempPos) if not checkDeviceInSP(tempDevicePositions, str(tempDevice["_id"])) else next

                                                    if(deviceDf["show"] == True):       
                                                        tempOffset["x"] += 45
                                                    currDevPos = {"top": str(tempOffset["y"]), "left": str(tempOffset["x"])}  

                                                    if(tempOffset["x"] > 1900):
                                                        tempOffset["x"] = 45
                                                        tempOffset["y"] += 25 if tempOffset["y"] < 900 else 0
                        #""" uncomment to save"""
                                                    updateCurrDocumentDevice(currDB, "device", ObjectId(tempDevice["_id"]), tempDevice)
                        updateCurrDocumentSubPlant(currDB, "subPlant", ObjectId(PlantSubPlant.id), tempDevicePositions) 
                    else:
                        0
                        yield (f"Missing SubPlant id: {PlantSubPlant.id}") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(f"Missing SubPlant id: {PlantSubPlant.id}")
                    
                    msg = sharedCode.progressYield(prgrss + 1, len(currPlant["subPlants"]))
                    if(msg):
                        yield msg
        yield ("Finito")  
    except Exception as e:
        print(f"An error occurred: {str(e)}:")
        yield f"An error occurred: {str(e)}:"
        traceback.print_exc()  


def updateCurrDocumentDevice(db, collection_name, document_id, associatedGroups):
    collection = db[collection_name]
    filter = {"_id": document_id}
    update_dataName = {"associatedGroups": associatedGroups["associatedGroups"]}
    update_dataId = {"associatedGroupIds": associatedGroups["associatedGroupIds"]}
    resultI = collection.update_one(filter, {"$set": update_dataId})
    resultN = collection.update_one(filter, {"$set": update_dataName})
    if resultN.matched_count == 1 and resultI.matched_count == 1:
       0#print("Device document updated successfully")
    else:
        print("Device document not found or not updated", document_id)
    #print("\tGROUP UPDATED", db, collection_name, document_id, associatedGroups)


def updateCurrDocumentSubPlant(db, collection_name, document_id, devicePositionsArray):
    collection = db[collection_name]
    filter = {"_id": document_id}
    update_data = {"devicePositions": devicePositionsArray}
    result = collection.update_one(filter, {"$set": update_data})
    if result.matched_count == 1:
        0#print("SubPlant document updated successfully")
    else:
        print("SubPlant document not found or not updated", document_id)
    #print("\tSubPlant Update", db, collection_name, document_id, devicePositionsArray)

def devicePositionTemplate_new(currDevPos, tempID, currPlant, deviceData, currIndex, **kwargs):
    posLeft = deviceData["posX"] if (deviceData["posX"] and int(deviceData["posX"]) > 10) else currDevPos["left"]
    posTop = deviceData["posY"] if (deviceData["posY"] and int(deviceData["posY"]) > 10) else currDevPos["top"]

    notElectricPlants = ["SINOTTICO-GENERALE", 
                         "IMPIANTO-ILLUMINAZIONE", 
                         "IMPIANTO-RETE-DATI", 
                         "IMPIANTO-RADIO", 
                         "IMPIANTO-SOS", 
                         "IMPIANTO-RILEVAMENTO-INCENDIO", 
                         "IMPIANTO-CANALIZZAZIONE", 
                         "IMPIANTO-VIDEOSORVEGLIANZA", 
                         "IMPIANTO-VENTILAZIONE", 
                         "IMPIANTO-USCITE-DI-SICUREZZA", 
                         ]
    for plant in notElectricPlants:
        if(plant in str(deviceData["newSubplant"]) and ("-INT" in str(deviceData["device"]) or "-SEZ" in str(deviceData["device"]))):
            deviceData["show"] = False

    devicePosition = {
                        "deviceId": tempID,
                        "top": posTop,
                        "left": posLeft,
                        "rotation": "0",
                        "scale": "1",
                        "layers": [],
                        "zIndex": "1",
                        "show": deviceData["show"]
                      }
    global globalMsg
    globalMsg = (f"inserimento:\t{currIndex["current"]}:{currIndex["maxElem"]} > {str(deviceData["device"])} - (x: {posLeft}, y: {posTop}) - [show: {deviceData["show"]}] in -> {currPlant}")# if "-INT" in str(deviceData["device"]) else next
    return devicePosition


if __name__ == '__main__':        
    UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder")
    if(UploadsFileFolder != "" and not UploadsFileFolder.endswith("\\")):
        UploadsFileFolder += "\\"

    chosenDB = ""
    sheet = ""
    filePath = UploadsFileFolder

    file0 = "test-algorab dragonfly_Donato" + ".xlsx"
    file1 = "Valsassina DevicesList_OutputProfili_OutputMappa_Valsassina_dragonfly" + ".xlsx"
    file2 = "OutputMappa_Galleria_ Serraspiga _Esemplificativo_Mappa_PLC_rev0_ANALISI_SINELEC_rev1_1" + ".xlsx"
    file3 = "_import_dispositivi_no_elettrici_ valsassina" + ".xlsx"
    file4 = "LISTA DISPOSITIVI PER IMPORT_DevicesList_OutputProfili_OutputMappa_ Valsassina _dragonfly (1)" + ".xlsx"
    file5 = "TEST_GALLERIA_APPIA file di trest" + ".xlsx"
    file6 = "CILLARESE device list per posizionamento automatico" + ".xlsx"
    file7 = "MONACO _DevicesList_OutputProfili__OutputMappa_Galleria_Monaco_A2_Esemplificativo_Mappa_PLC_2021-06-18_rev0_Merged (1) 1" + ".xlsx"
    
    filesCollection = [file0, file1, file2, file3, file4, file5, file6, file7]

    chosenItem = 7
    
    rndchoice = random.randrange(0, len(filesCollection)) if chosenItem < 0 else chosenItem
    print(filesCollection[rndchoice])

    mainFunCall(filePath, filesCollection[rndchoice], sheet, chosenDB)
    