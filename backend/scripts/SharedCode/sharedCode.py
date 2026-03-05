from datetime import datetime
import os, sys
import re, json
import pandas as pd
import socket
import psutil

project_root = os.getcwd()

# ----------------------------------- START COSTANTI -----------------------------------#  

allowed_extensions = {'txt', 'csv', 'xlsx', "py"}

# ----------------------------------- END COSTANTI -----------------------------------# 


# MultyCore

def defineChunkSize(CpuCores:int, dataSetSize:int):
    """
    Calcola la dimensione dei dati da suddividere su tutti i core in maniera omogenea.
    """
    chunk_size = int(dataSetSize / CpuCores)
    remainder = dataSetSize % CpuCores
    chunks = []
    start_index = 0
    for i in range(CpuCores):
        end_index = start_index + chunk_size
        if i < remainder:   # Distribute the remainder across the first few chunks
            end_index += 1
        chunks.append((start_index, end_index))
        start_index = end_index
    return chunks


# TIME
def currentTimeHMS(prefix = ""):    
    """
    Funzione che ritorna il tempo corrente, prefix = testo (es. Start: / End:)
    """
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f"\nCurrent Time {prefix} = {current_time}")


def timeStamp(**kwargs):  
    """kwargs: 
    - fullDate = True per includere: anno - mese - giorno _ ora . minuti . secondi
    - dmy = True per includere: anno - mese - giorno
    default: ora . minuti . secondi
    """ 
    fullDate = kwargs.get("fullDate", None) 
    if(fullDate):
        return datetime.today().strftime('%Y-%m-%d_%H.%M.%S')
    elif("dmy"):# day - month - year
        return datetime.today().strftime('%Y-%m-%d')
    else:
        now = datetime.now()
        current_time = now.strftime("%H.%M.%S")
        return f"{current_time}".replace(":","-")
 

def get_current_time():
    """
    Ritorna il tempo attuale in secondi
    """
    current_time_ms = int(datetime.now().timestamp() * 1000)
    return current_time_ms

    
def elapsedTimeFormatted(startTime:int, endTime:int):  
    """Ritorna una strigna con il tempo passato da inizio a fine sia in secondi che in minuti."""  
    minuti = int((endTime - startTime)/60)
    secondi = int((endTime - startTime) - (minuti *60))
    if(secondi < 10):
        secondi = "0" + str(secondi)       
    return ("{:.2f} secondi - ".format(endTime - startTime) + f"{minuti}.{secondi} minuti")
        

# CONFRONTI
def any_AinB(varA, varB, **kwargs):
    """
    - ritorna TRUE se almento un elemento di A è presente in B.
    NB. se A o B sono vuoti ritorna TRUE
    \nkwargs: exclude = lista di parole da rimuovere da entrambe le liste prima del confronto
    """
    if not varA or not varB:
        return True
    if(isinstance(varA, str)):
        varA = varA.strip().lower().split()
    elif(isinstance(varA, list)):
        varA = (" ".join(varA)).strip().lower().split()
    if(isinstance(varB, str)):
        varB = varB.strip().lower().split()
    elif(isinstance(varB, list)):
        varB = (" ".join(varB)).strip().lower().split()

    exclude = kwargs.get("exclude", None)
    if(exclude):
        if(isinstance(exclude, str)):
            exclude = exclude.split()
            exclude.append("NONE")
        for word in exclude:
            varA.remove(word.lower()) if word.lower() in varA else next
            varB.remove(word.lower()) if word.lower() in varB else next

    if(any(element in varB for element in varA)):
        return True
    else:
        return False


