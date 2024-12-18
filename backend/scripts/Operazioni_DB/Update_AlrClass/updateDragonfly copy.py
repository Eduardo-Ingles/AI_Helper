import pandas as pd
import traceback 
import sys, os, os.path
import pymongo
from bson.dbref import DBRef
from bson import ObjectId
from bson import json_util
import time
import json


project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, mongoSearch

# ----------------------------------- START COSTANTI -----------------------------------#  

# ----------------------------------- END COSTANTI -----------------------------------# 



def findPlant(nomeGalleria, chosenDB):
    dbAddress = "MongoProductionClient" if chosenDB.startswith("PROD") or chosenDB.startswith("P") else "MongoQualityClient"
    client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
    currDB = client["scada"] 
    extractedData = mongoSearch.readCollectionData(currDB, "scada_system", name = nomeGalleria, regex = True)
    foundItems = []
    for indx, item in enumerate(extractedData):
        foundItems.append(item)

    if(len(foundItems) > 1):
        for indx, item in foundItems:        
            print(f"{indx}:>\t {item["name"]}")
        return foundItems[int(input("Indice della galleria da utilizzare: \t"))]
    else:
        return foundItems[0] if foundItems[0] else None




def filterData(shared_data):
    def findKeys(elementZ):
        """Ricerca le chiavi "_NEW" su cui fare l'update"""
        keyList = []
        for key in elementZ.keys():
            if(key.endswith("_NEW")):
                kpair = {"old": key.replace("_NEW",""), "new": key}
                keyList.append(kpair) if kpair not in keyList else next
        return keyList
    
    itemPairs = []
    if(shared_data):
        refkeys = findKeys(shared_data[0])
        if(refkeys):
            for item in shared_data:
                for rkpair in refkeys:     
                    if(rkpair["old"] in item.keys() and rkpair["new"] in item.keys()):                   
                        kval = {"tagName": item["tagName"],"target": rkpair["old"], "data": {"old": item[rkpair["old"]], "new": item[rkpair["new"]]}} #WidgetName
                        itemPairs.append(kval) if kval not in itemPairs and kval["data"]["new"] != "" else next
    return itemPairs
    

def mainFunction(CpuCoreNumber, UploadsFileFolder, DownloadsFileFolder, fileName, chosenDB, **kwargs):
    try:
        yieldFlag = True if kwargs.get("yieldFlag") and kwargs.get("yieldFlag") else False
        
        msg = f"Loading file"
        yield msg if yieldFlag else print(msg)
        
        df = sharedCode.rw_xlsx(file = fileName, path = UploadsFileFolder)
        
        rawRows = df.apply(lambda row: json.dumps({col: str(row[col]) for col in df.columns}), axis=1).tolist()
        shared_data = []
        for row in rawRows:
            tempData = json.loads(row)
            for key, value in tempData.items():
                if(value == "nan"):
                    tempData[key] = ""
            shared_data.append(tempData)
            
        itemPairs = filterData(shared_data)
        #for ite in itemPairs:
        #    yield(ite)
        #    print(ite)
        #print(len(itemPairs))
        
        
        dbAddress = "MongoProductionClient" if chosenDB.startswith("PROD") or chosenDB.startswith("P") else "MongoQualityClient"
        client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
        currDB = client["scada"] 
        
        #yield(client, chosenDB) if yieldFlag else print(client, chosenDB)
        

        scada_tag = ["tagDevice", "tagName", "tagDescription"]
        scada_widget = ["WidgetName", "WidgetDescription", "widgetArchetype", "widgetDevice"]
        currCollection = ""
        print(f"\n{40*"-"}\n")
        for item in itemPairs:  
            querry = ""  
            target = ""        
            if(sharedCode.any_AinB(item["target"], scada_tag)):
                currCollection = "scada_tag"
                if ("tagDescription" in item["target"]):
                    target = "description" 
                elif("alarmClass" in item["target"]):
                    target = "alarmClass"
                elif("tagDevice" in item["target"]):
                    target = "tagDevice"
                elif("tagName" in item["target"]):
                    target = "name"    
                                    
                if(target != ""):
                    querry = {"name": item["tagName"], target: item["data"]["old"]}
                    
            if(sharedCode.any_AinB(item["target"], scada_widget)):
                currCollection = "scada_widget"
                if ("WidgetName" in item["target"]):
                    target = "name" 
                elif ("WidgetDescription" in item["target"]):
                    target = "description" 
                elif ("widgetArchetype" in item["target"]):
                    target = "archetype" 
                elif ("widgetDevice" in item["target"]):
                    target = "device"  
                                    
                if(target != ""):
                    querry = {"name": item["WidgetName"], target: item["data"]["old"]}
                

            if(querry!= "" and currCollection != ""):
                results = (mongoSearch.findCollectionData(currDB, currCollection, querry = querry))
                for result in results:
                    yield (f"{result["name"]} - {target}: {result[target]} --> {item}") if yieldFlag else print(f"{result["name"]} - {target}: {result[target]} --> {item}")
                    searchQuerry = {"name": item["tagName"], target: item["data"]["old"]}
                    updateQuerry = {target: item["data"]["new"]}
                    msg = (mongoSearch.updateOne(currDB, currCollection, searchQuerry = searchQuerry, updateQuerry = updateQuerry ))
                    yield msg if yieldFlag else print(msg)
                    yield " " if yieldFlag else print() 
        print(len(itemPairs))
            #input("---")
        #print(itemPairs[0].keys())
        #for item in itemPairs:
        #    yield item if yieldFlag else print(item)
        #    if(sharedCode.any_AinB(item["target"], scada_tag)):
        #        currKey = "device"
        #        currCollection = "scada_tag"
        #        extractedTagData = mongoSearch.findCollectionData(currDB, currCollection, key = currKey, value = item["data"]["old"])
        #    
        #        if(extractedTagData):   
        #            result = (mongoSearch.updateOne(currDB, currCollection, key = currKey, oldValue = item["data"]["old"], newValue = item["data"]["new"]))
        #            yield result if yieldFlag else print(result)
        #             
        #        
        #    if(sharedCode.any_AinB(item["target"], scada_widget)):
        #        currKey = "name"
        #        currCollection = "scada_widget"
        #        extractedWidgetData = mongoSearch.findCollectionData(currDB, currCollection, key = currKey, value = item["data"]["old"])
        #        if(extractedWidgetData): 
        #            result = (mongoSearch.updateOne(currDB, currCollection, key = currKey, oldValue = item["data"]["old"], newValue = item["data"]["new"]))
        #            yield result if yieldFlag else print(result)
           
        
        
               
    except Exception as e:
        print(f"An error occurred: {str(e)}:")
        traceback.print_exc()  
        
    

    
if __name__ == "__main__":
    currUploadsFolder = project_root + "\\scripts\\Analisi_Elaborazione\\MappaturaDragonfly\\File Elaborati\\"
    currDownloadsFolder =  currUploadsFolder#project_root + "\\scripts\\Analisi_Elaborazione\\MappaturaDragonfly\\File Elaborati\\"
    
    currUploadsFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder")
    currDownloadsFolder = project_root + sharedCode.loadSettings("paths", "downloadsFolder")

    CpuCoreNumber = 1
    chosenDB = "Q"
    fileName = "dragonfly_P_Jannello--Con modifiche da apportare Claudiu - Copia.xlsx"
    start = time.time()
    cnt = 0
    for output in mainFunction(CpuCoreNumber, currUploadsFolder, currDownloadsFolder, fileName, chosenDB):
        0
    end = time.time()
    
    print(sharedCode.elapsedTimeFormatted(start, end))
    