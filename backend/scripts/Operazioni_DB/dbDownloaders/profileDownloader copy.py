import pymongo
import pandas as pd
from bson import ObjectId 

import re


# ----------------------------------- START COSTANTI -----------------------------------#  

MongoQualityClient = "mongodb://rmtqual:H2Fnv3QAP4%3FB@rmt-q-nosql1-1.anasnet.it,rmt-q-nosql1-2.anasnet.it,rmt-q-nosql1-3.anasnet.it/?replicaSet=rmtqualRS&readPreference=secondaryPreferred&ssl=false"
MongoProductionClient = "mongodb://root:abc123!@rmt-p-nosql1-1.anasnet.it:27017,rmt-p-nosql1-2.anasnet.it:27017,rmt-p-nosql1-3.anasnet.it:27017/?replicaSet=rs1&authSource=admin"
# auto-py-to-exe
# pyinstaller scaricoDB.py --onefile
# pyinstaller scaricoDB.spec
# ----------------------------------- END COSTANTI -----------------------------------# 



def readCollectionData(currentDB, collectionName:str, **kwargs):
    id = kwargs.get("id")
    name = kwargs.get("name")
    description = kwargs.get("description")
    profileName = kwargs.get("profile")
    collection = currentDB[collectionName] # Find all the documents in the collection
    if(not id and not name and not description and not profileName):
        result = collection.find()         #find() returns a cursor
    elif(id and not name and not description and not profileName):
        if(isinstance(id,str) and "-" in id):
            result = collection.find_one({"_id": id})
        else:
            result = collection.find_one({"_id": ObjectId(id)})
    elif(not id and name and not description and not profileName):
        if("regex" in kwargs.keys()):
            result = collection.find({"name": {"$regex": name.upper()}}) 
        else:
            result = collection.find_one({"name": name}) 
    elif(not id and not name and description and not profileName):
        result = collection.find_one({"description": description}) 
    elif(not id and not name and not description and profileName):
        if("regex" in kwargs.keys()):
            result = collection.find({"profileName": {"$regex": profileName.upper()}}) 
        else:
            result = collection.find_one({"name": profileName}) 
    return result


"""
Carica o Salva un file .xlsx
kwargs: 
    filepath -> percorso del file
    fileName -> nome del file
    df -> df con i dati da salvare oppure dict di df {"sheetName1": df1, "sheetName2": df2}
    sheets -> -1/all per tutti gli sheet, altrimenti nome specifico stringa o lista
    mode -> save / load
"""
def rw_xlsx(**kwargs):    
    fileName = kwargs.get("file") if "file" in kwargs.keys() else None
    filepath = kwargs.get("path") if "path" in kwargs.keys() else ""
    df = kwargs.get("df") if "df" in kwargs.keys() else None    
    sheets = kwargs.get("sheet") if "sheet" in kwargs.keys() else None

    if(fileName and "df" in kwargs.keys()):
        if(".xlsx" not in fileName):
            fileName = fileName + ".xlsx"

        mode = "load"
        if(("mode" in kwargs.keys()) and ("save" in kwargs["mode"] or "write" in kwargs["mode"] or "create" in kwargs["mode"]) or "df" in kwargs.keys()):
            mode = "save"   

        
        if(sheets and isinstance(sheets,str)):
            if("all" == sheets.lower()):
                sheets = -1
            else:
                sheets = re.split(r"[,;/]", sheets.lower())

        if(mode == "load"):             
            try:      
                if sheets is None:                                        
                    return pd.read_excel(filepath + fileName, dtype = str)
                if(isinstance(sheets, int)):
                    if(sheets < 0 ):
                        all_sheets = pd.ExcelFile(filepath + fileName).sheet_names
                        #print(all_sheets, sheets)
                        return {s: pd.read_excel(filepath + fileName, sheet_name=s, dtype=str) for s in all_sheets}                        
                    else:
                        return pd.read_excel(filepath + fileName, sheet_name=sheets, dtype=str)
                
                elif(isinstance(sheets, list)):
                    resDf = []
                    for foglio in sheets:
                        tempDf = pd.read_excel(filepath + fileName, sheet_name=foglio, dtype=str)
                        resDf.append(tempDf) if tempDf not in resDf else next
                    return pd.concat(resDf, axis=1, ignore_index=False)
            except FileNotFoundError:
                return None
        
        elif(mode == "save"): 
            with pd.ExcelWriter(filepath + fileName) as writer:
                try:
                    if isinstance(df, dict):
                        for sheet, data in df.items():
                            data.to_excel(writer, sheet_name=sheet, index=False, freeze_panes=(1, 0))
                    elif isinstance(df, pd.DataFrame):
                        sheet_name = sheets[0] if sheets else "Sheet1"
                        df.to_excel(writer, sheet_name=sheet_name, index=False, freeze_panes=(1, 0))
                    else:
                        return False
                
                    return True
                except Exception:
                    return False