def notAny_AinB(varA, varB, **kwargs):
    """
    Contrario di any_AinB, (non è stato utilizzato not any_AinB per ragioni non indicate)
    - ritorna FALSE se almento un elemento di A è presente in B.
    NB. se A o B sono vuoti ritorna TRUE
    \nkwargs: exclude = lista di parole da rimuovere da entrambe le liste prima del confronto
    """
    if not varA or not varB:
        return True
    if(isinstance(varA, str)):
        varA = varA.strip().lower().split()
    elif(isinstance(varA, list)):
        varA = (" ".join(varA)).strip().lower().split()
    if(isinstance(varB, str)):
        varB = varB.strip().lower().split()
    elif(isinstance(varB, list)):
        varB = (" ".join(varB)).strip().lower().split()
        
    exclude = kwargs.get("exclude", None)
    if(exclude):
        if(isinstance(exclude, str)):
            exclude = exclude.split()
            exclude.append("NONE")
        for word in exclude:
            varA.remove(word.lower()) if word.lower() in varA else next
            varB.remove(word.lower()) if word.lower() in varB else next

    if(any(element in varB for element in varA)):
        return False
    else:
        return True


def all_AinB(varA, varB, **kwargs):  
    """
    Cerca la presenza di TUTTI glu elementi di A in B: NB. se A o B sono vuoti ritorna TRUE
    \nkwargs: exclude -> lista di parole da rimuovere da entrambe le liste prima del confronto, es: ALR, NaN
    """
    if(not varA or not varB):
        return True  
    if(isinstance(varA, str)):
        varA = varA.strip().lower().split()
    elif(isinstance(varA, list)):
        varA = (" ".join(varA)).strip().lower().split()
    if(isinstance(varB, str)):
        varB = varB.strip().lower().split()
    elif(isinstance(varB, list)):
        varB = (" ".join(varB)).strip().lower().split()

    exclude = kwargs.get("exclude", None)
    if(exclude):
        if(isinstance(exclude, str)):
            exclude = exclude.split()
            exclude.append("NONE")
        for word in exclude:
            varA.remove(word.lower()) if word.lower() in varA else next
            varB.remove(word.lower()) if word.lower() in varB else next

    if(varA and all(element in varB for element in varA)): 
        return True
    else:
        return False
    

def condizioneComplessa(condSI, condOR, condNO, dati):
    """Utilizzati da profilator(OLD)"""
    if((all_AinB(condSI, dati) == True and any_AinB(condOR, dati) == True) and any_AinB(condNO, dati) == False):
        return True
    else:
        return False
    

def compareLists(listA, listB):
    """
    Confronta due liste e ritorna:
    - [0] elementi comuni tra A e B
    - [1] elemeni unnivoci ad A
    - [2] elemeni unnivoci a B
    - (se A o B sono stringhe, si effettua uno split() )
    """
    # Convert lists to sets
    if(isinstance(listA, str)):
        listA = listA.strip().split()
    if(isinstance(listB, str)):
        listB = listB.strip().split()
    set1 = set(listA)
    set2 = set(listB)
    # Find intersection (elements that are the same)
    common_elements = set1.intersection(set2)
    # Find differences (elements that are not the same)
    unique_to_str1 = set1.difference(set2)
    unique_to_str2 = set2.difference(set1)
    return list(common_elements), list(unique_to_str1), list(unique_to_str2)


def most_matches(inputA, inputList:list):
    """
    Funzione che cerca gli elementi comuni (con più match) all'interno di una lista
    """
    def count_common_elements(list1, list2):
        return len(set(list1) & set(list2))     
    if(isinstance(inputA, str)):
        inputA = inputA.split()
    if(isinstance(inputList, str)):
        inputList = inputList.split()
    # Initialize variables to track the list with the most matches
    max_matches = 0
    best_match = []
    indx = -1
    # Iterate over each list in inputList
    for idx, sublist in enumerate(inputList):
        if(isinstance(sublist, str)):
            sublist = sublist.split()
        common_elements = count_common_elements(inputA, sublist)        
        # Update the best match if current sublist has more matches
        if common_elements > max_matches:
            max_matches = common_elements
            best_match = sublist
            indx = idx
    return {"index": indx, "match": best_match}


