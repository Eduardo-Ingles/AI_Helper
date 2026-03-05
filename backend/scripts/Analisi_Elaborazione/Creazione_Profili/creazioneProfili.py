
import pandas as pd
import traceback
import time
import os
import sys
import re
import json
import logging

LOG_FILENAME = 'logging_example.out'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

logging.debug('This message should go to the log file')

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, normalizzatore
from backend.scripts.Analisi_Elaborazione.Classi_Allarme import alrClassDefiner

# ----------------------------------- START COSTANTI -----------------------------------#  

CommandBody = sharedCode.loadSettings("profilatorSettings", "CommandBody") 
CommandBody_PAR = sharedCode.loadSettings("profilatorSettings", "CommandBody_PAR") 
OperationBodies = sharedCode.loadSettings("profilatorSettings", "OperationBodies")
valueObjects = sharedCode.loadSettings("profilatorSettings", "valueObjects")
thresholdsData = sharedCode.loadSettings("profilatorSettings", "thresholdsValues") 
dataTypeDict = sharedCode.loadSettings("globalSettings", "dataType") 
defaultValuesDict = sharedCode.loadSettings("profilatorSettings", "defaultValues")

splitRule = sharedCode.loadSettings("globalSettings", "splitRule")
rulesPath = sharedCode.loadSettings("globalSettings", "rulesFolderPath") 
dictFolder = sharedCode.loadSettings("paths", "dictFolder") 
dictFileName = sharedCode.loadSettings("files", "dizionarioMain")


dataRules = sharedCode.rw_file(path = rulesPath, file = sharedCode.loadSettings("globalSettings", "descrRules"))
alrClassRules = sharedCode.rw_file(path = rulesPath, file = sharedCode.loadSettings("globalSettings", "alrClassRules"))
dictionary = (sharedCode.rw_file(path = dictFolder, file = dictFileName))
dataUomRules = sharedCode.rw_file(path = rulesPath, file = sharedCode.loadSettings("globalSettings", "uomRules"))

indexedAliasArray = normalizzatore.aliasIndexArray(dictionary)

Profile = ['id', 'name', 'description', 'manufacturer', 'model', 'labels', 'operationStateExpression', 'showAlarmIcon', 'created', 'modified']
    
Threshold = ['profileName', 'signalName', 'thresholdId', 'emitAlarm', 'alarmLevel',        
            'lower', 'upper', 'valuesFromSignal', 'lowerSignal', 'upperSignal',
            'label', 'description', 'emitEvent', 'emitAlert', 'labelColor',
            'alarmDestination', 'emitInThresholdReadingsType']

VirtualThreshold = ['profileName', 'signalName', 'thresholdId', 'emitAlarm', 'alarmLevel',
                    'lower', 'upper', 'valuesFromSignal', 'lowerSignal', 'upperSignal',
                    'label', 'description', 'emitEvent', 'emitAlert', 'labelColor',
                    'alarmDestination', 'emitInThresholdReadingsType']

Signals = ['profileName', 'name', 'signalId', 'description', 'hidden', 'type',
            'uom', 'scale', 'valueBound', 'minimum', 'maximum', 'defaultValue',
            'valueObjects', 'decimalPlaces', 'readingExpireTime', 'emitReadings',
            'access', 'tags', 'alarmName', 'alarmDescription', 'alarmCode',
            'alarmIcon', 'alarmPriority']

VirtualSignals = ['profileName', 'name', 'signalId', 'description', 'mappings',
                'expression', 'hidden', 'type', 'uom', 'scale', 'valueBound', 'minimum',
                'maximum', 'defaultValue', 'valueObject', 'decimalPlaces',
                'readingExpireTime', 'emitReadings', 'tags', 'alarmName',
                'alarmDescription', 'alarmCode', 'alarmIcon', 'alarmPriority']
  
Commands = ['profileName', 'name', 'details', 'getDescription', 'setDescription', 'roleLevel', 'commandId', 'expression', 'virtual', 'noteOnExecutionEnabled', 'noteIsOptional', 'noteType', 'domainDefinition']

Operations = ['profileName', 'operationId', 'name', 'operationType', 'signalName', 'setParameterMode', 'groupId', 'delayAfterExec', 'execOrder', 'parameter']

Templates = ['profileName', 'name', 'parameter', 'value']

DetailTemplates = ['profileName', 'name', 'parameter', 'value', 'nameTabPreview']
    
dfOld = None
fPath_Old = None
fPath_New = None
fPath_Check = None
checkFileName = None

ENABLE_ALR_CLASS = True
# ----------------------------------- END COSTANTI -----------------------------------# 


def profileSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str)  
    for colonna in Profile:
        tdf[colonna] = None
    if(kwargs and "skip" in kwargs().keys()):
        return tdf
    tempDataList = []
    if(not isinstance(oldDf, type(None))):
        for index, row in oldDf.iterrows():
            tempProfile = { 'id': "", 
                            'name': str(row["profileName"]),
                            'description': str(row["profileName"]).lower(),
                            'manufacturer': "-",
                            'model': "-",
                            'labels': ["-"],
                            'operationStateExpression': "",
                            'showAlarmIcon': "VERO",
                            'created': "",
                            'modified': ""
                            }

            tempDataList.append(tempProfile) if tempProfile not in tempDataList else next  

        for index, tempData in enumerate(tempDataList):                
            for key, value in tempData.items():
                tdf.at[index, key] = str(value)

        return tdf


def thresholdSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str) 
    for colonna in Threshold:
        tdf[colonna] = None
    if(kwargs and kwargs.get("skip")):
        return tdf
    tempDataList = [] 
    for index, row in oldDf.iterrows():
        if(row["thresholds"] and str(row["thresholds"]) != "" and str(row["thresholds"]) != "nan"):
            thList = json.loads(str(row["thresholds"]))
            for thData in thList:
                tempThreshold = {   'profileName': str(row["profileName"]),
                                    'signalName': str(row["signalName"]),
                                    'thresholdId': "",
                                    'emitAlarm': "VERO",
                                    'alarmLevel': thData["alarmLevel"],
                                    'lower': thData["lower"],
                                    'upper': thData["upper"],
                                    'valuesFromSignal': "FALSO",
                                    'lowerSignal': "",
                                    'upperSignal': "",
                                    'label': thData["label"],
                                    'description': "",
                                    'emitEvent': "",
                                    'emitAlert': "",
                                    'labelColor': thData["labelColor"],
                                    'alarmDestination': thData["alarmDestination"],
                                    'emitInThresholdReadingsType': thData["emitInThresholdReadingsType"]
                                }       
                tempDataList.append(tempThreshold) if tempThreshold not in tempDataList else next  
    
    
    for index, tempData in enumerate(tempDataList):                
        for key, value in tempData.items():
            tdf.at[index, key] = str(value)
    return tdf
    
    
def virtualThresholdSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str) 
    for colonna in VirtualThreshold:
        tdf[colonna] = None
    if(kwargs and kwargs.get("skip")):
        return tdf
    tempDataList = [] 
    for index, row in oldDf.iterrows():
        tempVirtualThreshold = {'profileName': "", 
                                'signalName': "", 
                                'thresholdId': "", 
                                'emitAlarm': "", 
                                'alarmLevel': "",
                                'lower': "", 
                                'upper': "", 
                                'valuesFromSignal': "", 
                                'lowerSignal': "", 
                                'upperSignal': "",
                                'label': "", 
                                'description': "", 
                                'emitEvent': "", 
                                'emitAlert':"", 
                                'labelColor': "",
                                'alarmDestination': "", 
                                'emitInThresholdReadingsType': ""
                                }
        
        tempDataList.append(tempVirtualThreshold) if tempVirtualThreshold not in tempDataList else next  
    
    
    for index, tempData in enumerate(tempDataList):                
        for key, value in tempData.items():
            tdf.at[index, key] = str(value)
    return tdf

    
def signalsSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str)
    for colonna in Signals:
        tdf[colonna] = None
    if(kwargs and kwargs.get("skip")):
        return tdf
    tempDataList = [] 
    for index, row in oldDf.iterrows():
        tempSignals = { 'profileName': str(row["profileName"]), 
                        'name': str(row["signalName"]), 
                        'signalId': "", 
                        'description': str(row["signalDescription"]), 
                        'hidden': str(row["hidden"]), 
                        'type': str(row["valueType"]),
                        'uom': str(row["uom"]).replace('None', ''), 
                        'scale': str(row["scale"]), 
                        'valueBound': str(row["valueBound"]), 
                        'minimum': str(row["valueMin"]).replace('None', ''), 
                        'maximum': str(row["valueMax"]).replace('None', ''), 
                        'defaultValue': str(row["defaultValue"]).replace('None', ''),
                        'valueObjects': str(row["valueObjects"]).replace('None', ''), 
                        'decimalPlaces': str(row["decimalPlaces"]).replace('None', ''), 
                        'readingExpireTime': str(row["readingExpireTime"]), 
                        'emitReadings': str(row["emitReadings"]),
                        'access': "RW", 
                        'tags': str(row["tags"]).replace('[', '["').replace(']', '"]').replace(',', '","'), 
                        'alarmName': str(row["alarmClass"]).replace('nan', ''), 
                        'alarmDescription': str(row["alarmDescription"]).replace('None', ''), 
                        'alarmCode': "",
                        'alarmIcon': "", 
                        'alarmPriority': ""
                    }
        tempDataList.append(tempSignals) if tempSignals not in tempDataList else next      
    
    for index, tempData in enumerate(tempDataList):                
        for key, value in tempData.items():
            tdf.at[index, key] = str(value)
    return tdf


def virtualSignalsSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str)
    for colonna in VirtualSignals:
        tdf[colonna] = None
    if(kwargs and kwargs.get("skip")):
        return tdf
    tempDataList = [] 
    for index, row in oldDf.iterrows():    
        tempVirtualSignals = {  'profileName': "", 
                                'name': "", 
                                'signalId': "", 
                                'description': "", 
                                'mappings': "",
                                'expression': "", 
                                'hidden': "", 
                                'type': "", 
                                'uom': "", 
                                'scale': "", 
                                'valueBound': "", 
                                'minimum': "",
                                'maximum': "", 
                                'defaultValue': "", 
                                'valueObject': "", 
                                'decimalPlaces': "",
                                'readingExpireTime': "", 
                                'emitReadings': "", 
                                'tags': "", 
                                'alarmName': "",
                                'alarmDescription': "", 
                                'alarmCode': "", 
                                'alarmIcon': "", 
                                'alarmPriority': ""
                            }
        tempDataList.append(tempVirtualSignals) if tempVirtualSignals not in tempDataList else next      
    if(len(tempDataList) != 0):
        for index, tempData in enumerate(tempDataList):                
            for key, value in tempData.items():
                tdf.loc[index, key] = str(value)
    return tdf
  
     
def commandsSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str)
    for colonna in Commands:
        tdf[colonna] = None
    if(kwargs and kwargs.get("skip")):
        return tdf
    tempDataList = [] 
    for index, row in oldDf.iterrows():
        if("[Commands]" in str(row["tags"]) or "[Parameters]" in str(row["tags"])):
            tempCommands = {'profileName': str(row["profileName"]), 
                            'name': str(row["signalName"]), 
                            'details': "", 
                            'getDescription': "", 
                            'setDescription': str(row["commandDescription"]), 
                            'roleLevel': str(row["commandRoleLevel"]), 
                            'commandId': "",
                            'expression': "", 
                            'virtual': str(row["virtual"]),
                            'noteOnExecutionEnabled': 'FALSO',  # hardcoded
                            'noteIsOptional': 'FALSO',          # hardcoded
                            'noteType': 'freeText',                # hardcoded
                            'domainDefinition': ""
                        }
            tempDataList.append(tempCommands) if tempCommands not in tempDataList else next      
    
    for index, tempData in enumerate(tempDataList):                
        for key, value in tempData.items():
            tdf.at[index, key] = str(value)
    return tdf

   
def operationsSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str)
    for colonna in Operations:
        tdf[colonna] = None
    if(kwargs and kwargs.get("skip")):
        return tdf
    tempDataList = [] 
    for index, row in oldDf.iterrows():
        if("[Commands]" in str(row["tags"]) or "[Parameters]" in str(row["tags"])):
            parMode = ""
            if("[Commands]" in str(row["tags"])):
                parMode = "setParameter"
            elif("[Parameters]" in str(row["tags"])):
                parMode = "setSignal"
            tempOperations = {  'profileName': str(row["profileName"]), 
                                'operationId': "", 
                                'name': str(row["signalName"]), 
                                'operationType': "set", 
                                'signalName': str(row["signalName"]), 
                                'setParameterMode': parMode, 
                                'groupId': '0',
                                'delayAfterExec': '0',
                                'execOrder': '0',
                                'parameter': str(row["parameter"]).replace('None', ''),
                            }
            tempDataList.append(tempOperations) if tempOperations not in tempDataList else next      
    
    for index, tempData in enumerate(tempDataList):                
        for key, value in tempData.items():
            tdf.at[index, key] = str(value)
    return tdf

   
def templatesSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str)
    for colonna in Templates:
        tdf[colonna] = None
    if(kwargs and kwargs.get("skip")):
        return tdf
    tempDataList = [] 
    for index, row in oldDf.iterrows():
        tempTemplates = {   'profileName': str(row["profileName"]), 
                            'name': "DefaultDeviceTemplate", 
                            'parameter': "", 
                            'value': ""
                        }
        tempDataList.append(tempTemplates) if tempTemplates not in tempDataList else next      
    
    for index, tempData in enumerate(tempDataList):                
        for key, value in tempData.items():
            tdf.at[index, key] = str(value)
    return tdf
 
    
def detailTemplatesSheet(oldDf, **kwargs):
    tdf = pd.DataFrame(dtype=str)
    for colonna in DetailTemplates:
        tdf[colonna] = None
    if(kwargs and kwargs.get("skip")):
        return tdf
    tempDataList = [] 
    for index, row in oldDf.iterrows():
        tempDetailTemplate = {  'profileName': "", 
                                'name': "", 
                                'parameter': "", 
                                'value': "",  #f"signalStates.{(str(row["signalName"])).replace("_","_")}.value", 
                                'nameTabPreview': ""
                            }
        tempDataList.append(tempDetailTemplate) if tempDetailTemplate not in tempDataList else next      
    
    for index, tempData in enumerate(tempDataList):                
        for key, value in tempData.items():
            tdf.at[index, key] = str(value)
    return tdf
   

#NewProfileName	NewSignalName	NewSignalDescription	NewDataValueType	NewLogica	NewAlarmClass	NewAlarmDescription	Escludi Profili
  