def mainCall(nomeGalleria, **kwargs):

    suffix = "_QUALITY__"
    dbAddress = MongoQualityClient
    if(("db" in kwargs.keys() and kwargs["db"]) and (kwargs.get("db").upper().startswith("PROD") or kwargs.get("db").upper().startswith("P"))):
        suffix = "_PROD_"
        dbAddress = MongoProductionClient
        
    client = pymongo.MongoClient(dbAddress) 
    currDB = client["smartscada"] 

    sp_choice = int(input("Scaricare:\n0 -> profili+segnali+classi allarmi\n1 -> device + segnali + registri\n"))
    if(sp_choice != 0 and sp_choice != 1):
        print(f"Errore nella scelta effettuata!: {sp_choice}")
    else:
        for galleria in nomeGalleria.strip().split(","):  
            galleria = galleria.strip().capitalize()          
            dataHolder = []

            if(sp_choice == 0):   
                collectionName = "deviceProfile"  
                print(galleria)
                extractedData = readCollectionData(currDB, collectionName, name=galleria.strip(), regex = True)   
                
                if extractedData:
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
                            if tempDict and tempDict not in dataHolder:
                                dataHolder.append(tempDict)

                    if(dataHolder):
                        df = pd.DataFrame(dtype=str)
                        rowCount = 0
                        for device in dataHolder:
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
                        print("\nSalvataggio...", rw_xlsx(file = galleria + suffix + "Profili-AlrClass", df = df , mode = "save"))
                else:
                    print(f"{galleria} non trovato all'interno del DB!")
            elif(sp_choice == 1):
                collectionName = "device"
                extractedData = readCollectionData(currDB, collectionName, profile=galleria.strip(), regex = True)   
                if extractedData:
                    for data in extractedData:
                        if galleria.strip().upper() in data["profileName"]:
                            print(data["name"])
                            tempSignals = []
                            if("signalConfigurations" in data.keys() and data["signalConfigurations"]):
                                for signal in data["signalConfigurations"]:
                                    attributi = signal["attributes"] if "attributes" in signal.keys() else None

                                    signalName = signal["signalName"] if "signalName" in signal.keys() else ""
                                    signalDescription = ""
                                    if("signalStates" in data.keys()):
                                        signalDescription = data["signalStates"][signalName]["description"] if signalName in data["signalStates"].keys() else ""
                                    driverInstance = signal["driverInstance"] if "driverInstance" in signal.keys() else ""  
                                    tempSignal = {"name": signalName, "description": signalDescription, "driverInstance": driverInstance, "profileName": data["profileName"], "attributi": attributi}
                                   
                                    if tempSignal not in tempSignals:
                                        tempSignals.append(tempSignal)

                            tempDict = {"device": data["name"], "signals": tempSignals}
                            if tempDict and tempDict not in dataHolder:
                                dataHolder.append(tempDict)
                        # offset dataType registerType bitIndex register description signal datasource location
                
                    if(dataHolder):
                        df = pd.DataFrame(dtype=str)
                        rowCount = 0
                        for device in dataHolder:
                            df.loc[rowCount, "Device"] = device["device"]                            
                            if "signals" in device.keys():
                                for signal in device["signals"]:
                                    df.loc[rowCount, "Profilo"] = signal.get("profileName", "")
                                    df.loc[rowCount, "Device"] = device["device"]
                                    df.loc[rowCount, "Segnale"] = signal.get("name", "")
                                    df.loc[rowCount, "Descrizione"] = signal.get("description", "")
                                    df.loc[rowCount, "dataSource"] = signal.get("driverInstance", "")
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
                        print("\nSalvataggio...", rw_xlsx(file = galleria + suffix + "device-signals", df = df , mode = "save"))
                else:
                    print(f"{galleria} non trovato all'interno del DB!")
    #print("\nSalvataggio...", rw_xlsx(file = nomeGalleria + prefix, df = df, mode = "save"))


if __name__ == "__main__":     
    endFlag = False
    db = input("da quale DB scaricare? (prod / quality-> default) :\n").strip()
    while(endFlag == False):
        galleria = input("inserire nome galleria (utilizzare , per separare galleria multiple): (end/fine per uscire)\n").strip()
        if(not galleria.lower().startswith("end") and not galleria.lower().startswith("fine") and galleria != ""):
            mainCall(galleria, db = db) 
        else:
            endFlag = True