def split_by_uppercase(text):
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    return result


def camelCaseSplit(s, **kwargs):
    """
    kwargs: 
    - selfReturn --> se non trova alcun risultato, ritorna la stringa 's' data in input
    """
    if(s):
        # Split the string into segments
        segments = re.findall(r"[A-Z]+(?=[a-z]|\d|\W|$)|[A-Z]?[a-z]+|\d+|[A-Z]+", s)
        # Process segments to handle special cases
        result = []
        i = 0
        while i < len(segments):
            # Handle uppercase followed by number
            if i + 1 < len(segments) and segments[i].isupper() and segments[i + 1].isdigit():
                result.append(segments[i] + segments[i + 1])
                i += 2
            # Handle single uppercase letter followed by lowercase
            elif (
                len(segments[i]) == 1 and segments[i].isupper() and i + 1 < len(segments) and segments[i + 1][0].islower()
            ):
                result.append(segments[i] + segments[i + 1])
                i += 2
            else:
                result.append(segments[i])
                i += 1
        if(kwargs.get("selfReturn")):
            return " ".join(result) if result else s
        else:
            return " ".join(result) if result else None
    else:
        return None


def extractBracketText(inputText:str, type:str):  
    """
    Estrae il testo dalle parentesi.
    - type: '()',  '[]',  'any'
    """
    if(inputText and inputText != ""):
        if(type == "()"):  
            return re.findall(r'\((.*?)\)', inputText)
        elif(type == "[]"):  
            return re.findall(r'\[(.*?)\]', inputText)
        elif(type == "any"):  
            inputText = inputText.replace("[","(").replace("]",")")
            return re.findall(r'\((.*?)\)', inputText)
        else:
            return None
    else:
        return None
    
    
# COMPLETAMENTO
def fill_DataType(dataToCheck:str, dataDict:list, **kwargs):
    """
    Modifica i dati in base al loro utilizzo (file mappa o file profili) 
        - profile = True -> per file profili, default per mappa
    """
    if(dataToCheck and dataToCheck != "" and dataDict):
        usageType = 1
        for key, value in kwargs.items():
            if("profi" in key.lower()):
                usageType = 0
        
        if("_" in dataToCheck or " " in dataToCheck):
            for var in [" ","-"]:
                dataToCheck = dataToCheck.replace(var,"_") 
        for dataT in dataDict:
            for key, values in (dataT).items():
                for value in values:
                    if(dataToCheck.strip().upper() == value):
                        return values[usageType]
    else:
        return None
        

