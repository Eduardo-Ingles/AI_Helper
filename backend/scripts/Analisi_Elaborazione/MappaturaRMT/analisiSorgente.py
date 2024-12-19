from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from multiprocessing import Manager
import traceback 

import copy
#from collections import OrderedDict
#from datetime import datetime
import pandas as pd
import time, json

import os, sys

#import numpy as np
#from llama_cpp import Llama
#from sentence_transformers import SentenceTransformer
#from transformers import AutoTokenizer
#import requests
#import hashlib

#from sklearn.feature_extraction.text import TfidfVectorizer
#from sklearn.metrics.pairwise import cosine_similarity

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, normalizzatore, applyRules, rulesDefiner

# ----------------------------------- START COSTANTI -----------------------------------#  

dataArrayForTags = [{"collection": "ALR_Collection AlrType_Collection", "tag":"ALR"},
                    {"collection": "CMD_Collection", "tag": "CMD"},
                    {"collection": "ST_Collection Status_Collection", "tag": "ST"},
                    {"collection": "MIS_Collection MeasureTypes_Collection", "tag": "MIS"},
                    {"collection": "PAR_Collection ParType_Collection", "tag": "PAR"}]

SheetsName = ["WIP", "Import"]

dataTypeDict = sharedCode.loadSettings("globalSettings", "dataType") 
registerTypeDict = sharedCode.loadSettings("globalSettings", "registerTypes") 
dictFolder = sharedCode.loadSettings("paths", "dictFolder") 
dictFileName = sharedCode.loadSettings("files", "dizionarioMain")

splitRule = sharedCode.loadSettings("globalSettings", "splitRule")

rulesPath = sharedCode.loadSettings("paths", "rulesFolder")
rawRulesFile =  sharedCode.loadSettings("files", "sigRulesRaw")
newRulesFile =  sharedCode.loadSettings("files", "sigRules")

importColumns = sharedCode.loadSettings("globalSettings", "colonneImport")

colonneInput = sharedCode.loadSettings("analisiSorgenteSettings", "colonneIN")
filePrefix = sharedCode.loadSettings("analisiSorgenteSettings", "filePrefix")
fileSuffix = sharedCode.loadSettings("analisiSorgenteSettings", "fileSuffix")

dictionary = (sharedCode.rw_file(path = dictFolder, file = dictFileName))
indexedAliasArray = normalizzatore.aliasIndexArray(dictionary)

#rulesDefiner.creaNuovoFormato(rulesPath, rawRulesFile, newRulesFile)
currRules = rulesDefiner.loadRulesData(rulesPath, rawRulesFile, newRulesFile)

yieldFlag = None
errorsList = []
# ----------------------------------- END COSTANTI -----------------------------------# 

