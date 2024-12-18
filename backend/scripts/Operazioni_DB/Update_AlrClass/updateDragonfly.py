import traceback 
import sys, os, os.path
import pymongo
import time, datetime
import json

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, mongoSearch


# ----------------------------------- START COSTANTI -----------------------------------#  

# ----------------------------------- END COSTANTI -----------------------------------# 


def mainFunction(CpuCoreNumber, UploadsFileFolder, DownloadsFileFolder, dbLogsPath, fileName, chosenDB, **kwargs):
    try:        
        updateHystory  = []        
        checkData = []
        filteredTags = None
        filteredWidgets = None
        totalElements = 0
        counter = 0
        
        clientName = kwargs.get("clientName", None)
        if(clientName):
            clientName += "_"
        
        yieldFlag = True if kwargs.get("yieldFlag") and kwargs.get("yieldFlag") else False
        
        msg = f"Loading file"
        yield msg if yieldFlag else print(msg)        
        df = sharedCode.rw_xlsx(file = fileName, path = UploadsFileFolder)
        #yield f"Il file contiente {df.columns}"
        
        scada_tag = ["tagName", "tagDescription", "tagDevice", "tagUniverse", "tagGalaxy", "alarmClass"]
        scada_widget = ["WidgetName", "WidgetDescription", "widgetDevice", "widgetUniverse", "widgetArchetype"]
        searchTagFlag = False
        searchWidgetFlag = False
        
        missingCols = []
        for checkCol in scada_tag + ["tagDevice_NEW", "alarmClass_NEW"]:
            if(checkCol not in df.columns ):
                missingCols.append(checkCol) if checkCol not in missingCols else next
        for checkCol in scada_widget + ["widgetDevice"]:
            if(checkCol not in df.columns ):
                missingCols.append(checkCol) if checkCol not in missingCols else next
        
        for colonna in df.columns:
            if(colonna.replace("_NEW","") in scada_tag):
                scada_tag.append(colonna) if colonna not in scada_tag else next
                searchTagFlag = True

        for colonna in df.columns:
            if(colonna.replace("_NEW","") in scada_widget):
                scada_widget.append(colonna) if colonna not in scada_widget else next
                searchWidgetFlag = True
        
        if(missingCols):
            msg = f"Mancano le seguenti colonne! {missingCols}"
            yield msg if yieldFlag else print(msg)
        
        msg = f"Formattazione dataframe..."
        yield msg if yieldFlag else print(msg)
        dfTag = df[scada_tag]
        dfWidget = df[scada_widget]
        
        searchTags = dfTag.apply(lambda row: json.loads(json.dumps({col: str(row[col]) for col in dfTag.columns})), axis=1).tolist()
        searchWidgets = dfWidget.apply(lambda row: json.loads(json.dumps({col: str(row[col]) for col in dfWidget.columns})), axis=1).tolist()
        
        msg = f"connessione al db {chosenDB}..."
        yield msg if yieldFlag else print(msg)
        
        dbAddress = "MongoProductionClient" if chosenDB.startswith("PROD") or chosenDB.startswith("P") else "MongoQualityClient"
        client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
        currDB = client["scada"] 
        msg = f"elaborating...{chosenDB}"
        yield msg if yieldFlag else print(msg)
        
        if(searchTagFlag):   # update da eseguire su 'TAG'
            yield(f"filtraggio dati per 'TAG'...")
            filteredTags = filterData(searchTags, "tagName")
        if(searchWidgetFlag):   # update da eseguire su 'WIDGET'
            yield(f"filtraggio dati per 'WIDGET'...")
            filteredWidgets = filterData(searchWidgets, "WidgetName") 
        
        if(filteredTags):
            totalElements += len(filteredTags) 
        if(filteredWidgets):
            totalElements += len(filteredWidgets) 
        
        if(filteredTags):   # update da eseguire su 'TAG'
            #yield(f"searchTagFlag: {searchTagFlag}")
            #filteredTags = filterData(searchTags, "tagName")
            if(not filteredTags):
                yield f"Nessun dato presente per tagName"
            yield f"filteredTags --> {filteredTags}"
            for indx, filteredTag in enumerate(filteredTags):
                currCollection = "scada_tag"
                if ("tagDescription" in filteredTag["target"]):
                    target = "description" 
                elif("alarmClass" in filteredTag["target"]):
                    target = "alarmClass"
                elif("tagDevice" in filteredTag["target"]):
                    target = "device"
                elif("tagName" in filteredTag["target"]):
                    target = "name"      
                  
                if(filteredTag["data"]["old"] == "nan" or filteredTag["data"]["old"] == "None"):
                    filteredTag["data"]["old"] = None
                querry = {"name": filteredTag["tagName"], target: filteredTag["data"]["old"]}
                yield f"querry tag: {querry}\n"
                if(querry != "" and currCollection != ""):
                    results = (mongoSearch.findCollectionData(currDB, currCollection, querry = querry))  
                    for result in results:                
                        resTarg = "<empty>"
                        if(target not in result.keys()):
                            yield f"Updating tag: {result["_id"]} - {result["name"]}"
                            querry = {"name": result["name"]}
                        else:
                            resTarg = result[target] 
                        yield (f"{result["name"]} - {target}: {resTarg} \t====>") if yieldFlag else print(f"{result["name"]} - {target}: {resTarg} \t====>")
                        updateQuerry = {target: filteredTag["data"]["new"]}
                        if(filteredTag["data"]["new"] and (filteredTag["data"]["new"] != "None" and filteredTag["data"]["new"] != "nan")):
                            msg = (mongoSearch.updateOne(currDB, currCollection, searchQuerry = querry, updateQuerry = updateQuerry ))
                            if(msg and "flag" in msg.keys() and msg["flag"] == True):
                                updateData = {f"tag - {indx}:{sharedCode.timeStamp()}": f"Modificato {filteredTag["data"]["old"]} con {filteredTag["data"]["new"]}", "querry": msg}
                                updateHystory.append(updateData) if updateData not in updateHystory else next
                                yield f"{msg}" if yieldFlag else print(msg)
                                yield " " if yieldFlag else print() 
                            else:
                                checkData.append(f"tag - querry: {querry} | updateQuerry: {updateQuerry}") if querry not in checkData else next
                        else:
                            checkData.append(f"tag - querry: {querry} | updateQuerry: {updateQuerry}") if querry not in checkData else next
                
                counter += 1
                msg = sharedCode.progressYield(counter, totalElements)  
                if(msg):
                    yield msg
        if(filteredWidgets):   # update da eseguire su 'WIDGET'
            #yield(f"searchWidgetFlag: {searchWidgetFlag}")
            #filteredWidgets = filterData(searchWidgets, "WidgetName")             
            if(not filteredWidgets):
                yield f"Nessun dato presente per WidgetName"
            yield f"filteredWidgets --> {filteredWidgets}"
            for indx, filteredWidget in enumerate(filteredWidgets):
                currCollection = "scada_widget"
                if ("WidgetName" in filteredWidget["target"]):
                    target = "name" 
                elif ("WidgetDescription" in filteredWidget["target"]):
                    target = "description" 
                elif ("widgetArchetype" in filteredWidget["target"]):
                    target = "archetype" 
                elif ("widgetDevice" in filteredWidget["target"]):
                    target = "device" 
                    
                if(filteredWidget["data"]["old"] == "nan" or filteredWidget["data"]["old"] == "None"):
                    filteredWidget["data"]["old"] = None
                querry = {"name": filteredWidget["WidgetName"], target: filteredWidget["data"]["old"]}       
                if(querry!= "" and currCollection != ""):
                    results = (mongoSearch.findCollectionData(currDB, currCollection, querry = querry))
                    for result in results:
                        resTarg = "<empty>"
                        if(target not in result.keys()):
                            yield f"Updating widget: {result["_id"]} - {result["name"]}"
                            querry = {"name": result["name"]}  
                        else:
                            resTarg = result[target]
                        yield (f"result: {result}") if yieldFlag else print(f"result: {result}" )
                        yield (f"{result["name"]} - {target}: {resTarg} \t====>") if yieldFlag else print(f"{result["name"]} - {target}: {resTarg} \t====>")
                        updateQuerry = {target: filteredWidget["data"]["new"]}
                        if(filteredWidget["data"]["new"] and (filteredWidget["data"]["new"] != "None" and filteredWidget["data"]["new"] != "nan")):
                            msg = (mongoSearch.updateOne(currDB, currCollection, searchQuerry = querry, updateQuerry = updateQuerry ))          
                            
                            if(msg and "flag" in msg.keys() and msg["flag"] == True):
                                updateData = {f"widget - {indx}:{sharedCode.timeStamp()}": f"Modificato {filteredWidget["data"]["old"]} con {filteredWidget["data"]["new"]}", "querry": msg}
                                updateHystory.append(updateData) if updateData not in updateHystory else next
                                yield f"{msg}" if yieldFlag else print(msg)
                                yield " " if yieldFlag else print() 
                            else:
                                checkData.append(f"widget - querry: {querry} | updateQuerry: {updateQuerry}") if querry not in checkData else next
                        else:
                            checkData.append(f"widget - querry: {querry} | updateQuerry: {updateQuerry}") if querry not in checkData else next
            
                counter += 1
                msg = sharedCode.progressYield(counter, totalElements)  
                if(msg):
                    yield msg
                                 
        yield f"Save: {(sharedCode.rw_file(file = f"{clientName}{chosenDB}-{sharedCode.timeStamp(fullDate = True)}-updateHystory.json", path = dbLogsPath, data = updateHystory, mode = "save"))}"   
        yield f"errors: {len(checkData)}=> {(sharedCode.rw_file(file = f"{clientName}{chosenDB}-{sharedCode.timeStamp(fullDate = True)}-update_Error.json", path = dbLogsPath, data = checkData, mode = "save"))}" 
    except Exception as e:
        yield f"An error occurred: {str(e)}:"
        traceback.print_exc()  
        

def filterData(dataList, dictType):
    """Ricerca e filtra le colonne "_NEW" su cui fare l'update"""
    def findKeys(elementZ):
        keyList = []
        for key in elementZ.keys():
            if(key.endswith("_NEW")):
                kpair = {"old": key.replace("_NEW",""), "new": key}
                keyList.append(kpair) if kpair not in keyList else next
        return keyList
    
    itemPairs = []
    if(dataList):
        refkeys = findKeys(dataList[0])
        if(refkeys):
            for item in dataList:
                for rkpair in refkeys:     
                    if(rkpair["old"] in item.keys() and rkpair["new"] in item.keys()):  
                        kval = {dictType: item[dictType], "target": rkpair["old"], "data": {"old": item[rkpair["old"]], "new": item[rkpair["new"]]}} #WidgetName
                        itemPairs.append(kval) if kval not in itemPairs and (kval["data"]["new"] != "" and kval["data"]["new"] != "nan") else next
    return itemPairs
    
    
if __name__ == "__main__":
    None