def fillImportColumns(dfRif, dfimport_, sheetRif:str, importColumns:list, **kwargs): 
    """
    riferimento ai dati dello sheet "WIP"/"W.I.P." nello sheet "Import"
    """
    def excel_column_letter(column_number):
            result = ""
            tempCol = column_number
            prefix = ""
            if(column_number>26): 
                column_number -= 26
                prefix = "A"
                if(column_number>26): 
                    column_number -= 26
                    prefix = "B"
            while column_number > 0:  
                column_number, remainder = divmod(column_number - 1, 26)
                result = chr(65 + remainder) + result
            return prefix + result
       
    offset = 2#kwargs.get("offset") if "offset" in kwargs.keys() else 1
    dfimport = pd.DataFrame(dtype=str) 
    for colonna in importColumns:
        dfimport[colonna] = None

    for index, row in dfRif.iterrows(): 
        dfimport.loc[index, "deviceId"] = "=" + sheetRif + "!" + str(excel_column_letter(dfRif.columns.get_loc('Escludi Profili')+1)) + str(index + offset) if "Escludi Profili" in dfRif.columns else ""
        dfimport.loc[index, "deviceName"] = "=" + sheetRif + "!" + str(excel_column_letter(dfRif.columns.get_loc('NewDevice')+1)) + str(index + offset) if "NewDevice" in dfRif.columns else ""
        dfimport.loc[index, "signalName"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('NewSignalName')+1)) + str(index + offset) if "NewSignalName" in dfRif.columns else ""
        dfimport.loc[index, "profileName"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('NewProfileName')+1)) + str(index + offset) if "NewProfileName" in dfRif.columns else ""
        dfimport.loc[index, "dataType"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('NewDataValueType')+1)) + str(index + offset) if "NewDataValueType" in dfRif.columns else ""
        dfimport.loc[index, "registerType"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('NewRegisterType')+1)) + str(index + offset) if "NewRegisterType" in dfRif.columns else ""
        dfimport.loc[index, "register"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('NewRegister')+1)) + str(index + offset) if "NewRegister" in dfRif.columns else ""
        dfimport.loc[index, "bitIndex"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('NewBitIndex')+1)) + str(index + offset) if "NewBitIndex" in dfRif.columns else ""
        dfimport.loc[index, "registerCount"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('newRegisterCount')+1)) + str(index + offset) if "newRegisterCount" in dfRif.columns else "1"
        dfimport.loc[index, "datasourceName"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('dataSource')+1)) + str(index + offset) if "dataSource" in dfRif.columns else ""
        dfimport.loc[index, "driverInstance"] = ""
        dfimport.loc[index, "disabled"] = "false"
        dfimport.loc[index, "offset"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('$offsetMODBUS')+1)) + str(index + offset) if "$offsetMODBUS" in dfRif.columns else "0"
        dfimport.loc[index, "slaveId"] = "=" + sheetRif + "!" +  str(excel_column_letter(dfRif.columns.get_loc('$slaveId')+1)) + str(index + offset) if "$slaveId" in dfRif.columns else "1"
        dfimport.loc[index, "bitMask"] = "0000000000000000"
    return dfimport


# Lettura / Scrittura file
def rw_file(**kwargs):
    """
    Legge/Scrive dati su file (json/txt).
    kwargs: 
    - fileName = str(nome del file) (optional / o \\ ad inizio file). se non specificato il formato legge un .json
    - filePath = str(nome del percorso) (optional / o \\ a fine percorso).
    - mode = 'load/read' o 'save/create/write'. Default = 'load'
    - data = str(dati) da salvare sul file -> se esiste automaticamente mode = 'save'  
    """
    fileName = kwargs.get("file") if "file" in kwargs.keys() else None
    filePath = kwargs.get("path") if "path" in kwargs.keys() else ""
    dataToSave = kwargs.get("data") if "data" in kwargs.keys() and kwargs.get("data") != "" else None

    if(fileName and fileName != ""):
        mode = "load"

        if(".txt" not in fileName and ".json" not in fileName):
            fileName += ".json"
        
        if(filePath != ""):
            if(project_root.lower().replace("/","\\") not in filePath.lower().replace("/","\\")):
                if(((project_root.endswith("\\") or project_root.endswith("/")) and not (filePath.startswith("\\") or filePath.startswith("/"))) or
                   (not (project_root.endswith("\\") or project_root.endswith("/")) and (filePath.startswith("\\") or filePath.startswith("/")))):
                    filePath = project_root + filePath
                elif(not (project_root.endswith("\\") or project_root.endswith("/")) and not (filePath.startswith("\\") or filePath.startswith("/"))):
                    filePath = project_root + "\\" + filePath
            else:
                if(not (filePath.endswith("\\") or filePath.endswith("/")) and not (filePath.startswith("\\") or filePath.startswith("/"))):
                    filePath += "\\"

        if(("mode" in kwargs.keys()) and ("save" in kwargs["mode"] or "write" in kwargs["mode"] or "create" in kwargs["mode"]) or dataToSave):
            mode = "save"            

        if((".txt" in fileName) or ("type" in kwargs.keys() and "txt" in kwargs.get("type").lower())): 
            if(mode == "load"): 
                try:             
                    with open(filePath + fileName, encoding="utf8") as file: 
                        return file.read().strip()          
                except FileNotFoundError:
                    return None 
                
            elif(mode == "save"):                           
                    file = open(filePath + fileName, 'w', encoding="utf-8")
                    file.write(str(dataToSave))
                    file.close()
                    return True       

        elif((fileName.endswith(".json")) or ("type" in kwargs.keys() and "json" in kwargs.get("type").lower())):    
            if(mode == "save" and dataToSave): 
                """with open(filePath + fileName, 'w', encoding="utf-8") as f:
                    if isinstance(dataToSave, list):  # Check if data is a list (e.g., array of strings)
                        json.dump(dataToSave, f, indent=4 , ensure_ascii=False, sort_keys=True)
                    elif isinstance(dataToSave, str):  # Save as string in plain text if it's a string
                        f.write(dataToSave)
                    else:
                        raise ValueError("Unsupported data type for saving.")    
                    return True """
                if(isinstance(dataToSave, str)):
                    with open(filePath + fileName, 'w', encoding="utf-8") as f:
                        f.write(dataToSave)
                    return True
                elif(isinstance(dataToSave, list)):
                    with open(filePath + fileName, 'w', encoding="utf-8") as f:
                        json.dump(dataToSave, f, indent=4 , ensure_ascii=False, sort_keys=True)
                        return True
                elif(isinstance(dataToSave, dict)):
                    with open(filePath + fileName , 'w', encoding="utf-8") as json_file:
                        json.dump(dataToSave, json_file, ensure_ascii=False, sort_keys=True)
                    return True
            
            elif(mode == "load"):              
                try:
                    with open((filePath + fileName), encoding="utf-8") as file:
                        try:
                            return json.load(file)
                        except:
                            return None                                            
                except FileNotFoundError:
                    return False
    else:   
        print(f"Nome file mancante!")