def mainCall(files:list, uploadPath:str, downloadPath:str, CPUCores:int, **kwargs):
    global yieldFlag
    links = []
    yieldFlag = kwargs.get("yieldFlag", None)    
    fileAnagrafica = None
    fileSorgente = None
    yield f"Elaborazione di {files}..."
    if(len(files) == 1):
        fileSorgente = files[0]
    else:
        for file in files:
            if("anagraf" in file):
                fileAnagrafica = file
            else:
                fileSorgente = file
                
    if(not fileSorgente):
        yield "Sorgente non trovata!"
    
    def multyCoreProcessing(df, dfA):
        try:            
            if(checkColumns(df)):
                chunks = sharedCode.defineChunkSize(CPUCores, len(df))
                #print(chunks)
                #rawRows = df.apply(lambda row: json.dumps({col: str(row[col]) for col in df.columns if col.startswith("raw")}), axis=1).tolist()
                #rawRows = df.apply(lambda row: json.dumps({col: sharedCode.camelCaseSplit(str(row[col])) for col in df.columns}), axis=1).tolist()
                rawRows = df.apply(lambda row: json.dumps({col: str(row[col]) for col in df.columns}), axis=1).tolist()

                with Manager() as manager:            
                    shared_data = manager.dict()
                    shared_data["sharedData"] = manager.list()
                    shared_data['dataHolder'] = manager.list()
                    shared_data["cpuCounter"] = 0
                    shared_data["toDo"] = 0

                    for row in rawRows:
                        tempData = json.loads(row)
                        for key, value in tempData.items():
                            if(value == "nan"):
                                tempData[key] = ""
                        shared_data["sharedData"].append(tempData)

                    msg = (f"Inizio elaborazione...{chunks}")     
                    yield msg if yieldFlag else print(msg)
                    
                    yield sharedCode.progressYield(0.01, 100) if yieldFlag else print()
                    with multiprocessing.Pool(processes = CPUCores) as pool:
                        resultsElab = pool.starmap(
                            elaboraChunk,
                            [
                                (CPUCores, start, end, shared_data)
                                for start, end in chunks
                            ],
                        )                
                    
                    msg = ("\nUnione df....")     
                    yield msg if yieldFlag else print(msg)  
                    processed_dfs = [pd.concat(result) for result in resultsElab]
                    df = pd.concat(processed_dfs)
                                           
                    msg = (f"\n{df.columns}\n")
                    yield msg if yieldFlag else print(msg)  
                                       
                    msg = ("Riempimento colonne...") 
                    yield msg if yieldFlag else print(msg)   
                    df2 = sharedCode.fillImportColumns(df, "df2", "WIP", importColumns)
                    #df.drop(columns = importColumns, inplace=True)
                    dfs = {"WIP": df, "Import": df2}
                    outFileName = f"{filePrefix}{fileSorgente}"
                    if(not outFileName.endswith(".xlsx")):
                        outFileName += ".xlsx"
                    msg = (f"Salvataggio: {sharedCode.rw_xlsx(path = downloadPath, file = outFileName, df = dfs)}") 
                    yield msg if yieldFlag else print(msg) 
                    tlink = {"link": f"{downloadPath}{outFileName}", "linkName": outFileName}
                    links.append(tlink) if tlink not in links else next
                    if(links):
                        yield {"links": links}                        
                    yield sharedCode.progressYield(100, 100) if yieldFlag else print()
            else:
                msg = (f"Impossile elaborare!\nColonnne essenziali mancanti !!!")
                yield msg if yieldFlag else print(msg) 
        except Exception as e:
            emsg = (f"An error occurred: {str(e)}:")            
            print(emsg)
            errorsList.append(emsg) if emsg not in errorsList else next
            yield msg if yieldFlag else print(emsg) 
            traceback.print_exc()

            
    sharedCode.currentTimeHMS("start")
    dfA = None
    skip = False
    rowsAn = None   
    if(fileAnagrafica and fileAnagrafica != "" and skip == False): # 
        includedColumns = ["Nome Galleria", "Impianto", "NormalizedPlant", "Tipologia Dispositivo", "NormalizedType", "Nome dispositivo", "Locale tecnico", "Corsia", "Direzione", "NormalizedData"]

        msg = (f"Preparazione anagrafica: {fileAnagrafica}...")
        yield msg if yieldFlag else print(msg)
        
        dfA = sharedCode.rw_xlsx(path = uploadPath, file = fileAnagrafica, sheet = "Dispositivi")
        dfA["NormalizedData"] = None
        dfA["NormalizedPlant"] = None
        dfA["NormalizedType"] = None
        dfA = dfA[includedColumns]
        
        msg = (f"Normalizzazione dati {fileAnagrafica}...")
        yield msg if yieldFlag else print(msg)
        
        for index, row in dfA.iterrows():
            tempNormData = str(normalizzatore.normalizzaDati(str(row["Nome dispositivo"]), dictionary, splitRule=splitRule, aliasArray=indexedAliasArray)) + f"{" ".join(list(set(str(row["Nome dispositivo"]).replace(str(row["Nome Galleria"]).upper(),"").split("-"))))}"
            dfA.loc[index, "NormalizedData"] = " ".join(list(set(str(tempNormData).strip().split())))
            
            tempPlantNorm = str(normalizzatore.normalizzaDati(str(row["Impianto"]), dictionary, splitRule=splitRule, aliasArray=indexedAliasArray)).strip()
            dfA.loc[index, "NormalizedPlant"] = " ".join(list(set(str(tempPlantNorm).replace("PLANT","").strip().split())))
            
            tempPlantNorm = (str(normalizzatore.normalizzaDati(str(row["Tipologia Dispositivo"]), dictionary, splitRule=splitRule, aliasArray=indexedAliasArray))).strip()
            if(tempPlantNorm == ""):
                tempPlantNorm = normalizzatore.paroleNonCensite(f"{str(row["Tipologia Dispositivo"])}", indexedAliasArray)
            dfA.loc[index, "NormalizedType"] = tempPlantNorm

            sharedCode.progress(index, len(dfA))

        dfA = dfA[["Impianto", "NormalizedPlant", "Tipologia Dispositivo", "NormalizedType", "Nome dispositivo", "NormalizedData"]]
        # Converting each row to JSON format using apply and filtering by includedColumns
        rowsAn = dfA.apply(lambda row: json.dumps(
            {col: str(row[col]) for col in includedColumns if col in dfA.columns}), axis=1).tolist()
        #print(f"{dfA.head()}\n {dfA.columns}")
        #fileAnagrafica = fileAnagrafica+".xlsx" if not fileAnagrafica.endswith(".xlsx") else fileAnagrafica

    df = sharedCode.rw_xlsx(path = uploadPath, file = fileSorgente)

    for output in multyCoreProcessing(df, dfA):
        yield output
    #srcStr = "SEMAF"
    #for rdata in rowsAn:
    #    tempData = json.loads(rdata)
    #    if(srcStr in tempData["NormalizedType"]):
    #        if(sharedCode.any_AinB(srcStr, tempData["NormalizedData"])):
    #            print(f"{tempData}")

            #print(f"{tempData["NormalizedData"]} -> {sharedCode.most_matches(tempData["NormalizedData"], "VENT# 8 SX")}")


