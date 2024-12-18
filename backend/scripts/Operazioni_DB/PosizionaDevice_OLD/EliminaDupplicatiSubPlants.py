#EliminaDupplicatiSubPlants
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

#from scripts.SharedCode import sharedCode
import sharedCode


# ----------------------------------- START COSTANTI -----------------------------------#  

dictFileName = sharedCode.loadSettings("globalSettings", "mainDictionary")

UploadsFileFolder =  project_root + "\\uploads\\"
auxFilesFolder = sharedCode.loadSettings("globalSettings", "auxFolderPath") 
dictFolder = sharedCode.loadSettings("globalSettings", "dictionaryFolderPath")

dictionary = (sharedCode.dataLoaderJson(project_root + dictFolder, dictFileName, False))
splitRule = sharedCode.loadSettings("globalSettings", "splitRule")

# ----------------------------------- END COSTANTI -----------------------------------# 



def mainFunCall(chosenDB, nomeGalleria):
    try: 

        dbAddress = "MongoProductionClient" if chosenDB == "P" else "MongoQualityClient"
        client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
        currDB = client["smartscada"] 

        currPlant = sharedCode.readDB_wID(currDB, "plant", "", nomeGalleria.upper())
        
        tempPlants = currPlant["subPlants"]
        for plant in tempPlants:
            tempCheckedIdCollection = []
            tempSubPlant = sharedCode.readDB_wID(currDB, "subPlant", plant.id, "")
            newDevicePositions = [] 
            if(tempSubPlant and "devicePositions" in tempSubPlant.keys()):
                print(f"{tempSubPlant["name"]}")
                for devicePosition in tempSubPlant["devicePositions"]:
                    if(devicePosition["deviceId"] not in tempCheckedIdCollection):
                        tempCheckedIdCollection.append(devicePosition["deviceId"])
                        newDevicePositions.append(devicePosition)
                        tempDevice = sharedCode.readDB_wID(currDB, "device", ObjectId(devicePosition["deviceId"]), "")
                        #print(f"Keep:\t{tempDevice["name"]} {devicePosition["deviceId"]} -> {devicePosition}") if tempDevice else print(f"missing: {ObjectId(devicePosition["deviceId"])}")
                    else:
                        tempDevice = sharedCode.readDB_wID(currDB, "device", ObjectId(devicePosition["deviceId"]), "")
                        print(f"toRemove:\t{tempDevice["name"]} {devicePosition["deviceId"]} -> {devicePosition}")

                print(f"{tempSubPlant["name"]} - {len(tempSubPlant["devicePositions"])} > {len(newDevicePositions)}") if(len(tempSubPlant["devicePositions"]) > len(newDevicePositions)) else next
                # uncomment to save
                updateCurrDocumentSubPlant(currDB, "subPlant", ObjectId(tempSubPlant["_id"]), newDevicePositions) 
            else:
                print(f"!!! id >>> {plant.id} <<< non trovato !!!")

        print("Finito")  
    except Exception as e:  
        print(f"An error occurred: {str(e)}:")
        traceback.print_exc()  


def updateCurrDocumentSubPlant(db, collection_name, document_id, devicePositionsArray):
    collection = db[collection_name]
    filter = {"_id": document_id}
    update_data = {"devicePositions": devicePositionsArray}
    result = collection.update_one(filter, {"$set": update_data})
    if result.matched_count == 1:
        0#print("SubPlant document updated successfully")
    else:
        print("SubPlant document not found or not updated",document_id)


if __name__ == '__main__':    
    chosenDB = ""

    nomeGalleria = "MONACO"
    print(project_root)
   # mainFunCall(chosenDB, nomeGalleria)