def loadSettings(idName:str, dataPull:str, **kwargs):
    """
    Funzione per caricamento dati da "\\backend\\scripts\\FileEssenziali\\Settings\\settings.json"
    es. type: path, files, cardinatorSettings, dragonFlySettings,  globalSettings,  mappinatorSettings,  plantSettings,  profilatorSettings.
    - dato un "_id" ritorna i dati presenti in "data"
    - loadSettings("paths", "uploads") -> dal dict 'paths' cerca 'uploads'
    """
    settingsFileName = "settings.json"
    settingsFolder = kwargs.get("path") if kwargs.get("path") and kwargs.get("path") != "" else "\\backend\\scripts\\FileEssenziali\\Settings\\" 
    settings = (rw_file(path = project_root + settingsFolder, file = settingsFileName))
    tempArr = []
    if(not settings):
        return None
    if(idName == "" and dataPull == ""):
        for setting in settings:
            if(setting not in tempArr):
                tempArr.append(setting)
        return tempArr
    elif(idName != "" and dataPull == ""):
        for setting in settings[idName]:
            if(setting["_id"] not in tempArr):
                tempArr.append(setting["_id"] )
        return tempArr
    else:
        for tempy in settings[idName]:
            if(tempy["_id"] == dataPull):
                return tempy["data"]


def fileExists(**kwargs):
    """
    Cerca se il file indicato esiste o no
    - path
    - file
    - extension
    """
    extensions = [".xlsx", ".csv", ".txt", ".json"]
    file = kwargs.get("file", None)
    path = kwargs.get("path", "")
    
    extension = kwargs.get("extension", None)

    if not file:
        return False
    
    if(path != "" and not path.endswith("\\") or not path.endswith("/")):
        path += "\\"

    if(extension):
        if(not file.endswith(extension)):
            file += extension        
        return os.path.isfile(path + file)
    
    else:
        flag = False
        for ext in extensions:
            if(file.endswith(ext)):
                if(os.path.isfile(path + file)):
                    flag = True
            else:
                if(os.path.isfile(path + file + ext)):
                    flag = True
        return flag


