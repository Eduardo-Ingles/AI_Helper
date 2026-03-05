

import pandas as pd
import sys, os
import pymongo
from bson import ObjectId
from bson.dbref import DBRef

project_root = os.getcwd()
sys.path.append(project_root)

#from scripts.SharedCode import sharedCode, rulesDefiner, normalizeData

# ----------------------------------- START COSTANTI -----------------------------------#  

currFileFolder =  project_root + "/" #+ "\\exportsDb\\"

# ----------------------------------- END COSTANTI -----------------------------------# 
# auto-py-to-exe
# pyinstaller ScaricoProfiliAlrClass.py --onefile
# pyinstaller ScaricoProfiliAlrClass.spec


def progress(count, total, status = ''):                                                                  
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush() 


def readCollectionData(currentDB, collectionName:str, **kwargs):

    id = kwargs.get("id")
    name = kwargs.get("name")
    description= kwargs.get("description")
    query = {}
    collection = currentDB[collectionName] # Find all the documents in the collection
    if(not id and not name == "" and not description):
        result = collection.find()                          #find() returns a cursor
    elif(id and not name == "" and not description):
        result = collection.find_one({"_id": ObjectId(id)})
    elif(not id and name == "" and not description):
        result = collection.find({"name": name.upper()}) 
    elif(not id and not name == "" and description):
        result = collection.find_one({"description": description}) 
    return result



def loadPlant(extractedData):    
    foundPlants = []
    for plant in extractedData:
        if(galleria.upper() in plant["name"]):
            foundPlants.append(plant) if plant not in foundPlants else next

    choice = 0
    if(foundPlants and len(foundPlants) > 1):
        for index, fplant in enumerate(foundPlants):
            print(f"{index} {fplant["name"]}")
        choice = int(input("Scelta:> "))    
        print(f"Galleria selezionata: {foundPlants[choice]["name"]} - {foundPlants[choice]["description"]}")
    
    return foundPlants[choice] if len(foundPlants) != 0 else None


def loadSubPlants(currDB, idsList):
    collectionName = "subPlant"
    subPlants = []
    for id in idsList:
        #extractedData = sharedCode.readCollectionData(currDB, collectionName, id = id)
        extractedData = readCollectionData(currDB, collectionName, id = id)
        #print(extractedData["name"])
        subPlants.append(extractedData) if extractedData not in subPlants else next 

    return subPlants if len(subPlants) != 0 else None



def mainCall(galleria, **kwargs):

    dbAddress = "MongoQualityClient"
    db = kwargs.get("db")
    if(db and "prod" in db):
        dbAddress = "mongodb://root:abc123!@rmt-p-nosql1-1.anasnet.it:27017,rmt-p-nosql1-2.anasnet.it:27017,rmt-p-nosql1-3.anasnet.it:27017/?replicaSet=rs1&authSource=admin"
    elif ( db and "moms" in db.lower()): 
        dbAddress="mongodb://10.86.20.54:27017"
    else:
        dbAddress = "mongodb://rmtqual:H2Fnv3QAP4%3FB@rmt-q-nosql1-1.anasnet.it,rmt-q-nosql1-2.anasnet.it,rmt-q-nosql1-3.anasnet.it/?replicaSet=rmtqualRS&readPreference=secondaryPreferred&ssl=false"

    if(galleria == ""):
        print(f"Nome galleria mancante! {galleria}")
        exit()

    if(not dbAddress):
        print(f"Indirizzo DB mancante! {dbAddress}")
        exit()
        
    #dbAddress = "MongoProductionClient" if chosenDB == "P" else "MongoQualityClient"
    #client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
    client = pymongo.MongoClient(dbAddress)
    currDB = client["smartscada"] 
    collectionName = "plant"
    #extractedData = sharedCode.readCollectionData(currDB, collectionName, name = galleria)
    extractedData = readCollectionData(currDB, collectionName, name = galleria)
    
    if(extractedData):
        idsList = []
        currPlant = loadPlant(extractedData)
        
        if(currPlant):
            print(currPlant["name"])
            for subPlantId in currPlant["subPlants"]:                
                currOId = ObjectId((subPlantId.id))
                #print(f"{subPlantId} -> {currOId}")
                idsList.append(currOId) if currOId not in idsList else next
            subPlants = loadSubPlants(currDB, idsList)
            
            for subplant in subPlants:
                print(subplant["name"])

          
    else:
        print(f"\n{galleria} non trovata!!!\n")



def mainCall2(gallerie, **kwargs):
    # Set up database connection parameters
    suffix = "_QUALITY_"
    dbAddress = "mongodb://rmtqual:H2Fnv3QAP4%3FB@rmt-q-nosql1-1.anasnet.it,rmt-q-nosql1-2.anasnet.it,rmt-q-nosql1-3.anasnet.it/?replicaSet=rmtqualRS&readPreference=secondaryPreferred&ssl=false"
    db = kwargs.get("db")
    if db and "prod" in db.lower():
        dbAddress = "mongodb://root:abc123!@rmt-p-nosql1-1.anasnet.it:27017,rmt-p-nosql1-2.anasnet.it:27017,rmt-p-nosql1-3.anasnet.it:27017/?replicaSet=rs1&authSource=admin"
        suffix = "_PROD_"
    elif(db and "moms" in db.lower()):
        dbAddress = "mongodb://10.86.20.54:27017"
        suffix = "_MOMS_"
    elif(db and "qual" in db.lower()):
        suffix = "_QUALITY_"
        

    # Initialize MongoDB client
    client = pymongo.MongoClient(dbAddress)
    currDB = client["smartscada"] 
    collectionName = "deviceProfile"

    # Process each galleria
    for galleria in gallerie.strip().split(","):
        extractedData = readCollectionData(currDB, collectionName, name=galleria.strip())
        if extractedData:
            deviceList = []
            for data in extractedData:
                if galleria.strip().upper() in data["name"]:
                    print(data["name"])
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
                    if tempDict and tempDict not in deviceList:
                        deviceList.append(tempDict)

            print("\n", deviceList[0], " \t<--->\t", deviceList[-1], len(deviceList), "\n\n")

            # Create and populate DataFrame
            df = pd.DataFrame(dtype=str)
            rowCount = 0
            for device in deviceList:
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

            print("\nSaving df...", currFileFolder + "_scarico_" + suffix + galleria.strip() + ".xlsx")
            with pd.ExcelWriter(currFileFolder + "_scarico_" + suffix + galleria.strip() + ".xlsx") as writer:
                df.to_excel(writer, index=False, freeze_panes=(1, 0))
    
    input("Finito!")


if __name__ == '__main__':
    db = input("da quale DB scaricare? (prod / quality / moms): \n")
    galleria = input("inserire nome galleria (timpa,monaco): \n")
    if galleria:
        mainCall2(galleria, db=db)