def checkColumns(df):
    msg = ("\nCheck colonne...")
    yield msg if yieldFlag else print(msg) 
    
    colonneRif = sharedCode.loadSettings("analisiSorgenteSettings", "colonneIN")
    EssentialColumnsFlag = True
    currentDfColumns = []
    for colonna in colonneRif:
        if not colonna in df.columns:
            print(f"Colonna {colonna} non trovata!")
    for colonna in df.columns:
        currentDfColumns.append(colonna) if colonna not in currentDfColumns else next
    if(("rawAddress" not in currentDfColumns or ("rawRegister" not in currentDfColumns and "rawBitIndex" not in currentDfColumns))            
           and sharedCode.notAny_AinB(["rawSegnale", "rawDescrizione", "rawDescr&Signal"], currentDfColumns)):
        EssentialColumnsFlag = False
        print(df.columns)
    df.dropna(axis = 1, how = 'all', inplace = True)
    newColumns = sharedCode.loadSettings("analisiSorgenteSettings", "colonneElaborazione")
    for newColonna in newColumns:        
        df[newColonna] = None
    newColumns = sharedCode.loadSettings("globalSettings", "colonneImportSegnali")
    for newColonna in newColumns:        
        df[newColonna] = None
    return EssentialColumnsFlag


def elaboraChunk(CPUCore, start_index, end_index, shared_data):
    """
        shared_data["sharedData"] -->
        - rawRegister, rawBitIndex, rawAddress, rawRegisterType, rawDataType, rawDispositivo, rawSegnale, rawDescrizione,  rawDescr&Signal, rawLogica, rawTags, rawQuadro, rawCabina, rawDirezione, rawReference, rawIpPlc
        - newSubplant, NewAddress, NewRegisterType, NewDataValueType, NewTag, Escludi Profili, NewProfileName, NewDevice, NewSignalName, NewSignalDescription, NewAlarmClass, NewAlarmDescription, NewUOM, NewLogica, NewCabina, NewDirezione, NormalizedData, LeftOvers, LogicLeftOvers, <Used Functions>, Notice, newRegister, newBitIndex, extractedIds
    """
    def addressCheck(sharedData):
        """
        Estrae l'indirizzo (registro + bit)
        """
        rawAddress = str(sharedData.get("rawAddress")) if sharedData.get("rawAddress") and (sharedData.get("rawAddress")) != "None" else None
        rawRegister = str(sharedData.get("rawRegister")) if sharedData.get("rawRegister") and (sharedData.get("rawRegister")) != "None" else None
        rawBitIndex = str(sharedData.get("rawBitIndex")) if sharedData.get("rawBitIndex") and (sharedData.get("rawBitIndex")) != "None" else None
        rwaDataType = str(sharedData.get("rawDataType")) if sharedData.get("rawDataType") and (sharedData.get("rawDataType")) != "None" else None
        #rawRegisterType = str(sharedData.get("rawRegisterType")) if sharedData.get("rawRegisterType") and (sharedData.get("rawRegisterType")) != "None" else None

        
        tempDataType = sharedCode.fill_DataType(rwaDataType, dataTypeDict) if rwaDataType else ""
        newAddress = {"register": None, "bit": None, "dataType": tempDataType}


        if(rawAddress and not (rawRegister and rawBitIndex)):   # se esiste la colonna con 'registro' + 'bit' assieme es. '%MW800.1'
            checkReg = ''.join(c for c in str(rawAddress) if c.isdigit())
            if(checkReg.isdigit()):
                if("." in rawAddress or "," in rawAddress):
                    rawAddress = rawAddress.replace(",",".")
                    newAddress["register"] = f"{rawAddress.split(".")[0]}"
                    newAddress["bit"] = f"{rawAddress.split(".")[1]}"
                    newAddress["dataType"] = "BOOL" if not rwaDataType else tempDataType
                else:
                    newAddress["register"] = f"{rawAddress}"
                    newAddress["bit"] = f"0"
                    newAddress["dataType"] = "INT" if not rwaDataType else tempDataType
                return newAddress
        
        elif(not rawAddress and rawRegister): # se 'registro' e 'bit' sono in colonne separate
            checkReg = ''.join(c for c in str(rawRegister) if c.isdigit())
            if(checkReg.isdigit()):
                if(rawBitIndex):#and rawBitIndex != "" or rawBitIndex != "None"):
                    newAddress["register"] = ''.join(c for c in str(rawRegister) if c.isdigit())
                    newAddress["bit"] = f"{rawBitIndex}"
                    newAddress["dataType"] = "BOOL" if not rwaDataType else tempDataType
                else:
                    newAddress["register"] = ''.join(c for c in str(rawRegister) if c.isdigit())
                    newAddress["bit"] = str(0)
                    newAddress["dataType"] = "INT" if not rwaDataType else tempDataType

                return newAddress
        else:
            return None


    def directionExtraction(sharedData):
        """
        Estrae le possibili direzioni
        """
        direzioni = []
        # indLocPos_Collection -> DIR_Collection / POS_Collection / CardinalPos_Collection / SX&DX_Collection
        rawDescr = sharedData.get("rawDescrizione") if sharedData.get("rawDescrizione") else None
        rawDir = sharedData.get("rawDirezione") if sharedData.get("rawDirezione") else None
        tempDir = normalizzatore.normalizeByType("SX&DX_Collection INTERN&EXTERN_Collection CardinalPos_Collection CORS_POS_Collection", f"{str(rawDir)} {str(rawDescr)}", dictionary) if rawQuadro else None
        #return " ".join(sharedCode.extractBracketText(rawDescr,"any"))
        direzioni.append(tempDir) if tempDir and tempDir != "" else next
        return direzioni


    def quadroExtraction(sharedData):
        """
        Estrae i possibili quadri
        """
        rawSignal = sharedData.get("rawSegnale") if sharedData.get("rawSegnale") else ""
        rawDescr = sharedData.get("rawDescrizione") if sharedData.get("rawDescrizione") else ""
        rawSignalDescr = sharedData.get("rawDescr&Signal") if sharedData.get("rawDescr&Signal") else "" 
        rawDevice = sharedData.get("rawDispositivo") if sharedData.get("rawDispositivo") else ""
        rawCabina = sharedData.get("rawCabina") if sharedData.get("rawCabina") else ""        
        
        dictQuadro = {"quadro": None, "quadri": []}

        rawQuadro = sharedData.get("rawQuadro") if sharedData.get("rawQuadro") else None

        tempQuadro = normalizzatore.normalizeByType("miscQuadri_Collection", str(rawQuadro), dictionary).replace("QUADR","") if rawQuadro else None
        dictQuadro["quadro"] = tempQuadro if tempQuadro and tempQuadro != "" and tempQuadro not in dictQuadro["quadri"] else None

        dataSet = sharedCode.camelCaseSplit(f"{rawSignal} {rawDescr} {rawSignalDescr} {rawDevice} {rawCabina}", selfReturn = True)
        tempQuadri = normalizzatore.normalizeByType("miscQuadri_Collection", dataSet, dictionary).replace("QUADR","") if rawQuadro else None
        dictQuadro["quadri"].append(tempQuadri) if tempQuadri and tempQuadri != "" and tempQuadri not in dictQuadro["quadri"] else next
        #dictQuadro["quadri"].append(tempQuadro) if tempQuadro and tempQuadro != "" and tempQuadro not in dictQuadro["quadri"] else next
        #print(f"{tempQuadri} --> {dataSet}")
        return dictQuadro


    def cabinaExtraction(sharedData):
        """
        Estrae le possibili cabine 
        """        
        cabina = {"cabina": None, "cabine": None}
        
        rawSignal = sharedData.get("rawSegnale") if sharedData.get("rawSegnale") else ""
        rawDescr = sharedData.get("rawDescrizione") if sharedData.get("rawDescrizione") else ""
        rawSignalDescr = sharedData.get("rawDescr&Signal") if sharedData.get("rawDescr&Signal") else "" 
        rawDevice = sharedData.get("rawDispositivo") if sharedData.get("rawDispositivo") else ""
        rawQuadro = sharedData.get("rawQuadro") if sharedData.get("rawQuadro") else ""
        rawCabina = sharedData.get("rawCabina") if sharedData.get("rawCabina") else None

        if(rawCabina):
            cabina["cabina"] = normalizzatore.normalizeByType(["CAB_Collection"], str(rawCabina), dictionary) 
            if(cabina["cabina"] == ""):
                cabina["cabina"] = None
        
        dataSet = f"{rawSignal} {rawDescr} {rawSignalDescr} {rawDevice} {rawQuadro}"
        cabina["cabine"] = normalizzatore.normalizeByType(["CAB_Collection"], (dataSet), dictionary) 
        if(cabina["cabine"] == ""):
            cabina["cabine"] = None

        return cabina


    def deviceExtraction(sharedData, **kwargs):
        """
        Estrae possibili devices
        """
        devices = []
        device = ""
        rawSignal = sharedData.get("rawSegnale") if sharedData.get("rawSegnale") else ""
        rawDescr = sharedData.get("rawDescrizione") if sharedData.get("rawDescrizione") else ""
        rawSignalDescr = sharedData.get("rawDescr&Signal") if sharedData.get("rawDescr&Signal") else "" 
        rawDevice = sharedData.get("rawDispositivo") if sharedData.get("rawDispositivo") else ""
        rawQuadro = sharedData.get("rawQuadro") if sharedData.get("rawQuadro") else ""

        rawReference = sharedData.get("rawReference") if sharedData.get("rawReference") else ""        

        if(rawDevice != ""):
            device = normalizzatore.normalizeByType(["Device_Collection", "miscItems_Collection"], str(rawDevice), dictionary) if rawDevice != "" else None
        else:
            dataSet = (f"{rawSignal} {rawDescr} {rawSignalDescr}").strip()
            dataSet = normalizzatore.normalizeByType(["Device_Collection", "miscItems_Collection"], dataSet, dictionary) if rawSignal != "" or rawDescr != ""  or rawSignalDescr != "" else None

        dataSetAll = (f"{rawSignal} {rawDescr} {rawSignalDescr} {rawQuadro}").strip()
        tempDevice = normalizzatore.normalizeByType(["Device_Collection", "miscItems_Collection"], str(dataSetAll), dictionary) if rawSignal != "" or rawDescr != ""  or rawSignalDescr != "" else None
        devices.append(str(tempDevice)) if tempDevice and str(tempDevice) != "" and str(tempDevice) not in devices else next
        
        if(len(devices) == 0):
            tempDevice = normalizzatore.normalizeByType(["Device_Collection", "miscItems_Collection"], str(rawReference), dictionary) if rawReference != "" else None
            #device = str(tempDevice) if tempDevice and str(tempDevice) != "" else next
            devices.append(str(tempDevice)) if tempDevice and str(tempDevice) != "" and str(tempDevice) not in devices else next

        deviceDicty = {"device": device, "devices": devices}
        return deviceDicty


    def registerTypeExtraction(sharedData):
        rwaRegisterType = sharedData.get("rawRegisterType", None)
        filledData = sharedCode.fill_DataType(str(rwaRegisterType), registerTypeDict)
        return filledData
    

    def tagExtraction(sharedData):
        """
        Estrae i possibili 'tag' se la colonna 'rawTags' esiste, altrimenti cerca di estrare dal resto delle colonne (possibili valori multipli / in conflitto)
        """
        rawSignal = (sharedData.get("rawSegnale")) if sharedData.get("rawSegnale") else ""
        rawDescr = (sharedData.get("rawDescrizione")) if sharedData.get("rawDescrizione") else ""
        rawSignalDescr = (sharedData.get("rawDescr&Signal")) if sharedData.get("rawDescr&Signal") else "" 
        rawDevice = (sharedData.get("rawDispositivo")) if sharedData.get("rawDispositivo") else ""
        rawLogic = (sharedData.get("rawLogica")) if sharedData.get("rawLogica") else ""
        rawQuadro = sharedData.get("rawQuadro") if sharedData.get("rawQuadro") else ""
        rawTag = (sharedData.get("rawTags")) if sharedData.get("rawTags") else None 

        tagArray = []
        dataSet = sharedCode.camelCaseSplit(f"{rawSignal} {rawDescr} {rawSignalDescr} {rawDevice} {rawLogic}", selfReturn = True)
        tempTag = normalizzatore.normalizeByType("TAG_Collection", str(rawTag), dictionary) if rawTag else None
        if(not tempTag):
            tempTag = normalizzatore.normalizeByType("TAG_Collection", dataSet, dictionary) 
            if (tempTag and tempTag == ""):
                tempTag = None

        for dataTag in dataArrayForTags:
            tempTagData = normalizzatore.normalizeByType(dataTag["collection"], dataSet, dictionary)
            if(tempTagData and tempTagData != ""):
                tagArray.append(dataTag["tag"]) if dataTag["tag"] not in tagArray else next
        
        if(len(tagArray) == 0):
            tagArray = None
        else:
            tagArray.append(tempTag) if (tempTag and tempTag != "") and tempTag not in tagArray else next

        tagDicty = {"tag": tempTag, "tags": tagArray}
        return tagDicty


    def logicExtraction(sharedData):
        """
        Estrae la logica dalla colonna 'rawLogica' se esiste altrimenti cerca nella descrizione
        """
        rawDescr = sharedData.get("rawDescrizione") if sharedData.get("rawDescrizione") else None
        rawLogic = sharedData.get("rawLogica") if sharedData.get("rawLogica") else ""
        if(rawLogic and rawLogic != ""):
            normLogic = normalizzatore.normalizzaDati(rawLogic, dictionary, aliasArray = indexedAliasArray)
            return normLogic if normLogic and normLogic != "" else rawLogic
        elif(not rawLogic and rawDescr):
            return " ".join(sharedCode.extractBracketText(rawDescr,"any")).strip()
        else:
            return ""


    try: 
        currentCore = copy.copy(shared_data["cpuCounter"])
        shared_data["cpuCounter"] += 1
        shared_data["toDo"] += 1

        df = pd.DataFrame(dtype=str) 

        for index, sharedData in enumerate(shared_data["sharedData"][start_index:end_index]):
            newAddressData = addressCheck(sharedData)

            #rawAddress = sharedData.get("rawAddress") if sharedData.get("rawAddress") else None
            #rawRegister = sharedData.get("rawRegister") if sharedData.get("rawRegister") else None
            #rawBitIndex = sharedData.get("rawBitIndex") if sharedData.get("rawBitIndex") else None
            #rwaRegisterType = sharedData.get("rawRegisterType") if sharedData.get("rawRegisterType") else None

            rawDevice = sharedData.get("rawDispositivo") if sharedData.get("rawDispositivo") else ""
            rawSignal = (sharedData.get("rawSegnale")) if sharedData.get("rawSegnale") else ""
            rawDescr = (sharedData.get("rawDescrizione")) if sharedData.get("rawDescrizione") else ""
            rawSigDescr = (sharedData.get("rawDescr&Signal")) if sharedData.get("rawDescr&Signal") else ""

            #rawTag = sharedData.get("rawTags") if sharedData.get("rawTags") else ""
            rawQuadro = sharedData.get("rawQuadro") if sharedData.get("rawQuadro") else ""
            rawCabina = sharedData.get("rawCabina") if sharedData.get("rawCabina") else ""
            #rawDir = sharedData.get("rawDirezione") if sharedData.get("rawDirezione") else None

            rawReference = sharedData.get("rawReference") if sharedData.get("rawReference") else None
            rawPlcIp = sharedData.get("rawIpPlc") if sharedData.get("rawIpPlc") else None

            rawIds = sharedData.get("rawIDs") if sharedData.get("rawIDs") else ""

            dirList = directionExtraction(sharedData)
            quadroList = quadroExtraction(sharedData)
            cabinaList = cabinaExtraction(sharedData)
            deviceListDict = deviceExtraction(sharedData) # ["device"] / ["devices"]
            tagListDict = tagExtraction(sharedData) # ["tag"] / ["tags"]
            logicList = logicExtraction(sharedData) # modificare return type e adeguare codice sottostante
            #print(tagListDict)

            
            tempQuadro = (quadroList["quadro"]).strip() if quadroList["quadro"]  else "-".join(quadroList["quadri"]) if quadroList["quadri"] else ""#" ".join(quadroList) if quadroList else ""#normalizzatore.normalizeByType("miscQuadri_Collection", str(rawQuadro), dictionary) if rawQuadro else None
            tempTag = str(tagListDict["tag"]).strip() if tagListDict["tag"]  else " ".join(tagListDict["tags"]) if tagListDict["tags"] else ""#normalizzatore.normalizzaDati(str(rawTag), dictionary, aliasArray = indexedAliasArray) if rawTag else None

            #tempDataSetAll = ""
            tempExtractedId = (sharedCode.extract_id(rawIds, splitRule) if rawIds else "") + (f" {sharedCode.camelCaseSplit(f"{rawIds}", selfReturn = True)}" if rawIds else "")
            tempDevice = deviceListDict["device"] if deviceListDict["device"] else (" ".join(deviceListDict["devices"])) if len(deviceListDict["devices"]) != 0 else ""
            tempProfile = ""
            #tempSignal = normalizzatore.normalizzaDati(rawDescr.replace(logicList, "").replace(str(tempQuadro),""), dictionary, aliasArray = indexedAliasArray)
            #tempSignalDesciption = ""#"tempSignalDesciption"
            tempAlrClass = ""
            tempAlrClassDescription = ""

            dataSet = sharedCode.camelCaseSplit(f"{rawDevice} {rawSignal} {rawDescr} {rawSigDescr} {rawQuadro} {rawCabina} {tempDevice}", selfReturn = True)
            tempNormalizedData = normalizzatore.normalizzaDati(f"{tempTag} {dataSet}", dictionary, aliasArray = indexedAliasArray)
            tempLeftOvers = normalizzatore.paroleNonCensite(f"{dataSet}", indexedAliasArray)
            if(tempExtractedId and tempLeftOvers):
                tempLeftOvers = tempLeftOvers.replace(tempExtractedId, "")

            tempCabina = (cabinaList["cabina"]).strip() if cabinaList["cabina"]  else cabinaList["cabine"].strip() if cabinaList["cabine"] else ""

            tempRegister = newAddressData.get("register", "") if newAddressData else ""
            tempBitIndex = newAddressData.get("bit", "") if newAddressData else ""
            tempValueType = newAddressData.get("dataType", "") if newAddressData else ""

            tempDirezione = (" ".join(dirList)) if dirList and len(dirList) != 0 else ""
            tempUom = ""

            test = applyRules.applyRules(currRules, normalizzatore.normalizzaDati(f"{tempTag} " + rawDescr.replace(logicList,"").replace(str(tempQuadro),""), dictionary, aliasArray = indexedAliasArray), dictionary, indexedAliasArray, device = tempDevice)
            usedFunctions = sharedCode.noticeUpdate(None, "Test 1a") if test else None
            #normLogic = normalizzatore.normalizzaDati(logicList, dictionary, aliasArray = indexedAliasArray)
            if (not test or "signal" not in test or test["signal"] == ""):                
                test = applyRules.applyRules(currRules, normalizzatore.normalizzaDati(f"{tempTag} " + rawDescr.replace(logicList,"").replace(str(tempQuadro),""), dictionary, aliasArray = indexedAliasArray), dictionary, indexedAliasArray, device = tempDevice)
                usedFunctions = sharedCode.noticeUpdate(None, "Test 1b") if test else None

                if (not test or "signal" not in test or test["signal"] == ""):
                    test = applyRules.applyRules(currRules, (f"{tempTag} {tempNormalizedData}").split(), dictionary, indexedAliasArray, device = tempDevice)
                    usedFunctions = sharedCode.noticeUpdate(usedFunctions, "Test 2a") if test else None

                    if (not test or "signal" not in test or test["signal"] == ""):
                        test = applyRules.applyRules(currRules, (f"{tempTag} {tempNormalizedData}").split(), dictionary, indexedAliasArray)
                        usedFunctions = sharedCode.noticeUpdate(usedFunctions, "Test 2b") if test else None

                        if (not test or "signal" not in test or test["signal"] == ""):
                            test = applyRules.applyRules(currRules, f"{tempTag} {tempNormalizedData} {tempDevice}", dictionary, indexedAliasArray, device = tempDevice)
                            usedFunctions = sharedCode.noticeUpdate(usedFunctions, "Test 3a") if test else None

                            if (not test or "signal" not in test or test["signal"] == ""):
                                test = applyRules.applyRules(currRules, f"{tempTag} {tempNormalizedData} {tempDevice}", dictionary, indexedAliasArray)
                                usedFunctions = sharedCode.noticeUpdate(usedFunctions, "Test 3b") if test else None
            

            if(tempLeftOvers and tempLeftOvers != ""):
                for probQuadro in tempLeftOvers.split():
                    if(probQuadro.upper().startswith("Q")):
                        tempQuadro += f"{probQuadro} "
            if(tempQuadro and tempQuadro != ""):
                tempQuadro = tempQuadro.strip()
            
            if not tempExtractedId:
                tempExtractedId = rawIds.strip().replace(" ", "-")

            if(not tempExtractedId or tempExtractedId == "" and rawReference):
                tempExtractedId = normalizzatore.normalizzaDati(f"{rawReference}", dictionary, aliasArray = indexedAliasArray)
            
            if(not tempExtractedId or (tempExtractedId and tempExtractedId == "")):
                tempExtractedId = ""               

            newDevice = (normalizzatore.normalizzaDati(f"{tempQuadro} {tempDevice} {sharedCode.camelCaseSplit(tempExtractedId, selfReturn = True)}", dictionary, aliasArray = indexedAliasArray, dataType = "LIST")) #(f"{tempQuadro} {tempDevice} {tempExtractedId}")#.strip().replace(" ","-").upper()
            newDevice += (normalizzatore.paroleNonCensite(f"{dataSet}", indexedAliasArray, dataType = "LIST"))
            newDevice = "-".join(newDevice)
            if(tempCabina):
                newDevice += f"-{tempCabina}"
                
            # clean device:
            newDevice = newDevice.replace("NONE","").replace("--","-")
            tempDict = {
                "NewRegisterType": registerTypeExtraction(sharedData),
                "NewDataValueType": tempValueType,
                "NewTag": tempTag,
                "Escludi Profili": None,
                "NewProfileName": (f"{tempQuadro} {tempDevice} {tempCabina}").strip().replace(" ","-").upper(),
                "NewDevice": newDevice,
                "NewSignalName": test["signal"] if test else "",#tempSignal,
                "NewSignalDescription": test["descr"] if test else "",#tempSignalDesciption, 
                "NewAlarmClass": tempAlrClass,  
                "NewAlarmDescription": tempAlrClassDescription,
                "NewLogica": logicList,
                "NewAddress": f"{tempRegister}.{tempBitIndex}",
                "newRegister": tempRegister,
                "newBitIndex": tempBitIndex,
                "NewUOM": tempUom,
                "newSubplant": None,
                "NewCabina": tempCabina,
                "NewQuadro": tempQuadro,
                "NewDirezione": tempDirezione, 
                "NormalizedData": tempNormalizedData,
                "LeftOvers": tempLeftOvers,
                "extractedIds": tempExtractedId,
                "<Used Functions>": usedFunctions,
                "Notice": None
                }
            
            sharedData.update(tempDict)
            """Salva dati in df"""
            for key, value in sharedData.items():
                df.loc[index, key] = str(value).strip() if value and str(value).upper() != "NONE" else ""

            #for key, value in tempDict.items():
            #    df.loc[index, key] = str(value)

        shared_data["toDo"] -= 1
        print(f"\tElaborato part 1:>\t start_index: {start_index} - end_index: {end_index}\t core: {currentCore}/{CPUCore - 1}\t ({shared_data["toDo"]})")
        return [df]
    except Exception as e:
        emsg = (f"An error occurred: {str(e)}:")
        print(emsg)
        errorsList.append(emsg) if emsg not in errorsList else next
        traceback.print_exc() 
    
    #rulesResult = applyRules.applyRules(currRules, tempNormData, dictionary, indexedAliasArray, device = normDevice)