def fileInUse(filename):
    """Se il file esiste, cerca di rinominarlo in se stesso per verificare se è aperto o no."""
    try:
        os.rename(filename, filename)
        return False
    except:    
        return True
    

def rw_xlsx(**kwargs):    
    """
    Carica o Salva un file .xlsx
    kwargs: 
    - file -> nome del file (estensione '.xlsx' optional)
    - path -> percorso del file
    - df -> df con i dati da salvare oppure dict di df {"sheetName1": df1, "sheetName2": df2}
    - sheet -> -1/all per tutti gli sheet, altrimenti nome specifico stringa o lista
    - mode -> save / load
    """
        
    fileName = kwargs.get("file") if "file" in kwargs.keys() else None
    filePath = kwargs.get("path") if "path" in kwargs.keys() else ""
    #dataToSave = kwargs.get("data") if "data" in kwargs.keys() and kwargs.get("data") != "" else None
    #df = kwargs.get("df") if "df" in kwargs.keys() and kwargs.get("data") != "" else None    
    df = kwargs.get("df") if "df" in kwargs.keys() else None    
    sheets = kwargs.get("sheet", None)
    standalone = kwargs.get("standalone", None) 

    if(fileName):
        if(".xlsx" not in fileName):
            fileName = fileName + ".xlsx"

        mode = "load"
        if(("mode" in kwargs.keys()) and ("save" in kwargs["mode"] or "write" in kwargs["mode"] or "create" in kwargs["mode"]) or "df" in kwargs.keys()):
            mode = "save"   

        if(filePath != ""):    
            if(not (fileName.startswith("\\") or fileName.startswith("/")) and not (filePath.endswith("\\") or filePath.endswith("/"))):
                filePath += "\\" 

            if(standalone):
                 filePath = filePath
            else:
                if(project_root.lower().replace("/","\\") not in filePath.lower().replace("/","\\")):
                    if(((project_root.endswith("\\") or project_root.endswith("/")) and not (filePath.startswith("\\") or filePath.startswith("/"))) or
                    (not (project_root.endswith("\\") or project_root.endswith("/")) and (filePath.startswith("\\") or filePath.startswith("/")))):
                        filePath = project_root + filePath
                    elif(not (project_root.endswith("\\") or project_root.endswith("/")) and not (filePath.startswith("\\") or filePath.startswith("/"))):
                        filePath = project_root + "\\" + filePath
        
        if(sheets and isinstance(sheets,str)):
            if("all" == sheets.lower() or sheets== "-1"):
                sheets = -1
                mode = "load"
            else:
                sheets = re.split(r"[,;/]", sheets)

        if(mode == "load"):           
            try:      
                if sheets is None:                                        
                    return pd.read_excel(filePath + fileName, dtype = str)
                if(isinstance(sheets, int)):
                    if(sheets < 0 ):
                        all_sheets = pd.ExcelFile(filePath + fileName).sheet_names
                        #print(all_sheets, sheets)
                        return {s: pd.read_excel(filePath + fileName, sheet_name=s, dtype=str) for s in all_sheets}                        
                    else:
                        return pd.read_excel(filePath + fileName, sheet_name=sheets, dtype=str)
                
                elif(isinstance(sheets, list)):
                    resDf = []
                    for foglio in sheets:
                        tempDf = pd.read_excel(filePath + fileName, sheet_name=foglio, dtype=str)
                        resDf.append(tempDf) if tempDf not in resDf else next
                    return pd.concat(resDf, axis=1, ignore_index=False)
            except FileNotFoundError:
                return None
        
        elif(mode == "save"): 
            alreadyOpen = False
            if(os.path.isfile(filePath + fileName) == True):
                alreadyOpen = fileInUse(filePath + fileName)
                while(alreadyOpen == True):
                    input("File già aperto!\nChiudere il file e premere invio per continuare\n")                    
                    alreadyOpen = fileInUse(filePath + fileName)

            if(alreadyOpen == False):          
                with pd.ExcelWriter(filePath + fileName) as writer:
                    try:
                        if("df" in kwargs.keys()):
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