def mainCall(CpuCoreNumber, UploadsFileFolder, DownloadsFileFolder, fileName, outFileName, sheet, **kwargs):
    """
    - CpuCoreNumber: numero di processori da utilizzare (Non utilizzato)
    - UploadsFileFolder: percorso della cartella dove il file è stato caricato
    - DownloadsFileFolder: percorso della cartella dove il file verrà salvato
    - fileName: nome del fine in input
    - outFileName: nome / suffisso del fine in output -> integrare con 'settings.json'
    - sheet: nome o numero dello sheet
    - kwargs: yieldFlag
    """
    prefisso = sharedCode.loadSettings("profilatorSettings", "prefix")
    links = []
        
    yield f"Elaborazione in corso di '{fileName}'..."
    
    def checkColumns(df, target, newColumnsArray):  
        yield f"Controllo in corso delle colonne..."      
        #yield "Step I"
        colonneRif = sharedCode.loadSettings(target, "colonneIN")
        for idx, colonna in enumerate(colonneRif):  
            if not colonna in df.columns:                  
                yield (f"Colonna {colonna} non trovata!") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(f"Colonna {colonna} non trovata!")
                df[colonna] = None
            msg = sharedCode.progressYield(idx+1, len(colonneRif))
            if(msg):
                yield msg
        #yield "Step II"
        newColumns = sharedCode.loadSettings(target, "outputColumns")
        for idx, newColonna in enumerate(newColumns):   
            if not newColonna in df.columns:     
                df[newColonna] = None
            msg = sharedCode.progressYield(idx+1, len(newColumns))
            if(msg):
                yield msg
      
      
    def checkProfileSignals_(df):    
        try:    
            global checkFileName
            counter = 0
            yield "Controllo segnali: profili <-> devices in corso..."

            def localExtractor(arrA, arrB):    
                #return list(set(arrA) ^ set(arrB))         
                z = set(arrA).difference(set(arrB)) 
                if(z):     
                    return list(z)

            if("NewDevice" in df.columns and "NewProfileName" in df.columns and "NewSignalName" in df.columns):
                TempDictProfiles = {}
                TempDictDevices = {}  

                for index, row in df.iterrows():
                    if(str(row["Escludi Profili"]) == "" or str(row["Escludi Profili"]) == "nan"):
                        counter += 1                    
                        tempDfDevice = str(row["NewDevice"]).strip().replace("nan", "")
                        tempDfProfile = str(row["NewProfileName"]).strip().replace("nan", "")
                        
                        TempDictProfiles[tempDfProfile] = {"signals": [], "devices": [], "dups": []}
                        TempDictDevices[tempDfDevice] = {"signals": [], "profiles": []}

                for index, row in df.iterrows():
                    if(str(row["Escludi Profili"]) == "" or str(row["Escludi Profili"]) == "nan"):
                        counter += 1
                        tempDfSignal = str(row["NewSignalName"]).strip() if str(row["NewSignalName"]).strip() != "nan" else None
                        tempDescr = str(row["NewSignalDescription"]).strip() if str(row["NewSignalDescription"]).strip() != "nan" else None
                        tempDfDevice = str(row["NewDevice"]).strip() if str(row["NewDevice"]).strip() != "nan" else None
                        tempDfProfile = str(row["NewProfileName"]).strip() if str(row["NewProfileName"]).strip() != "nan" else None
                        
                        dups = {"signal": tempDfSignal, "description": tempDescr}
                        TempDictProfiles[tempDfProfile]["dups"].append(dups) if dups not in TempDictProfiles[tempDfProfile]["dups"] else next
                        
                        if(tempDfProfile in TempDictProfiles.keys() and tempDfSignal):
                            TempDictProfiles[tempDfProfile]["signals"].append(tempDfSignal) if tempDfSignal not in TempDictProfiles[tempDfProfile]["signals"] else next
                            TempDictProfiles[tempDfProfile]["devices"].append(tempDfDevice) if tempDfDevice not in TempDictProfiles[tempDfProfile]["devices"] else next

                        if(tempDfDevice in TempDictDevices.keys() and tempDfSignal):
                            TempDictDevices[tempDfDevice]["signals"].append(tempDfSignal) if tempDfSignal not in TempDictDevices[tempDfDevice]["signals"] else next
                            TempDictDevices[tempDfDevice]["profiles"].append(tempDfProfile) if tempDfProfile not in TempDictDevices[tempDfDevice]["profiles"] else next

                df_selected = pd.DataFrame() 
                checkedData = []                
                for Profiles in TempDictProfiles:                      
                    dupsList = []                    
                    signal_descriptions = {}   
                    for dup in TempDictProfiles[Profiles]["dups"]:
                        signal = dup["signal"]
                        description = dup["description"]         
                        if not signal or not description:
                            continue                 
                        if signal in signal_descriptions:
                            if description != signal_descriptions[signal]:
                                dupsList.append(f"{signal} ({description} vs {signal_descriptions[signal]})")
                        else:
                            signal_descriptions[signal] = description
                        
                    if(TempDictProfiles[Profiles]["devices"]):
                        for device in TempDictProfiles[Profiles]["devices"]:
                            tempDevVary = {
                                "Profilo": Profiles, 
                                "Segnali del profilo": TempDictProfiles[Profiles]["signals"], 
                                "Dispositivi associati": TempDictProfiles[Profiles]["devices"], 
                                "Segnali mancanti": [],
                                "Assegnazione multipla di profili a dispositivo": "",
                                "Segnale dupplicato": "-".join(dupsList) if dupsList else ""
                                }
                            
                            if("profiles" in TempDictDevices[device].keys() and len(TempDictDevices[device]["profiles"]) != 1):
                                tempDevVary["Assegnazione multipla di profili a dispositivo"] = f"{device} <-> {TempDictDevices[device]["profiles"]}"
                            
                            if(TempDictProfiles[Profiles]["signals"] and TempDictDevices[device]["signals"]):
                                if(not sharedCode.all_AinB(TempDictProfiles[Profiles]["signals"], TempDictDevices[device]["signals"])):
                                    extractSignals = localExtractor(TempDictProfiles[Profiles]["signals"], TempDictDevices[device]["signals"])
                                    tempDevVary["Segnali mancanti"].append(f"{device} -> {extractSignals}")                            
                            checkedData.append(tempDevVary) if tempDevVary["Profilo"] != "" and  tempDevVary not in checkedData else next                                    
                               
                    elif(TempDictProfiles[Profiles] and dupsList):
                        tempDevVary = {
                                "Profilo": Profiles, 
                                "Segnali del profilo": "", 
                                "Dispositivi associati": "", 
                                "Segnali mancanti": [],
                                "Assegnazione multipla di profili a dispositivo": "",
                                "Segnale dupplicato": "-".join(dupsList) if dupsList else ""
                                }                        
                        checkedData.append(tempDevVary) if tempDevVary["Profilo"] != "" and  tempDevVary not in checkedData else next   
                        print(checkedData)
                                     
                if(checkedData):
                    for key in checkedData[0].keys():
                        df_selected[key] = None
                    for index, chkData in enumerate(checkedData):
                        for key in chkData.keys():
                            if(chkData[key] != "" or chkData[key] != "nan"):
                                df_selected.at[index, key] = chkData[key]
                
                cfileName = f"_Controlli_{outFileName}_{fileName}.xlsx"
                sCheck = sharedCode.rw_xlsx(path = DownloadsFileFolder, file = cfileName, df = {"CheckProfileSignals": df_selected}, mode = "save")
                checkFileName =  (f"_Controlli_{outFileName}_{fileName}") if sCheck else None
                if(sCheck):
                    links.append({"link": f"{DownloadsFileFolder}{cfileName}", "linkName": cfileName})  
            
        except Exception as e:            
            yield(f"An error occurred: {str(e)}:") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(f"An error occurred: {str(e)}:")
            traceback.print_exc()
            logging.error(e, exc_info=True)
            

    #usedColumns = ["NewProfileName", "NewSignalName", "NewSignalDescription", "NewDataValueType", "NewLogica", "NewAlarmClass", "NewAlarmDescription", "NewUOM", "Escludi Profili"]
    
    """Caricamento del file 'grezzo'"""    
    yield "Caricamento del file in corso..."
    # df= sharedCode.rw_xlsx(path=r'C:\Utente\Downloads', file='elaborazione_PREPO.xlsx', sheet= -1)
    df = sharedCode.rw_xlsx(path = UploadsFileFolder, file = fileName, sheet = -1, standalone=True)
    if not(df):
        yield "errore nel caricamento del dataframe!"
        return
    yield f"Sheets presenti: {df.keys()}"
    if (not ("WIP" in df.keys() or "W.I.P." in df.keys() or "Profiles" in df.keys())):
        yield "Rinominare lo sheet con i dati in input 'WIP' / 'W.I.P.' oppure 'Profiles'"
        return 
    
    if("WIP" in df.keys()):
        yield "...sheet attuale: WIP..."
        df = df["WIP"]
    if("W.I.P." in df.keys()):
        yield "...sheet attuale: W.I.P...."
        df = df["W.I.P."]
    if("Profiles" in df.keys()):
        yield "...sheet attuale: Profiles..."
        df = df["Profiles"]
    
    
    for output in checkProfileSignals_(df):
        yield output
        
    yield "Rimozione elementi dupplicati [NewProfileName + NewSignalName + NewSignalDescription]"
    dropColumns = ["NewProfileName", "NewSignalName", "NewSignalDescription"]
    currCols = []
    for col in df.columns:
        currCols.append(col) if col not in currCols else next
    if(not sharedCode.all_AinB(dropColumns, currCols)):
        return 
    df = df[df['Escludi Profili'].isna() | (df['Escludi Profili'] == '')]  
    df = df.drop_duplicates(subset = dropColumns)    
    
    def ElaboraDati_OLD_Format(df): 
        """
        Esegue l'elaborazione del file import dei Profili nel vecchio formato (da utilizzare con il 'motorino di Emma')
        """ 
        try:              
            yield "Controllo colonne in corso"
            for innerYield in checkColumns(df, "profilatorSettings", None):
                yield innerYield
            #print("drop duplicates")
            #dropDuplicateValues() 
            #print("check profili <-> segnali...")
            #global checkFileName
            #checkFileName =  checkProfileSignals()            
            yield "logicExtractor" if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("logicExtractor...")
            logicExtractor()            
            yield "reAssignDataType..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("reAssignDataType...")
            reAssignDataType() 
            #if(normalizeFlag):
            #    print("normalizeData...")
            #    normalizeData()             
            yield "normalizeData...(attendere)" if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("normalizeData...")
            #normalizeData()             
            for normYield in normalizeData():
                yield normYield
            yield "defineAllarms..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("defineAllarms...") 
            defineAllarms()
            yield "defineCommands..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("defineCommands...")
            defineCommands()            
            yield "defineMisure..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("defineMisure...")
            defineMisure()            
            yield "defineParams..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("defineParams...")
            defineParams()            
            yield "defineStates..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("defineStates...")
            defineStates()            
            yield "staticValues..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("staticValues...")
            staticValues()            
            yield "appendUOM..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("appendUOM...")
            appendUOM()         
            if(ENABLE_ALR_CLASS):     
                yield "alrClassFiller...(attendere)" if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("alrClassFiller...(attendere)")
                for output in alrClassFiller(df):
                    yield output if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(output)
            yield "cercaDoppioni..." if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print("cercaDoppioni...")
            cercaDoppioni()
            
            selected_columns = sharedCode.loadSettings("profilatorSettings", "outputColumns")
            fillOldData(df)      
            global dfOld
            dfOld = df[selected_columns]  
                        
            suffix = sharedCode.loadSettings("profilatorSettings", "suffixOld")
            savename = f"{prefisso}_{fileName}_{suffix}.xlsx"#_{sharedCode.timeStamp(fullDate = True)}"
            
            yield " - Salvataggio vecchio formato..."
            
            if(sharedCode.rw_xlsx(file = savename, path = DownloadsFileFolder, df = {"Profiles": dfOld}, mode = "save")):
                global fPath_Old
                fPath_Old = f"""<a href="downloads/{savename}">{savename}</a><br>"""                 
                links.append({"link": f"{DownloadsFileFolder}{savename}", "linkName": savename})    
            
            else:
                yield "Errore nella creazione del vecchio formato!\nElaborazione fallita!"
        except Exception as e:            
            yield(f"An error occurred: {str(e)}:") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(f"An error occurred: {str(e)}:")
            traceback.print_exc()
            logging.error(e, exc_info=True)
             


    def ElaboraDati_NEW_Format(oldDf):  
        """
        Esegue l'elaborazione del file import dei Profili nel nuovo formato (possibile caricare direttamente da GUI smartScada)
        """
        try:         
            #yield(oldDf.head())
            #yield(oldDf.columns)
            dfNew = {"Profile": profileSheet(oldDf),
                     "Threshold": thresholdSheet(oldDf),
                     "Virtual Threshold": virtualThresholdSheet(oldDf),
                     "Signals": signalsSheet(oldDf),
                     "VirtualSignals": virtualSignalsSheet(oldDf),
                     "Commands": commandsSheet(oldDf),
                     "Operations": operationsSheet(oldDf),
                     "Templates": templatesSheet(oldDf),
                     "DetailTemplates": detailTemplatesSheet(oldDf),                     
                     }

            suffix = sharedCode.loadSettings("profilatorSettings", "suffixNew")
            savename = f"{prefisso}_{fileName}_{suffix}.xlsx"#_{sharedCode.timeStamp(fullDate = True)}"              
            yield "- Salvataggio nuovo formato..."
            if(f"New format: {sharedCode.rw_xlsx(file = savename, path = DownloadsFileFolder, df = dfNew, mode = "save")}"): 
                global fPath_New 
                fPath_New = f"""<a href="downloads/{savename}">{savename}</a><br>"""
                yield ("")
                if(checkFileName):
                    links.append({"link": f"{DownloadsFileFolder}{savename}", "linkName": savename})               
   
        except Exception as e:            
            yield(f"An error occurred: {str(e)}:") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(f"An error occurred: {str(e)}:")
            traceback.print_exc()            
            logging.error(e, exc_info=True)             
                
                
    def alrClassFiller(df):        
        alrClassPath = project_root + sharedCode.loadSettings("paths", "staticData")
        sheet = "RIFERIMENTO"    
        alrClassFile = "ALR_CLASS_ANAS"
        counter = 0
        for index, row in df.iterrows():
            tempDfDevice = str(row["NewDevice"]).strip()
            tempDfProfile = str(row["NewProfileName"]).strip()
            tempDfSignal = str(row["NewSignalName"]).strip()
            tempDfSignalDescr = str(row["NewSignalDescription"]).strip()

            currentAlrClass = str(row["NewAlarmClass"]).strip()
            if(currentAlrClass != "" and currentAlrClass != "nan"):
                if(tempDfDevice and (tempDfDevice == "nan" or tempDfDevice == "")):
                    tempDfDevice = tempDfProfile
                if(tempDfDevice and tempDfDevice != "nan" and tempDfSignal and tempDfSignal != "nan" and tempDfSignalDescr and tempDfSignalDescr != "nan"):
                    inputData = {"device": tempDfDevice, "signal": tempDfSignal, "descr": tempDfSignalDescr}            
                    result = alrClassDefiner.mainCall(alrClassFile, alrClassPath, inputData) 
                    if(result):
                        df.at[index, "NewAlarmClass"] = result["CODICE ALLARME"]
                        df.at[index, "NewAlarmDescription"] = result["DESCRIZIONE ALLARME"]
                        yield (f"{inputData} -> {result["DISPOSITIVO"]}: {result["CODICE ALLARME"]} - {result["DESCRIZIONE ALLARME"]}")
                        yield ("-"*50)  
                        
            counter += 1
            msg = sharedCode.progressYield(counter, len(df.index))
            if (msg):
                yield msg
   
        
    def checkProfileSignals():
        def localExtractor(arrA, arrB):    
            #return list(set(arrA) ^ set(arrB))         
            z = set(arrA).difference(set(arrB)) 
            if(z):     
                return list(z)
        
        devicesList = []
        duplicatedSignals = []
        if("NewDevice" in df.columns and "NewProfileName" in df.columns and "NewSignalName" in df.columns):
            TempArrProfiles = []
            TempArrDevices = [] 
            TempArrSignals = [] 

            for index, row in df.iterrows():
                tempDfDevice = str(row["NewDevice"]).strip()
                tempDfProfile = str(row["NewProfileName"]).strip()
                tempDfSignal = str(row["NewSignalName"]).strip()
                
                foundDeviceFlag = False
                for tempDictDevice in TempArrDevices:
                    if(tempDfDevice == tempDictDevice["device"]):
                        foundDeviceFlag = True
                        tempDictDevice["signal"].append(tempDfSignal) if tempDfSignal not in tempDictDevice["signal"] else next
                        tempDictDevice["profile"].append(tempDfProfile) if tempDfProfile not in tempDictDevice["profile"] else next
                        #if(tempDfSignal in tempDictDevice["signal"]):
                        #    tempDictDevice["duplicatedSignals"].append(tempDfSignal) if tempDfSignal not in tempDictDevice["duplicatedSignals"] else next


                if(foundDeviceFlag == False):
                    #TempArrDevices.append({"device": tempDfDevice, "profile": [tempDfProfile], "signal": [tempDfSignal], "duplicatedSignals": []})
                    TempArrDevices.append({"device": tempDfDevice, "profile": [tempDfProfile], "signal": [tempDfSignal]})


                foundProfileFlag = False
                for tempDictProfilo in TempArrProfiles: 
                    if(tempDfProfile == tempDictProfilo["profile"]):
                        foundProfileFlag = True
                        tempDictProfilo["signal"].append(tempDfSignal) if tempDfSignal not in tempDictProfilo["signal"] else next
                        tempDictProfilo["device"].append(tempDfDevice) if tempDfDevice not in tempDictProfilo["device"] else next
                        #if(tempDfSignal in tempDictProfilo["signal"]):
                        #    tempDictProfilo["duplicatedSignals"].append(tempDfSignal) if tempDfSignal not in tempDictProfilo["duplicatedSignals"] else next
                        
                    
                if(foundProfileFlag == False):
                    #TempArrProfiles.append({"profile": tempDfProfile, "device": [tempDfDevice], "signal": [tempDfSignal], "duplicatedSignals": []}) 
                    TempArrProfiles.append({"profile": tempDfProfile, "device": [tempDfDevice], "signal": [tempDfSignal]}) 
            
            df_selected = pd.DataFrame() 
            checKData = []
            for device in TempArrDevices:
                for profile in TempArrProfiles:
                    if(device["device"] in profile["device"]):
                        if(not sharedCode.all_AinB(profile["signal"], device["signal"])):
                            tempDevVary = {"device": device["device"], "profile": device["profile"], "missingSignal": localExtractor(device["signal"], profile["signal"]), 
                                           "usedBy": profile["device"], "device_Signals": device["signal"], "profile_Signals": profile["signal"]}#},
                                           #"duplicatedSignals_Device": device["duplicatedSignals"], "duplicatedSignals_Profile": profile["duplicatedSignals"]}
                            #print(tempDevVary)
                            checKData.append(tempDevVary) if tempDevVary not in checKData else next

            """
            df_selected = pd.DataFrame() 
            checKData = []
            missingProfileData = []
            for device in TempArrDevices:
                for profile in TempArrProfiles:
                    if(device["device"] in profile["device"]):
                        if(not sharedCode.all_AinB(profile["signal"], device["signal"])):
                            tempDevVary = {"device": device["device"], "profile": profile["profile"], "missingSignal": localExtractor(device["signal"], profile["signal"]), "deviceSignals": device["signal"], "profileSignals": profile["signal"]}
                            #print(tempDevVary)
                            checKData.append(tempDevVary) if tempDevVary not in checKData else next
                    if(profile["profile"] in device["profile"]):
                        if(not sharedCode.all_AinB(profile["signal"], device["signal"])):
                            0
                            tempDevVary = {"device": device["device"], "profile": profile["profile"], "missingSignal": localExtractor(device["signal"], profile["signal"]), "deviceSignals": device["signal"], "profileSignals": profile["signal"]}
                            #print(tempDevVary)
                            checKData.append(tempDevVary) if tempDevVary not in checKData else next
                            #profyData = {"profile": profile["profile"], "device": device, "missingSignal": localExtractor(device["signal"], profile["signal"])}
                            ##print(f"{profyData}")
                            #missingProfileData.append(profyData) if profyData not in missingProfileData else next
                    #if(device["device"] in profile["device"]):
                    #    checcky = sharedCode.all_AinB(profile["signal"], device["signal"])
                    #    print(f"{device["device"]} -> {device["profile"]} -> {device["signal"]} | {profile["signal"]}\t{checcky}")
            #for dm in missingProfileData:
            #    print(dm)
            """
            if(len(checKData) != 0):
                for key in checKData[0].keys():
                    df_selected[key] = None
                for index, chkData in enumerate(checKData):
                    for key in chkData.keys():
                        if(chkData[key] != "" or chkData[key] != "nan"):
                            df_selected.at[index, key] = chkData[key]
            if(not fileName.endswith(".xlsx")):
                fileName += ".xlsx"
            sCheck = sharedCode.rw_xlsx(path = DownloadsFileFolder, file = f"_Controlli_{outFileName}_{fileName}", df = {"CheckProfileSignals": df_selected}, mode = "save")
            return (f"_Controlli_{outFileName}_{fileName}") if sCheck else None


    def checkColumns_(df, target, newColumnsArray):
        colonneRif = sharedCode.loadSettings(target, "colonneIN")
        for colonna in colonneRif:  
            if not colonna in df.columns:                  
                yield (f"Colonna {colonna} non trovata!") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(f"Colonna {colonna} non trovata!")
                df[colonna] = None
                
        newColumns = sharedCode.loadSettings(target, "outputColumns")
        for newColonna in newColumns:   
            if not newColonna in df.columns:     
                df[newColonna] = None
                
                
    def logicExtractor():        
        """
        Estrae le variabili con la logica dalla colonna 'NewLogica' cercando la presenza di un uguaglianza: ' : = - ' e di un divisiore: ', ; / '
        - NB: Esegue la normalizzazione delle parole nella logica!
        
        """
        egualator = "[:=-]"
        divider = "[,;/]"
        for index, row in df.iterrows():
            foundLogicFlag = False
            for item in egualator+divider:
                if( item in str(row["NewLogica"])):
                    if("NON" in str(row["NewLogica"]).upper() or "NOT" in str(row["NewLogica"]).upper() or "IN" in str(row["NewLogica"]).upper()):
                        df.at[index, "NewLogica"] = str(row["NewLogica"]).replace("NON ","NON").replace("NOT ","NOT").replace("IN","")
                    foundLogicFlag = True
            if(foundLogicFlag == True):                
                tempData = re.split(r""+divider, str(row["NewLogica"]))
                arrOfArr = [[ subElem if subElem.isdigit() else (subElem) for subElem in re.split(r""+egualator, elem)] for elem in tempData]
                df.at[index, "NewLogica"] =  str("/".join("=".join (a.strip() for a in arr) for arr in arrOfArr))
                df.at[index, "NewLogica"] = df.at[index, "NewLogica"][:-1] if df.at[index, "NewLogica"].endswith("/") else df.at[index, "NewLogica"]
                tempLeftOvers = normalizzatore.paroleNonCensite((str(row["NewLogica"])), indexedAliasArray, splitRule = splitRule)
                df.at[index, "LogicLeftOvers"] = str(tempLeftOvers) if str(tempLeftOvers) != "NAN" else ""
                for item in df.at[index, "LogicLeftOvers"].split():
                    if(item == "IN"):
                        df.at[index, "LogicLeftOvers"] = df.at[index, "LogicLeftOvers"].replace(item,"")
                if(df.at[index, "LogicLeftOvers"] == "" and df.at[index, "NewLogica"].count("/") <= 2):
                    arrOfArr = [[ subElem if subElem.isdigit() else normalizeString(subElem) for subElem in re.split(r""+egualator, elem)] for elem in tempData]
                    df.at[index, "NewLogica"] =  str("/".join("=".join (a for a in arr) for arr in arrOfArr)).replace(".0","")
    
    
    def reAssignDataType():     
        """
        Riassegna il data type (bool, int, float) nel formato corretto
        """
        
        for index, row in df.iterrows():
            tempLogic = df.at[index, "NewLogica"] if df.at[index, "NewLogica"] != "" else None
            tempVal = None
            tempNewDType = sharedCode.fill_DataType(str(df.at[index, "NewDataValueType"]), dataTypeDict, profile = True)
            if(tempNewDType):
                tempNewDType = tempNewDType.capitalize()
            df.at[index, "NewDataValueType"] = tempNewDType #if (str(row["NewDataValueType"]) != "" or df.at[index, "NewDataValueType"] != None) else ""
            if(tempLogic and type(tempLogic) == str):
                for item in tempLogic.split("/"):
                    if(any(itemLog in tempLogic for itemLog in ["112","113","115","118","50","50%","75","75%","100","100%"] )):
                        for pholder in ["112","113","115","118","50","50%","75","75%","100","100%"]:
                            item = item.replace(pholder, "PLACEHOLDER")
                    tempVal = "".join(re.findall(r"\d+",item.replace(".0","")))            
            elif(tempLogic and type(tempLogic) != str):
                    tempVal = "".join(re.findall(r"\d+",str(tempLogic).replace(".0","")))
            if(tempVal and int(tempVal) > 1):
                if(df.at[index, "NewDataValueType"] and df.at[index, "NewDataValueType"].upper() != "INTEGER"):
                    #sharedCode.noticeUpdate(index, f"assigned INT: {df.at[index, "NewDataValueType"]} -> Integer")
                    df.at[index, "NewDataValueType"] = "Integer"
                    noticeUpdate(index, f"tempVal:  {tempVal}")
                    
    
    def normalizeData():   
        """
        Normalizza i dati delle colonne 'NewProfileName' + 'NewSignalName' + 'NewSignalDescription' + 'NewLogica'
        """
        if("NormalizedData" not in df.columns):
            df["NormalizedData"] = None
        if("LeftOvers" not in df.columns):
            df["LeftOvers"] = None
        counter = 0
        for index, row in df.iterrows():
            if not pd.isna(row["NewProfileName"]):
                dataSet = str(row["NewProfileName"]) +" "+ str(row["NewSignalName"]) +" "+ str(row["NewSignalDescription"]) + " " + str(row["NewLogica"])
                #df.at[index, "NewSignalName"] = normalizeString(str(row["NewSignalName"])).replace(" ","-")  if "STAND_ALONE" not in fileName else str(row["NewSignalName"])# to review !   
                #df.at[index, "NormalizedData"] = str(sharedCode.normalizeAll((dataSet), "signal", dictionary, splitRule))   
                #df.at[index, "LeftOvers"] = str(sharedCode.leftOverWords((dataSet), dictionary, splitRule)) 

                normData = normalizzatore.normalizzaDati(dataSet, dictionary, aliasArray = indexedAliasArray, splitRule = splitRule)
                if(normData):
                    df.at[index, "NormalizedData"] = normData
                    df.at[index, "LeftOvers"] = normalizzatore.paroleNonCensite(dataSet, indexedAliasArray, splitRule = splitRule)
            counter += 1
            #sharedCode.progress(index, len(df))
            msg = sharedCode.progressYield(counter, len(df.index))
            if(msg):
                yield msg 
    

     #CMD-ST -> COMANDO
    
    
    def defineCommands():
        for index, row in df.iterrows():  
            if ((str(row["NewSignalName"]).startswith('CMD-')) or (str(row["NewSignalName"]).startswith('CMD-ST-'))):#or (str(row["NewSignalName"])).startswith('ST-CMD')):
                df.at[index, "valueBound"] = 'RANGE'
                if(df.at[index, "NewSignalName"].startswith('CMD-ST-')):
                    logica = str(row["NewLogica"]).strip()
                    hasCustomLogic = logica and logica != "nan" and "=" in logica and "/" in logica
                    if hasCustomLogic:
                        tempStr = [s.strip() for s in logica.split("/")]
                        tempValueObj = []
                        for part in tempStr:
                            if "=" in part:
                                splitPart = part.split("=", 1)
                                if splitPart[0].strip().lstrip("-").isdigit():
                                    prototipo = {
                                        "value": int(splitPart[0].strip()),
                                        "description": splitPart[1].strip()
                                    }
                                    tempValueObj.append(prototipo)
                        if tempValueObj:
                            df.at[index, "valueObjects"] = str(tempValueObj).replace("'", '"')
                            df.at[index, "NewDataValueType"] = "Integer"
                            noticeUpdate(index, f"CMD-ST - valueObjects elaborati da logica")
                    else:
                        for valueObject in valueObjects:
                            if(logica == "0"):
                                if (valueObject["_id"] == "valueObjects_1_NO_0_SI"):
                                    df.at[index, "valueObjects"] = valueObject["data"]
                            else:
                                if (valueObject["_id"] == "valueObjects_0_NO_1_SI"):
                                    df.at[index, "valueObjects"] = valueObject["data"]
                    df.at[index, "valueBound"] = 'LIST'
                    df.at[index, "hidden"] = 'FALSE'
                else:
                    df.at[index, "hidden"] = 'TRUE'
                if("=" in str(row["NewLogica"])):
                    for logic in str(row["NewLogica"]).split("="):
                        if(logic.isnumeric()):
                            df.at[index, "parameter"] = str(int(logic))
                else:
                    df.at[index, "parameter"] = str(row["NewLogica"]) if str(row["NewLogica"]) != "nan" else 1
               # if(df.at[index, "NewDataValueType"].upper() != "BOOLEAN" and ((str(row["NewLogica"])!= 0 or str(row["NewLogica"])!= 1))and str(row["NewLogica"]) != ""):
                if(not df.at[index, "NewSignalName"].startswith('CMD-ST-') and df.at[index, "NewDataValueType"].upper() != "BOOLEAN" and str(row["NewLogica"]) != "" and str(row["NewLogica"]) != "nan"):                    
                    df.at[index, "valueBound"] = "UNBOUNDED"
                df.at[index, "valueMin"] = '0'
                df.at[index, "valueMax"] = '1'
                df.at[index, "tags"] = '[Commands]'        
                df.at[index, "commandDescription"] = str(row["NewSignalDescription"])
                df.at[index, "commandRoleLevel"] = '0'
                df.at[index, "commandBody"] = CommandBody

                for OperationBody in OperationBodies:
                    if (OperationBody["_id"] == "operationBody"):
                        df.at[index, "operationBody"] = OperationBody["data"] 

    # ST-CMD -> STATO
    def defineStates():
        for index, row in df.iterrows():
            if (str(row["NewSignalName"]).startswith('ST-') and not "MIS" in str(row["NewSignalName"])):
                df.at[index, "valueBound"] = 'LIST'
                df.at[index, "hidden"] = "FALSE"
                if(str(row["NewSignalName"]).startswith("ST-CMD-")):
                    df.at[index, "tags"] = '[States]'
                    df.at[index, "parameter"] = '1'
                    df.at[index, "valueMin"] = '0'
                    df.at[index, "valueMax"] = '1'
                    df.at[index, "commandBody"] = CommandBody
                    for OperationBody in OperationBodies:
                        if (OperationBody["_id"] == "operationBody"):
                            df.at[index, "operationBody"] = OperationBody["data"] 
                else:
                    df.at[index, "tags"] = '[States]'
                assignValueObject(df, index, row)
                

    def defineAllarms():    #re-do: c'è qualcosa che non va ma non si sa cosa!     
        alrKWords = "".join([word for word in [words["data"] if words["_id"] == "AlrKWords" else None for words in sharedCode.loadSettings("profilatorSettings", "thresholdsValues")] if word != None])
        for index, row in df.iterrows():    
            if(str(df.at[index, "NewSignalName"]).strip().startswith('ALR-')):
                df.at[index, "valueBound"] = 'RANGE'
                df.at[index, "hidden"] = 'FALSE'
                df.at[index, "valueMin"] = '0'
                df.at[index, "valueMax"] = '1'
                df.at[index, "tags"] = '[Alarms]'                
                normLogic = str(row["NewLogica"]) if "NewLogica" in df.columns else ""
                logicType = (logicValType(normLogic))
                changedValA = ""
                changedValB = ""                
                
                if(logicType):                    
                    if(logicType == "DEFAULT"):
                        for threshold in thresholdsData:        #"".join(re.findall(r"\d+", x)   
                            if("/" not in normLogic and "=" in normLogic and normLogic != "nan"):
                                logicValue = int("".join(re.findall(r"\d+", normLogic)))
                                if(logicValue == 0 or logicValue == 1):
                                    if("0" in normLogic and threshold["_id"] == "THRESHOLD_AT0"):
                                        df.at[index, "thresholds"] = threshold["data"]
                                    elif("1" in normLogic and threshold["_id"] == "THRESHOLD_AT1"):
                                        df.at[index, "thresholds"] = threshold["data"]     
                                    noticeUpdate(index, f"if DEFAULT normLogic: {normLogic} -> {logicValue}")                                      
                                elif(logicValue != 0 and logicValue > 1):
                                    if(threshold["_id"] == "THRESHOLD_AT1"):
                                        df.at[index, "thresholds"] = threshold["data"].replace('"CRITICAL", "lower":"1", "upper":"1"', f'"CRITICAL", "lower":"{logicValue}", "upper":"{logicValue}"') 
                                    noticeUpdate(index, f"else DEFAULT normLogic: {normLogic} -> {logicValue}") 
                            elif("/" not in normLogic and "=" not in normLogic and normLogic == "nan"): 
                                for threshold in thresholdsData:                                            
                                    if( threshold["_id"] == "THRESHOLD_AT1" ):                           
                                        df.at[index, "thresholds"] = threshold["data"]   
                    
                    elif(logicType == "VALUE"):                          
                        intLogicValue = ([int(i) for i in normLogic.split("=") if i.isdigit()][0]) 
                        for threshold in thresholdsData:                      
                            if(intLogicValue > 1):
                                if(threshold["_id"] == "THRESHOLD_AT1"):
                                    df.at[index, "thresholds"] = threshold["data"].replace('"CRITICAL", "lower":"1", "upper":"1"', f'"CRITICAL", "lower":"{intLogicValue}", "upper":"{intLogicValue}"')  
                                    if(df.at[index, "NewDataValueType"].upper() != "INTEGER"):
                                        changedValA = f' | Modificato [valueType]: [{df.at[index, "NewDataValueType"]}] -> [Integer]'
                                    if(df.at[index, "valueBound"] != "UNBOUNDED"):
                                        changedValB = f' & [valueBound]:[{df.at[index, "valueBound"]}] -> [UNBOUNDED]'
                                    #df.at[index, "Notice"] = f'ALR - thresholds & Logic value [{intLogicValue}]{changedValA}{changedValB}' 
                                    noticeUpdate(index, f"if DEFAULT normLogic: {normLogic} -> {intLogicValue}")                                              
                                    df.at[index, "NewDataValueType"] = 'Integer'
                                    df.at[index, "valueBound"] = 'UNBOUNDED' 
                            else:                   
                                if("0" in normLogic and threshold["_id"] == "THRESHOLD_AT0" ):                        
                                    df.at[index, "thresholds"] = threshold["data"]
                                elif("1" in normLogic and threshold["_id"] == "THRESHOLD_AT1"):
                                    df.at[index, "thresholds"] = threshold["data"]
                        noticeUpdate(index, f"VALUE normLogic: {normLogic}")
                    
                    elif(int(logicType) >= 3):  
                        tempValueObj = []
                        for element in normLogic.split("/"):
                            valNum = ""
                            valDescr = ""
                            alrLevel = "CRITICAL"
                            labelColor = "#9A3324"
                            for elem in element.split("="):
                                if(elem.isnumeric() == False):
                                    valDescr = elem
                                    if(elem.upper() == "OK"):
                                        alrLevel = "NORMAL"
                                        labelColor = "#008C95"
                                        valDescr = "NOT ATTIVO"
                                if(elem.isnumeric() == True):
                                    valNum = elem
                            prototipo = {'"emitInThresholdReadingsType":"VALUE_CHANGE", "emitAlarm":true, "alarmLevel":"%s", "lower":"%s", "upper":"%s", "label":"%s", "labelColor":"%s", "alarmDestination":"ALL"'%(alrLevel, valNum, valNum, valDescr,labelColor)}
                            tempValueObj.append(prototipo)   
                        intLogicValue = ([int(i) for i in normLogic.split("=") if i.isdigit()][0])
                        df.at[index, "thresholds"] = threshold["data"].replace('"CRITICAL", "lower":"1", "upper":"1"', f'"CRITICAL", "lower":"{intLogicValue}", "upper":"{intLogicValue}"')  
                        if(df.at[index, "NewDataValueType"].upper() != "INTEGER"):
                            changedValA = f'Modificato [valueType]: [{df.at[index, "NewDataValueType"]}] -> [Integer]'
                        if(df.at[index, "valueBound"].upper() != "UNBOUNDED"):
                            changedValB = f' & [valueBound]:[{df.at[index, "valueBound"]}] -> [UNBOUNDED]'          
                        df.at[index, "Notice"] = f'{changedValA}{changedValB} <!_check_!>'
                        df.at[index, "NewDataValueType"] = "Integer"
                        df.at[index, "valueBound"] = "UNBOUNDED"                        
                        df.at[index, "thresholds"] = str(tempValueObj).replace("'","")
                    
                    elif(int(logicType) <= 2):               
                        for logic in normLogic.split("/"):
                            intLogicValue =  ([int(i) for i in logic.split("=") if i.isdigit()][0])
                            if(sharedCode.any_AinB(alrKWords, logic)):   
                                for threshold in thresholdsData:                                                          
                                    if("0" in logic and threshold["_id"] == "THRESHOLD_AT0" ):                        
                                        df.at[index, "thresholds"] = threshold["data"]
                                    elif("1" in logic and threshold["_id"] == "THRESHOLD_AT1"):
                                        df.at[index, "thresholds"] = threshold["data"]
                                    elif(intLogicValue > 1):
                                        if(threshold["_id"] == "THRESHOLD_AT1"):
                                            df.at[index, "thresholds"] = threshold["data"].replace('"CRITICAL", "lower":"1", "upper":"1"', f'"CRITICAL", "lower":"{intLogicValue}", "upper":"{intLogicValue}"')  
                                            if(df.at[index, "NewDataValueType"].upper() != "INTEGER"):
                                                changedValA = f'Modificato [valueType]: [{df.at[index, "NewDataValueType"]}] -> [Integer]'
                                            if(df.at[index, "valueBound"].upper() != "UNBOUNDED"):
                                                changedValB = f' & [valueBound]:[{df.at[index, "valueBound"]}] -> [UNBOUNDED]'                                              
                                            df.at[index, "Notice"] = f'ALR - thresholds & Logic value [{intLogicValue}]{changedValA}{changedValB}'                                            
                                            df.at[index, "NewDataValueType"] = 'Integer'
                                            df.at[index, "valueBound"] = 'UNBOUNDED'
                    else:                      
                        print(f"else: {logicType} -> {str(row["NewLogica"])}")     
                
                if(str(row["NewDataValueType"]).upper() !=  "BOOLEAN"):
                    if(df.at[index, "Notice"] != None and str(df.at[index, "Notice"]) != "nan"):
                        df.at[index, "Notice"] += " ALR - Ceck [valueType]"
                    else:
                        df.at[index, "Notice"] = "ALR - Ceck [valueType]"
                
                if(df.at[index, "thresholds"] == "nan" or df.at[index, "thresholds"] == "" or df.at[index, "thresholds"] == None):
                    for threshold in thresholdsData:    
                        if(threshold["_id"] == "THRESHOLD_AT1" ):
                            df.at[index, "thresholds"] = threshold["data"]                            
                
                            noticeUpdate(index, f"Assegnazione di default")     
            elif("-ALR" in str(row["NewSignalName"]).upper()):
                df.at[index, "Notice"] = "ALR - possibile allarme ?"

    
    def defineMisure():
        for index, row in df.iterrows():            
            if (str(row["NewSignalName"]).startswith('MIS-')):  
                if (str(row["NewSignalName"]).startswith('MIS-') and not (str(row["NewSignalName"]).startswith('MIS-ST') or df.at[index, "NewSignalName"].startswith('MIS-MSG'))):    
                    df.at[index, "valueBound"] = 'UNBOUNDED'
                    df.at[index, "hidden"] = 'FALSE'
                    df.at[index, "tags"] = '[Measures]'
                    df.at[index, "defaultValue"] = '0'
                elif(str(row["NewSignalName"]).startswith('MIS-ST') or str(row["NewSignalName"]).startswith('MIS-MSG')):
                    df.at[index, "valueBound"] = 'LIST'
                    df.at[index, "hidden"] = 'FALSE'
                    df.at[index, "Notice"] = f'Misura-Stato? | modificato: [valueType] da {df.at[index, "NewDataValueType"]} -> [Integer]'
                df.at[index, "tags"] = '[Measures]'
                df.at[index, "defaultValue"] = '0'
                if(str(row["NewSignalName"]).startswith('MIS-ALR')):
                    df.at[index, "tags"] = '[Alarms]'
                    df.at[index, "valueBound"] = 'LIST'
                    df.at[index, "hidden"] = 'TRUE'
                    df.at[index, "thresholds"] = "{}" 
                    df.at[index, "Notice"] = "MIS/ALR - possibile Misura & Allarme ?" 
                normLogic = str(row["NewLogica"]) if "NewLogica" in df.columns else ""
                logicType = (logicValType(normLogic))                
                if(logicType != "DEFAULT"):
                    if("/" in str(row["NewLogica"]) and "=" in str(row["NewLogica"])):
                        tempStr = str(row["NewLogica"]).split("/")
                        tempValueObj = []
                        if(tempStr and len(tempStr) != 0):
                            for i in range (len(tempStr)):
                                if("=" in tempStr[i]):
                                    prototipo = {"value": int((tempStr[i].split("=")[0])), "description": tempStr[i].split("=")[1]}   
                                    tempValueObj.append(prototipo)
                            df.at[index, "valueObjects"] = str(tempValueObj).replace("'",'"')#.upper()                        
                            df.at[index, "Notice"] = f'Modificato [valueType] da {df.at[index, "NewDataValueType"]} -> [Integer] & [valueBound] da {df.at[index, "valueBound"]} -> LIST'
                            df.at[index, "NewDataValueType"] = "Integer"
                            df.at[index, "valueBound"] = "LIST"
                        else:
                            print(f"error: {str(row["NewLogica"])}")
                    else: 
                        df.at[index, "Notice"] = "MIS - dati in logica non elaborati"
                elif(normLogic != "" and normLogic != "nan"):
                    df.at[index, "Notice"] = "MIS - dati in logica non elaborati"
                if(df.at[index, "NewDataValueType"].upper() == "FLOAT"):
                    df.at[index, "decimalPlaces"] = "2"
                    

    def defineParams():     #re-do !   
        for index, row in df.iterrows():
            if (str(row["NewSignalName"]).startswith('PAR-')):
                
                logica = str(df.at[index, "NewLogica"]).strip()
                hasLogic = logica and logica != "nan" and logica != "None"
                
                df.at[index, "valueBound"] = 'LIST' if hasLogic else 'UNBOUNDED'
                df.at[index, "hidden"] = 'TRUE'
                df.at[index, "tags"] = '[Parameters]'
                df.at[index, "defaultValue"] = '0'
                df.at[index, "commandDescription"] = str(row["NewSignalDescription"])
                df.at[index, "commandRoleLevel"] = '0'
                df.at[index, "commandBody"] = CommandBody_PAR
                for OperationBody in OperationBodies:
                    if (OperationBody["_id"] == "operationBody_PAR"):
                        df.at[index, "operationBody"] = OperationBody["data"]

                # ← BLOCCO MANCANTE: elabora la logica come fa defineMisure()
                if hasLogic and "/" in logica and "=" in logica:
                    tempStr = logica.split("/")
                    tempValueObj = []
                    for i in range(len(tempStr)):
                        if("=" in tempStr[i]):
                            prototipo = {
                                "value": int(tempStr[i].split("=")[0]),
                                "description": tempStr[i].split("=")[1]
                            }
                            tempValueObj.append(prototipo)
                    if tempValueObj:
                        df.at[index, "valueObjects"] = str(tempValueObj).replace("'", '"')
                        df.at[index, "NewDataValueType"] = "Integer"
                        noticeUpdate(index, f"PAR - valueObjects elaborati da logica")
                    else:
                        noticeUpdate(index, f"PAR - logica presente ma non elaborata: {logica}")
                elif hasLogic:
                    noticeUpdate(index, f"PAR - logica presente ma non elaborata: {logica}")

    
    def noticeUpdate(index, inString):
        """
        Esegue l'upldate della colonna 'Notice' alla riga 'index' con la stgringa in input 
        """
        if(len(inString) != 0):
            if(df.at[index, "Notice"] == "" or str(df.at[index, "Notice"]) == "nan" or df.at[index, "Notice"] == None):
                df.at[index, "Notice"] = f"|{inString}|"     
            elif(df.at[index, "Notice"] != "" or df.at[index, "Notice"] != None or str(df.at[index, "Notice"]) == "nan"):
                df.at[index, "Notice"] += f" & |{inString}|" if f"{inString}" not in str(df.at[index, "Notice"]) else ""
    
    
    def staticValues():
        for index, row in df.iterrows():
            for val in defaultValuesDict:
                if(val["_id"] == "defaultReadingExpireTime"):
                    df.at[index, "readingExpireTime"] = val["data"]
                if(val["_id"] == "defaultReadingExpireTime"):
                    df.at[index, "readingExpireTime"] = val["data"]
                elif(val["_id"] == "defaultEmitReadings"):
                    df.at[index, "emitReadings"] = val["data"]
                elif(val["_id"] == "defaultVirtual"):
                    df.at[index, "virtual"] = val["data"]
                elif(val["_id"] == "defaultScale"):
                    df.at[index, "scale"] = val["data"]


    def logicValType(logicIn):
        logVal = ""
        if("/" in logicIn):
            logVal =  len(logicIn.split("/"))
        elif(logicIn.isdigit()):
            logVal =  "VALUE"
        elif("/" not in logicIn and not logicIn.isdigit()):
            logVal =  "DEFAULT"
        return logVal 
                
                
    def appendUOM():
        egualator = [":", "=", "-"]
        divider = [",", ";", "/"]
        for index, row in df.iterrows():  
            foundLogicFlag = False                  
            if(str(row["NewLogica"]) != "" and (row["NewLogica"]) != None and str(row["NewLogica"]) != "nan"):            
                for item in egualator+divider:
                    if( item in str(row["NewLogica"])):
                        if("NON" in str(row["NewLogica"]).upper() or "NOT" in str(row["NewLogica"]).upper() or "IN" in str(row["NewLogica"]).upper()):
                            df.at[index, "NewLogica"] = str(row["NewLogica"]).replace("NON ","NON").replace("NOT ","NOT").replace("IN","")
                        foundLogicFlag = True                    
                if(foundLogicFlag == False and str(row["NewLogica"]).isdigit() == False):
                    df.at[index, "NewUOM"] = str(row["NewLogica"])
                    df.at[index, "NewLogica"] = ""
                
            if((str(row["NewUOM"]) == "" or row["NewUOM"] == None or str(row["NewUOM"]) == "nan") and (str(row["NewSignalName"]).startswith("MIS-") or str(row["NewSignalName"]).startswith("PAR-"))):
                descr = str(row["NewProfileName"]) + "-" + str(row["NewSignalName"]) + "-" + str(row["NewSignalDescription"]).lower() #df.at[index, "NewSignalName"] + "-" + df.at[index, "NewSignalDescription"]
                if(sharedCode.any_AinB("vibraz vibrazioni vibrazione", descr) == True):
                    df.at[index, "NewUOM"] = "mm/s²"
                if(sharedCode.any_AinB("AN anemometro vento", descr) == True):
                    df.at[index, "NewUOM"] = "m/s"
                if(sharedCode.any_AinB("CO NO", descr) == True):
                    df.at[index, "NewUOM"] = "ppm"
                if(sharedCode.any_AinB("OP opacimetro", descr) == True):
                    df.at[index, "NewUOM"] = "1/km"
                if(sharedCode.any_AinB("contaore ore", descr) == True):
                    df.at[index, "NewUOM"] = "h"
                if(sharedCode.any_AinB("secondi", descr) == True):
                    df.at[index, "NewUOM"] = "s"
                if(sharedCode.any_AinB("tensione tens", descr) == True):
                    df.at[index, "NewUOM"] = "V"
                if(sharedCode.any_AinB("corrente assorbimento corr", descr) == True):
                    df.at[index, "NewUOM"] = "A"
                if(sharedCode.any_AinB("potenza", descr) == True):
                    df.at[index, "NewUOM"] = "kW"
                if(sharedCode.any_AinB("frequenza freq", descr) == True):
                    df.at[index, "NewUOM"] = "Hz"
                if(sharedCode.any_AinB("temperatura", descr) == True):
                    df.at[index, "NewUOM"] = "°C"
                if(sharedCode.any_AinB("metri metro metrica posizione minuti pos", descr) == True):
                    df.at[index, "NewUOM"] = "m"
                if(sharedCode.any_AinB("luminanza illuminazione sonda", descr) == True):
                    df.at[index, "NewUOM"] = "cd/m²"
                if(sharedCode.any_AinB("rpm giri", descr) == True):
                    df.at[index, "NewUOM"] = "RPM"
                if(df.at[index, "NewUOM"] != None and "%" in descr):
                    df.at[index, "NewUOM"] = str(df.at[index, "uom"]) + "%"
        
      
    def cercaDoppioni():
        arrProfili = []
        arrAlrClass = []
        for index, row in df.iterrows():
            strProfili = str(row["NewProfileName"]) + " " + str(row["NewSignalName"])# + " " + str(row["NewSignalDescription"])
            if(("nan" not in strProfili or strProfili != "") and strProfili not in arrProfili):
                arrProfili.append(strProfili)
            elif(("nan" not in strProfili or strProfili != "") and strProfili in arrProfili):
                df.at[index, "Profili Dupplicati"] = "Profilo dupplicato"
            
            if(str(row["NewAlarmClass"]) != "nan"):
                strAlrClass = str(row["NewProfileName"]) + " " + str(row["NewAlarmClass"]) + " " + str(row["NewAlarmDescription"])
                if(("nan" not in strAlrClass or strAlrClass != "") and strAlrClass not in arrAlrClass):
                    arrAlrClass.append(strAlrClass) 
                elif(("nan" not in strAlrClass or strAlrClass != "") and strAlrClass in arrAlrClass):
                    df.at[index, "alrClass Dupplicati"] = "ALR_Class dupplicato"  


    def assignValueObject(df, index, row): 
        """
        Cerca di assegnare i ValueObject ai segnali STATO
        """       
        signalData = str(df.at[index, "NewSignalName"])
        rawDescr = str(df.at[index, "NewSignalDescription"])
        descrData = normalizeString(rawDescr)   
        normLogic = str(df.at[index, "NewLogica"]).replace(".0","") 
        defaultValueObjsDefault = ["valueObjects_1_NO_0_SI", "valueObjects_0_NO_1_SI"]      
        choiceString = ["AP", "CH", "AUTO", "MAN", "INCL", "ESCL", "INSERT", "DISINSERT", "FORZ", "LOC", "LOCAL", "REM", "REMOT", "NORD", "SUD", "RED", "GREEN", "YELLOW", "ORANGE", "SI", "NO"]

        def ValueObjectBuilder(dataArr):
            if(len(dataArr) >= 2):
                tempValueObj = []  
                valNum = None
                valDescr = None
                for item in dataArr:
                    for obj in item.split("="):
                        if(obj.isdigit()):
                            valNum = obj
                        else:
                            valDescr = obj                            
                    #valDescr = str(sharedCode.normalizeAll((valDescr), "sig_descr", dictionary, splitRule)).upper() if valDescr and df.at[index, "LogicLeftOvers"] == "" and not ("NO" in valDescr and "SI" in valDescr) else valDescr
                    valDescr = str(normalizzatore.normalizzaDati(valDescr, dictionary, splitRule = splitRule, aliasArray = indexedAliasArray, returnType  = "sig_descr")).upper() if valDescr and df.at[index, "LogicLeftOvers"] == "" and not ("NO" in valDescr and "SI" in valDescr) else valDescr

                    prototipo = {"value": int(valNum), "description": valDescr.upper()}   
                    tempValueObj.append(prototipo) 
                noticeUpdate(index, f"controllare descrizione [valueObject]")                   
                return tempValueObj

        def checkData(varsArr):
            """
            Definisce cosa utilizzare per i controlli
            - LOGICA: scartare le informazioni del segnale e della descrizione e utilizzare solo la logica
            - DEFAULT_DESCR: scartare le informazioni del segnale e utilizzare la descrizione
            - LOGICA_SIGN: 
            - ERRORE:
            - CHECK: 
            """
            tempSignalData = signalData.split("-")
            tempDescrData = descrData.split()
            operazione = ""
            if(all(item in tempSignalData for item in varsArr) and all(item in tempDescrData for item in varsArr)): 
                operazione = "LOGICA"   # all in sign not descr
            elif(all(item in tempSignalData for item in varsArr) and not any(item in tempDescrData for item in varsArr)): 
                operazione = "LOGICA"   # all in sign not descr
            elif(all(item in tempSignalData for item in varsArr) and any(item in tempDescrData for item in varsArr)): 
                operazione = "DEFAULT_DESCR"   # all in sign any descr
            elif(not any(item in tempSignalData for item in varsArr) and all(item in tempDescrData for item in varsArr)): 
                operazione = "LOGICA"   # not sign all descr
            elif(any(item in tempSignalData for item in varsArr) and all(item in tempDescrData for item in varsArr)): 
                operazione = "LOGICA_SIGN"   # any sign all descr 
            elif(any(item in tempSignalData for item in varsArr) and not any(item in tempDescrData for item in varsArr)): 
                operazione = "LOGICA_SIGN"   # any sign not descr 
            elif(not any(item in tempSignalData for item in varsArr) and any(item in tempDescrData for item in varsArr)): 
                operazione = "DEFAULT_DESCR"   # no sign any descr 
            elif(any(item in tempSignalData for item in varsArr) and any(item in tempDescrData for item in varsArr)): 
                for item in varsArr:
                    if(item in tempSignalData and item in tempDescrData):
                        operazione = "DEFAULT_DESCR"   # any sign any descr 
                    elif(item in tempSignalData and item not in tempDescrData):
                        operazione = "ERRORE"   # any sign not any descr mismatch
            else:
                operazione = "CHECK"
            return operazione

        def extractLogic():
            if(normLogic == "nan" or normLogic == None):
                return None
            elif(normLogic != "nan" and normLogic != None):
                logiky = {"valore" : []}
                logicCount = normLogic.count("=")
                if(logicCount == 0):
                    if(normLogic.isdigit()):
                        logiky["valore"].append(normLogic.strip())
                    elif(not normLogic.isdigit()):
                        logiky["valore"].append(normLogic.strip())# "".join(re.findall(r"\d+",normLogic)))
                if(logicCount > 0 and logicCount <= 2):      
                    for item in normLogic.split("/"):
                        logiky["valore"].append(item.strip()) 
                if(logicCount > 2):
                    for item in normLogic.split("/"):
                        logiky["valore"].append(item.strip()) 
                return logiky
            
        def valueObjectAssigner(logicArr, valObjArr, elabType, varsArr):
            if(logicArr):
                if(len(logicArr) == 1): 
                    if(elabType == "DEFAULT_DESCR"):
                        for logikData in logicArr:
                            if(not "=" in logikData and logikData.isdigit()): 
                                tempVal = "".join(re.findall(r"\d+",logikData))
                                for valObject in valObjArr:
                                    if((f"NO_{tempVal}_SI") in valObject): 
                                        for valueObject in valueObjects: 
                                            if (valueObject["_id"] == valObject):
                                                return valueObject["data"]
                            elif("=" in logikData):
                                for item in logikData.split("="):
                                    if(not item.isdigit()):
                                        tempFound = normalizeString(item)
                                        if(tempFound in descrData):
                                            tempVal = "".join(re.findall(r"\d+",logikData))
                                            for valObject in valObjArr:
                                                if((f"NO_{tempVal}_SI") in valObject):  
                                                    for valueObject in valueObjects: 
                                                        if (valueObject["_id"] == valObject):
                                                            return valueObject["data"] 
                                        elif(tempFound not in descrData):
                                            tempVal = "".join(re.findall(r"\d+",logikData))
                                            tempVary = f"_{tempVal}_{tempFound}"
                                            for tempValObjy in valueObjects:
                                                if(tempVary in tempValObjy["_id"]):                                                    
                                                    tempItem = tempValObjy["_id"].replace("valueObjects","").replace(tempVary,"")
                                                    for suby in tempItem:
                                                        tempItem = (normalizeString(tempItem)).replace(" ","=") if type(suby)==str else next
                                                    for item in tempItem.split("="):
                                                        if(not item.isdigit()):
                                                            tempVal2 = "".join(re.findall(r"\d+",tempItem))
                                                            for valObject in valObjArr:
                                                                if((f"NO_{tempVal2}_SI") in valObject):  
                                                                    for valueObject in valueObjects: 
                                                                        if (valueObject["_id"] == valObject):
                                                                            return valueObject["data"]
                    elif("LOGICA" in elabType):                  
                        for logikData in logicArr:
                            if(not "=" in logikData and logikData.isdigit()):             
                                tempVal = "".join(re.findall(r"\d+",logikData))
                                for valObject in valObjArr:
                                    if((f"NO_{tempVal}_SI") in valObject): 
                                        for valueObject in valueObjects: 
                                            if (valueObject["_id"] == valObject):
                                                return valueObject["data"]
                            elif("=" in logikData):
                                for item in logikData.split("="):
                                    if(not item.isdigit()):
                                        tempFound = normalizeString(item)
                                tempVal = "".join(re.findall(r"\d+",logikData))
                                for item in valObjArr:
                                    if((f"_{tempVal}_{tempFound}") in item):                     
                                        for valueObject in valueObjects: 
                                            if (valueObject["_id"] == item):
                                                return valueObject["data"]
                    elif("CHECK" in elabType):                        
                        for logikData in logicArr:
                            if("=" in logikData):
                                for item in logikData.split("="):
                                    if(not item.isdigit()):
                                        tempFound = normalizeString(item)
                                tempVal = "".join(re.findall(r"\d+",logikData))
                                for item in valObjArr:
                                    if((f"_{tempVal}_{tempFound}") in item):                     
                                        for valueObject in valueObjects: 
                                            if (valueObject["_id"] == item):
                                                return valueObject["data"]
                elif(len(logicArr) == 2): 
                    if("DEFAULT_DESCR" == elabType):                  
                        if("=" in logicArr[0]):
                            for logiky in logicArr:
                                for item in logiky.split("="):
                                    if(not item.isdigit()):
                                        tempFound = normalizeString(item)
                                        if(tempFound in descrData):
                                            tempVal = "".join(re.findall(r"\d+",logiky))
                                            for valObject in valObjArr:
                                                if((f"NO_{tempVal}_SI") in valObject): 
                                                    for valueObject in valueObjects: 
                                                        if (valueObject["_id"] == valObject):
                                                            return valueObject["data"] 
                    elif("LOGICA" in elabType):
                        if("=" in logicArr[0]):
                            for item in logicArr[0].split("="):
                                if(not item.isdigit()):
                                    tempFound = normalizeString(item)
                            tempVal = "".join(re.findall(r"\d+",logicArr[0]))
                            for item in valObjArr:
                                if((f"_{tempVal}_{tempFound}") in item):                  
                                    for valueObject in valueObjects: 
                                        if (valueObject["_id"] == item):
                                            return valueObject["data"]
                    elif("CHECK" in elabType):
                        if("=" in logicArr[0]):
                            for item in logicArr[0].split("="):
                                if(not item.isdigit()):
                                    tempFound = normalizeString(item)
                            tempVal = "".join(re.findall(r"\d+",logicArr[0]))
                            for item in valObjArr:
                                if((f"_{tempVal}_{tempFound}") in item):                  
                                    for valueObject in valObject: 
                                        if (valueObject["_id"] == item):
                                            return valueObject["data"]
                elif(len(logicArr) > 2):
                    print(f">>>\t\t{logicArr}")
            else:
                if(elabType == "LOGICA_SIGN"):                 
                    for item in valObjArr:
                        for varry in varsArr:
                            if((f"_1_{varry}") in item and varry in signalData):                  
                                for valueObject in valueObjects: 
                                    if (valueObject["_id"] == item):
                                        return valueObject["data"]
                elif(elabType == "LOGICA"):
                    if(not logicArr):
                        for valueObject in valueObjects: 
                            if (valueObject["_id"] == "valueObjects_0_NO_1_SI"):      
                                return valueObject["data"]
                    
                else:  
                    for valueObject in valueObjects: 
                        if (valueObject["_id"] == "valueObjects_0_NO_1_SI"):      
                            return valueObject["data"]

        def definer(varsArr, valObjArr):
            checkedData = checkData(varsArr)
            extractedLogic = extractLogic()
            tempValObj = None
            if(str(row["valueObjects"]) != "" or str(row["valueObjects"]) != "nan"):
                if(varsArr == ""):
                    tempValObj = ValueObjectBuilder(extractedLogic["valore"]) if extractedLogic and not tempValObj else tempValObj
                    tempValObj = valueObjectAssigner(None, valObjArr, checkedData, varsArr) if not tempValObj else tempValObj
                else:
                    if(extractedLogic):
                        if(checkedData == "CHECK"):
                            tempValObj = ValueObjectBuilder(extractedLogic["valore"]) if not tempValObj else tempValObj
                            tempValObj = valueObjectAssigner(extractedLogic["valore"], valObjArr, checkedData, varsArr) if not tempValObj else tempValObj
                        elif(checkedData == "LOGICA"):  
                            tempValObj = valueObjectAssigner(extractedLogic["valore"], valObjArr, checkedData, varsArr) #if not tempValObj else tempValObj
                        elif(checkedData == "LOGICA_SIGN"): 
                            tempValObj = valueObjectAssigner(extractedLogic["valore"], valObjArr, checkedData, varsArr) if not tempValObj else tempValObj
                        elif(checkedData == "DEFAULT_DESCR"): 
                            tempValObj = valueObjectAssigner(extractedLogic["valore"], defaultValueObjsDefault, checkedData, varsArr) if not tempValObj else tempValObj
                        elif(checkedData == "ERRORE"):
                            noticeUpdate(index, f"Block:{checkedData} MisMatch!")
                        else:
                            print(f">\t\tcheckedData: {checkedData}")
                            noticeUpdate(index, f"checkedData error: {checkedData}")
                    else:
                        tempValObj = valueObjectAssigner(None, valObjArr, checkedData, varsArr) if not tempValObj else tempValObj
                df.at[index, "valueObjects"] = tempValObj if tempValObj else ""
                noticeUpdate(index, "Missing: ValueObject!") if not tempValObj else noticeUpdate(index, str(varsArr))

        def Elaborazione():   
            def RemoveFromArr(reference, arrIn):
                for item in reference:
                    arrIn.remove(item) if item in arrIn else next
                return " ".join(arrIn)    
                    
            if(any(item in re.split(r""+splitRule, ((str(df.at[index, "NormalizedData"]) + " " +  normLogic))) for item in choiceString)):          
                currentChoices = ["AP", "CH"]       
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_CH_0_AP", "valueObjects_0_CH_1_AP"]
                    definer(currentChoices, usedValueObjects)
                currentChoices = ["AUTO", "MAN"]          
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_MAN_0_AUTO", "valueObjects_0_MAN_1_AUTO"]
                    definer(currentChoices, usedValueObjects)
                currentChoices = ["LOCAL", "REMOT"]          
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_LOCAL_0_REMOT", "valueObjects_0_LOCAL_1_REMOT"]
                    definer(currentChoices, usedValueObjects)
                currentChoices = ["INCL", "ESCL"]          
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_ESCL_0_INCL", "valueObjects_0_ESCL_1_INCL"]
                    definer(currentChoices, usedValueObjects)
                currentChoices = ["INSERT", "DISINSERT"]          
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_ESCL_0_INCL", "valueObjects_0_ESCL_1_INCL"]
                    definer(currentChoices, usedValueObjects)
                currentChoices = ["FORZ"]          
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_NON_0_FORZ", "valueObjects_0_NON_1_FORZ"]
                    definer(currentChoices, usedValueObjects)
                currentChoices = ["NORD", "SUD"]          
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_ESCL_0_INCL", "valueObjects_0_ESCL_1_INCL"]
                    definer(currentChoices, usedValueObjects)
                currentChoices = ["RED", "GREEN", "YELLOW", "ORANGE"]         
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_NO_0_SI", "valueObjects_0_NO_1_SI"]
                    definer(currentChoices, usedValueObjects)
                currentChoices = ["NO", "SI"]          
                if(sharedCode.condizioneComplessa(""," ".join(currentChoices), RemoveFromArr(currentChoices, choiceString), (str(row["NormalizedData"]) + " " + normLogic)) == True):
                    usedValueObjects = ["valueObjects_1_NO_0_SI", "valueObjects_0_NO_1_SI"]
                    definer(currentChoices, usedValueObjects)
                else:
                    0#print(f">>>\t{signalData} - {rawDescr}\t{normLogic}")
            else:          
                usedValueObjects = ["valueObjects_1_NO_0_SI", "valueObjects_0_NO_1_SI"]
                definer("", usedValueObjects)
                if(str(df.at[index, "valueObjects"]) == "nan" or str(df.at[index, "valueObjects"]) == "" or df.at[index, "valueObjects"] == None):                    
                    for valueObject in valueObjects: 
                        if (valueObject["_id"] == "valueObjects_0_NO_1_SI"):      
                            df.at[index, "valueObjects"] = valueObject["data"]
                            noticeUpdate(index, f"ValObj assegnazione di default")

            if(str(df.at[index, "valueObjects"]) == "nan" or str(df.at[index, "valueObjects"]) == "" or df.at[index, "valueObjects"] == None):                    
                if(df.at[index, "Notice"] != None and "Missing: ValueObject!" in str(df.at[index, "Notice"])):
                    for valueObject in valueObjects: 
                        if (valueObject["_id"] == "valueObjects_0_NO_1_SI"):      
                            df.at[index, "valueObjects"] = valueObject["data"]
                            noticeUpdate(index, f"ValObj assegnazione di default_2") 
        
        Elaborazione()   
    
    
    def fillOldData(df):
        for index, row in df.iterrows():  
            if not pd.isna(row["NewProfileName"]):
                df.at[index, "profileName"] = str(row["NewProfileName"]).strip()
            if not pd.isna(row["NewSignalName"]):
                df.at[index, "signalName"] = str(row["NewSignalName"]).strip()
            if not pd.isna(row["NewSignalDescription"]):
                df.at[index, "signalDescription"] = str(row["NewSignalDescription"]).strip()
            if not pd.isna(row["NewDataValueType"]):
                df.at[index, "valueType"] = str(row["NewDataValueType"]).strip()
            if not pd.isna(row["NewUOM"]):
                df.at[index, "uom"] = str(row["NewUOM"])
            if not pd.isna(row["NewLogica"]):
                df.at[index, "Logica (0/1)"] = str(row["NewLogica"]).replace(".0","")
            if not pd.isna(row["NewAlarmClass"]):
                df.at[index, "alarmClass"] = str(row["NewAlarmClass"]).strip()
            if not pd.isna(row["NewAlarmDescription"]):
                df.at[index, "alarmDescription"] =  str(row["NewAlarmDescription"]).strip()
                
    yield "> Elaborazione vecchio formato..."
    for innerYield in ElaboraDati_OLD_Format(df):
        yield innerYield
        
    global dfOld    
    if(isinstance(dfOld, type(None)) or len(dfOld.index) == 0):                
        yield ("Errore! ")
        return
    
    yield "> Elaborazione nuovo formato..."
    for innerYield in ElaboraDati_NEW_Format(dfOld):
        yield innerYield
    
    
    if(links):
        yield {"links": links}
        links = []
        
    else:
        yield "Errore nella generazione dei link!"


def normalizeString(inStr):    
    """Data una stringa in input, ritorna la contraparte normalizata."""
    return str(normalizzatore.normalizzaDati(inStr, dictionary, aliasArray = indexedAliasArray, splitRule = splitRule))
    
    
if __name__ == "__main__":
    CpuCoreNumber = 0
    UploadsFileFolder = r'C:\Utente\Downloads' #project_root + sharedCode.loadSettings("paths", "uploadsFolder") 
    DownloadsFileFolder = project_root + sharedCode.loadSettings("paths", "downloadsFolder")
    
    #fileName = "Device_Profile_10.10.2024_10.54.xlsx"
    
    fileName = "elaborazione_PREPO.xlsx"
    prefix  = "_test_profiles_old_"
    for output in mainCall(CpuCoreNumber, UploadsFileFolder, DownloadsFileFolder, fileName, prefix, None, yieldFlag = True):
        print(f"{output}")