if __name__ == "__main__":    
    import datetime
    x = datetime.datetime.now()
    timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")

    scriptFoldername = "Elaborazione sorgente RMT"

    UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder")+ f"{timeStamptFolder}\\"
    DownloadsFileFolder = f"{project_root + sharedCode.loadSettings("paths", "downloadsFolder")}{scriptFoldername}\\{timeStamptFolder}\\"

    #currFileFolder =  project_root + "\\scripts\\Analisi_Elaborazione\\MappaturaDragonfly\\File Elaborati\\"
    offsetCPU = 0#int(os.cpu_count()/2)
    CpuCoreNumber = os.cpu_count() - offsetCPU
    CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)
    
    fileAnagrafica = None#"xx-xxx-xx_Anagrafica Cuponeddi_2024-10-22_rev0_v1"#"xx-xxx-xx_Anagrafica San Giuliano_2024-08-26_rev1_v1"
    
    skipScriptExtraction = True
    auxName = "_elaborazione_"

    Sorgenti = ["Galleria San Giuliano e Casola_Esemplificativo Mappa PLC TO ELABORATE"]#"MODBUS TCPIP Rmt Plc Galleria Cuponeddi merged"]
    Sorgenti = ["Galleria San Giuliano e Casola_Esemplificativo Mappa PLC TO ELABORATE.xlsx"]
    for sorgente in Sorgenti:
        start = time.time()
        
        for output in mainCall([sorgente], UploadsFileFolder, DownloadsFileFolder, CpuCoreNumber):
            print (output)
        end = time.time()
        #minuti = int((end - start)/60)
        #secondi = int((end - start) - (minuti *60))
        #if(secondi < 10):
        #    secondi = "0" + str(secondi)
        #print("(total: {:.3f} s)".format(end - start), "({:.2f}) min".format((end - start)/60) )
        print(f"Tempo elaborazione: {sharedCode.elapsedTimeFormatted(start, end)}")
        #print("Tempo elaborazione: {:.2f} secondi\t-\t".format(end - start), f"{minuti}.{secondi} minuti")
        