# Miscelanea
def progress(count:int, total:int, status = ''):                                                                  
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def progressYield(currValue: float, maxDim: int):
    """Ritorna il progress formato dict per la funzione di yield da passare successivamente al frontend per il progress bar/circle"""  
    if(currValue != 0 and maxDim != 0): 
        progress = round(100.0 * currValue / float(maxDim), 1)                        
        return {"progress": progress}
    else: return None
    
    
def noticeUpdate(noticeHolder, inputString:str):
    """
    ritorna noticeHolder dato in input con l'aggiunta del testo in input (se non presente)
    """
    if(not noticeHolder):
        noticeHolder = []
    if(inputString and inputString != ""):
        if(isinstance(noticeHolder, list)):
            noticeHolder.append(inputString) if inputString not in noticeHolder else next
        elif(isinstance(noticeHolder, str)):
            noticeHolder += str(f"|{inputString}|") if str(f"|{inputString}|") not in noticeHolder else ""
        return noticeHolder


def lowerFirstChar(inStr):
    """
    'lowerCase' della prima lettera della stringa data in input
    """
    if(inStr and len(inStr) > 1):
        return inStr[0].lower() + inStr[1:]


def upperFirstChar(inStr):
    """
    'upperCase' della prima lettera della stringa data in input
    """
    if(inStr and len(inStr) > 1):
        return inStr[0].upper() + inStr[1:]


def extract_id(inputData:str, splitRule): 
    """
    cerca di estrare un potenziale di max 6 caratteri ID dalla strigna data in input
    """ 
    if(inputData):
        inputData = re.split(r"" + splitRule, inputData)
        ids = []
        if(len(inputData) == 1 and inputData[0].isdigit()):
            ids.append(inputData[0])
        for element in inputData:
            if(len(element) <= 6):                       
                pattern = r'\b(?=\w*\d)(?=\w*[a-zA-Z])\w{2,}\b'
                ids.append((re.findall(pattern, element))[0]) if (re.findall(pattern, element)) else next 
    return "/".join(ids) if "/".join(ids) != "" else None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_script_list(folderPath:str):
    """Ritorna la lista degli script dal path indicato"""
    return [file for file in os.listdir(folderPath) if file.endswith('.py')]


def get_template_files_list(folderPath:str):
    """Ritorna la lista dei file dal path indicato"""
    template_files = [file for file in os.listdir(folderPath) if os.path.isfile(os.path.join(folderPath, file))]
    return template_files


def check_resources():
    available_memory = psutil.virtual_memory().available
    cpu_percent = psutil.cpu_percent()
    perc_memory = psutil.virtual_memory().percent
    return available_memory, cpu_percent, perc_memory


def resourceMonitor():
    available_memory = psutil.virtual_memory().available#round((psutil.virtual_memory().available)/(1024*1024), 2)
    tot_memory = psutil.virtual_memory().total#round((psutil.virtual_memory().total)/(1024*1024), 2)
    perc_memory = psutil.virtual_memory().percent
    cpu_percent = round(psutil.cpu_percent(), 2)
    #stats = {"cpu": f"{cpu_percent}", "RAM": f"{round((available_memory/tot_memory)*100, 2)}"}
    stats = {"cpu": f"{cpu_percent}", "RAM": f"{perc_memory}"}
    return stats


def get_ip():
    """Ritorna l'indirizzo IP"""
    try:
        # This establishes a connection to an external service (Google's DNS), just to get the network IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))  # Use Google's public DNS server to check routing
        ip_address = s.getsockname()[0]
        s.close()
    except Exception as e:
        print(f"Error determining IP address: {e}")
        # Fallback to bind to all interfaces
        ip_address = '0.0.0.0'
    return ip_address




if __name__ == "__main__":
    0