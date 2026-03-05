import pandas as pd
import traceback 
import sys, os, os.path
import pymongo
import time
import json
import copy
import requests

import multiprocessing
from functools import partial
from multiprocessing import Manager


project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, mongoSearch, normalizzatore, applyRules, rulesDefiner
from backend.scripts.Analisi_Elaborazione.MappaturaDragonfly import scriptExtractor

from llama_cpp import Llama
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")

# ----------------------------------- START COSTANTI -----------------------------------#  
SheetsName = ["WIP", "Import"]
dataTypeDict = sharedCode.loadSettings("globalSettings", "dataType") 
registerTypeDict = sharedCode.loadSettings("globalSettings", "registerTypes") 

dictFolder = project_root + sharedCode.loadSettings("paths", "dictFolder")
rulesPath = project_root + sharedCode.loadSettings("paths", "rulesFolder")

dictFileName = sharedCode.loadSettings("files", "dizionarioMain")

sigRules =  sharedCode.loadSettings("files", "sigRules") 
sigRulesRaw =  sharedCode.loadSettings("files", "sigRulesRaw")


splitRule = sharedCode.loadSettings("globalSettings", "splitRule")
importColumns = sharedCode.loadSettings("globalSettings", "colonneImport")

dictionary = (sharedCode.rw_file(path = dictFolder, file = dictFileName))

indexedAliasArray = normalizzatore.aliasIndexArray(dictionary)

currRules = copy.copy(rulesDefiner.loadRulesData(rulesPath, sigRulesRaw, sigRules)) # create = True --> Error!!! ç_ç

sysPrompt = """

            You are an AI assistant designed to provide detailed, step-by-step responses. Your outputs should follow this structure:
            1. Begin with a <thinking> section.
            2. Inside the thinking section:
            a. Briefly analyze the question and outline your approach.
            b. Present a clear plan of steps to solve the problem.
            c. Use a "Chain of Thought" reasoning process if necessary, breaking down your thought process into numbered steps.
            3. Include a <reflection> section for each idea where you:
            a. Review your reasoning.
            b. Check for potential errors or oversights.
            c. Confirm or adjust your conclusion if necessary.
            4. Be sure to close all reflection sections.
            5. Close the thinking section with </thinking>.
            6. Provide your final answer in an <output> section.

            Always use these tags in your responses. Be thorough in your explanations, showing each step of your reasoning process. Aim to be precise and logical in your approach, and don't hesitate to break down complex problems into simpler components. Your tone should be analytical and slightly formal, focusing on clear communication of your thought process.

            Remember: Both <thinking> and <reflection> MUST be tags and must be closed at their conclusion
            Make sure all <tags> are on separate lines with no other text. Do not include other text on a line containing a tag.

            ### Your task is to analyze a given script and extract specific information. 
                
            Follow these steps carefully:
                Extract Variables:
                Scan all 'if' condition blocks in the script.
                Identify and list all variables starting with '$'.
                Include variables in ActionServiceListener blocks.

                Extract Labels and IDs:                
                    Locate the <grid> section in the script.
                    For each <row> element inside <rows>:

                        Extract the 'value' attribute from the <label> tag.
                        Extract the 'id' attribute from the <label> tag inside the <div>.    
                        Compile a list of these label-ID pairs.

                Compare and Extract Logic Values:
                    Match variables from step 1 with IDs from step 2.
                    For each match, examine the corresponding 'if' condition block.

                    If the condition sets the class to 'bellOn' or 'circleOn':
                        Extract the logic value (usually 1 for 'bellOn'/'circleOn') for commands, states and allarms.

                    For command variables (e.g., $commManCmd):
                        Look for the logic value in the $service.write() call (e.g., 1.0 or 0.0).
                        Associate the corresponding label text with this command.

                For measurement (mis) and parameters (par) variables e.g., $misValorePotenzaFaseR, $vibrazioneLimitePar:
                    Look for when the $variable is getValue() and for the label check when the 'fellow' has 'setValue'.
                    For a measurement value, the 'label value' that must be extracted is the description associated with the extracted fellow that corresponds to the 'value id' 
                    A measurement variable doesn't have any logic, instead it has UOM (unit Of Measure).
                    UOM example: ($misTensione1 -> UOM = 'V'), ($correnteF1Mis -> UOM = 'A'), ($potezaMis -> UOM = 'kW'), ($valCisternaPienaPar -> UOM = '%').

                    <measurement example>
                    //////
                    <row>
                        <label value='Valore potenza fase R'/> <div align='right'>  <label id='misValorePotenzaFaseR'/> <label value='KW'/> </div>
                    </row>
                    //////
                    and
                    //////
                    if (tags.get('$misValorePotenzaFaseR')?.getValue() != null) {
                            BigDecimal e = new BigDecimal(tags.get('$misValorePotenzaFaseR')?.getValue());
                            e = e.setScale(0, BigDecimal.ROUND_HALF_UP);
                            component.getFellow("misValorePotenzaFaseR").setValue("" + e);
                        }else {
                            component.getFellow("misValorePotenzaFaseR").setValue("- - -");
                            component.getFellow("misValorePotenzaFaseR").setClass('blink_me');
                        }

                    expected output = 
                    [{'variable': $misValorePotenzaFaseR, 'fellow': misValorePotenzaFaseR, 'label': Valore potenza fase R, 'logic': "KW"}]
                    //////
                    </measurement example>


                Generate JSON Output:
                    Create a JSON array of objects without comments or annotations inside of it.
                        Each object should contain:

                        'variable': The '$' prefixed variable name
                        'fellow': The 'id' attribute value (without 'alr' or 'cmd' prefix)
                        'label': The corresponding label text
                        'logic': The extracted logic value (1 or 0 for 'bellOn'/'circleOn', or the specific value for commands), for measurements or parameters the UOM if avaiable.

                        Example JSON structure:
                        json
                        [
                          {
                            "variable": "$guastoComunicazPlcDongoAlr",
                            "fellow": "GuastoComunicazPlcDongo",
                            "label": "Guasto comunicazione PLC Dongo",
                            "logic": "1"
                          },
                          {
                            "variable": "$commManCmd",
                            "fellow": "CommuManOn",
                            "label": "Commutazione manuale attiva",
                            "logic": "1.0"
                          }
                        ]

                Important notes:
                    - Be thorough in scanning the entire script for all relevant information.
                    - Handle variations in variable naming and condition structures.
                    - For command variables, extract both the active and inactive states.
                    - Ensure all extracted data is accurately represented in the final JSON output.
                    - If a variable or label is missing, use 'null' or an empty string as appropriate.
                    - Double-check that all JSON objects have consistent structure and all required fields.
                    - Do not explain your process. Evaluate your answer before replying, checking for errors. Always return the data in the specified JSON format.
                    - If the 'logic' is too complex to extract and some variables may not have a direct 'if' condition block associated with them, let the field to 'none' or empty ''. 
                    - Ensure that the "logic" field always has the delimiter double quote "" even when is empty.
                    - The logic field in the json return can't have code snipets inside, example {"logic": ""+tcpInErr} -> {"logic":"tcpInErr"}.
                    - Do not return a logic value when is associated with blink in the 'if' condition block.

                    - Remember to always use the JSON format and ensure the structure is correct without any comments inside the JSON body. 
                    - Ensure the JSON format has the correct delimiters double quote.
                    
                    
                    ! example of INCORRECT JSON FORMAT: {
                        "variable": "$terniManDirezioneStatus",
                        "fellow": component.getName() + "terniDirezione",
                        "label": "Direzione Terni",
                        "logic": "" // No logic value associated with an 'if' condition block for command variables in this case, hence empty string as per instructions
                    }
                    
                    -> Ensure that there aren't code segments inside the JSON like "fellow": component.getName()+ "terniDirezione" ---> only "fellow": "terniDirezione" is acceptable.
                    -> do not make comments whent the "logic" filed is empty in the JSON like: "logic": ""// No logic value associated with an 'if' condition block for command variables in this case, hence empty string as per instructions.
                    
                    -> Remove: '// No explicit logic value provided in the condition block, hence empty string as per instructions'
                    -> Remove: '// There is no corresponding fellow attribute for $ortesAutoDirezioneStatus in the script provided.'
                    -> Remove: '// Corresponding label text cannot be determined due to missing fellow attribute.'
                    -> Remove: '""+tags.get('variable')?.getValue()+""'.
                    -> Remove: 'component.getName()+ '.
                    !
                """
sysPrompt2 = """You are tasked with returning a JSON compliant format. Ensure that there are no mistakes in the given JSON. If there are any errors or comments placeholders that may break the JSON format, 
                correct it
                example:  {
                              "variable": "$intGeneraleMotopompaStatus",
                              "fellow": "intGenMoto",
                              "label": "Interruttore generale motopompa",
                              "logic": "" 
                            }
  
    DO NOT MAKE ANY COMMENTS. Focus only on extracting the JSON DATA.
    Ensure the correct enclousure in double quotes."""

example = """<example> [{'variable': '$var1', 'fellow': 'fellow1', 'label': label1, 'logic': '1'}, {'variable': '$var2', 'fellow': 'fellow2', 'label': label2, 'logic': '0'}, {'variable': '$var3', 'fellow': 'None', 'label': None, 'logic': 'None'}] </example>"""

skipColumns = ["archetypeScript", "scriptData", "archetypeMainScript"]

urlAddress = f"http://{sharedCode.get_ip()}:5600/api/"

localElab = True # se utilizzare LLM locale o appoggiarsi al server (lasciare locale = True) Per disabilitare completamente l'elaborazione degli script da LLM mettere su False

stopFlag = False

yieldingFlag = True #non toccare

errorsList = []
globalResult = None

client_id = None
sio = None
# ----------------------------------- END COSTANTI -----------------------------------# 


def mainCall(nomeGalleria:str, uploadPath:str, downloadPath:str, fileAnagrafica, auxName:str, CPUCores:int, chosenDB:str, **kwargs):  
    global client_id
    global sio
    client_id = kwargs.get("client_id", None)
    sio = kwargs.get("sio", None)    
    prefisso = ""
        
    links = []
    try:                                 
        rulesDefiner.creaNuovoFormato(rulesPath, sigRulesRaw, sigRules)
        #if(chosenDB == "" or chosenDB.startswith("Q")):
        #    chosenDB = "_Q_"  
        downloadOnly = kwargs.get("soloScarico", True)
        
        global yieldingFlag
        yieldingFlag = kwargs.get("yieldingFlag", False) 
        
        if(downloadOnly == True ):
            prefisso = sharedCode.loadSettings("dragonFlySettings", "prefix_scarico")
        else:
            prefisso = sharedCode.loadSettings("dragonFlySettings", "prefix_elaborazione")
            
        savename = f"{prefisso}_{chosenDB}_{nomeGalleria}_{sharedCode.timeStamp(fullDate = True)}.xlsx"

        yield f"...cercando '{nomeGalleria}'...nel db [{chosenDB}]" if yieldingFlag else print (f"...cercando '{nomeGalleria}'...nel db [{chosenDB}]")
        currentPlant = findPlant(nomeGalleria.strip(), chosenDB)
        if(not currentPlant):
            msg =  f"Nessun impianto trovato per: '{nomeGalleria}' nel db: '{chosenDB}'" 
            yield msg if yieldingFlag else print(msg)
            return None
        yield f"...trovato: '{currentPlant["name"]}'"  if yieldingFlag else print (f"...trovato: '{currentPlant["name"]}' - db: {chosenDB}" )
        
        subPlantNumber = len(currentPlant["views"]) if "views" in currentPlant.keys() else None

        usedCpuCores_DB = copy.copy(CPUCores)
        if(subPlantNumber):
            if(subPlantNumber >= 1 and subPlantNumber <= CPUCores):
                usedCpuCores_DB = subPlantNumber
            chunksDB = sharedCode.defineChunkSize(usedCpuCores_DB, subPlantNumber)

            with Manager() as manager:            
                shared_data = manager.dict()
                shared_data["sharedData"] = manager.list()
                shared_data["archetypeCollection"] = manager.list()
                shared_data["missingWidgets"] = manager.list()
                shared_data["missingTags"] = manager.list()
                shared_data["ExtractedScriptData"] = manager.list()
                shared_data["cpuCounter"] = 0
                shared_data["toDo"] = 0    
                shared_data["done"] = 0 
                shared_data["supportNormalizedData"] = manager.dict()
                shared_data["supportLeftoverdData"] = manager.dict()
                
                yield(f"\nEstrazione da db...") if yieldingFlag else print(f"\nEstrazione da db...")

                load_DB_Data_partial = partial(load_DB_Data)
                args_list = [
                    (usedCpuCores_DB, chosenDB, currentPlant, start, end, shared_data)
                    for start, end in chunksDB
                ]

                with multiprocessing.Pool(processes=usedCpuCores_DB) as pool:
                    for result_list in pool.imap_unordered(load_DB_Data_partial, args_list):
                        yield result_list if yieldingFlag else print(result_list)

                        msg = sharedCode.progressYield(shared_data["done"], len(chunksDB)) 
                        if(msg):
                            yield msg
                    yield {"progress": 100}
                    
                    """
                    Salva una copia degli script
                    """
                    yield "Salvataggio copia degli script in corso..." if yieldingFlag else print("Salvataggio copia degli script in corso..." )
                    scriptsPath = (downloadPath + "scriptsFolder\\" + nomeGalleria)                             
                    try:  
                        os.mkdir(scriptsPath)  
                    except OSError as error:  
                        0#print(error) 
                        #yield error

                    shared_data["ExtractedScriptData"] = sriptsExtraction(shared_data["sharedData"])
                    if(shared_data["ExtractedScriptData"]):                    
                        for indx, scriptData in enumerate(shared_data["ExtractedScriptData"]): #dict_keys(['name', 'variabili', 'scriptData', 'data'])
                            """print(f"{scriptData.keys()}")  
                            if (scriptData["data"]):
                                for dato in scriptData["data"]: #dict_keys(['script', 'data'])
                                    print(f"\t{dato.keys()}")
                                    for dat in dato["data"]:    # ict_keys(['id', 'label', 'uom', 'logicBlock'])
                                        print(f"\t\t{dat.keys()}")"""
                            if(scriptData["scriptData"] != ""):
                                sharedCode.rw_file(path = scriptsPath, file = scriptData["name"] + ".txt" , data = scriptData["scriptData"])
                    

                if(downloadOnly == False):  # Se False, esegue anche l'elaborazione (molto lenta!)
                    usedCpuCores_Data = copy.copy(CPUCores)
                    if(len(shared_data["sharedData"]) >= 1 and len(shared_data["sharedData"]) <= usedCpuCores_Data):
                        usedCpuCores_Data = len(shared_data["sharedData"])
                    dataChunks = sharedCode.defineChunkSize(usedCpuCores_Data, len(shared_data["sharedData"]))
                    

                    """START LLM TEST"""
                    yield "LLM Elaboration" if yieldingFlag else print("LLM Elaboration" )
                    tempHolder = []
                    excludeScriptsNames = ["SCENAR"] # implementare logica per gestione esclusione scripts 
                    
                    #msg = sharedCode.progressYield(0.1, len(shared_data["ExtractedScriptData"])) 
                    #if msg:
                    #    yield msg
                    for indx, data in enumerate(shared_data["ExtractedScriptData"]):
                        checkFlag = checkScriptFolder(data, scriptsPath)
                        tokens = len(tokenizer.encode(f"{str(data["variabili"])} {str(data["scriptData"])} {str(sysPrompt)} {str(example)}"))                        
                        #tokens = len((f"{str(data["variabili"])} {str(data["scriptData"])} {str(sysPrompt)} {str(example)}").split())
                        
                        if(checkFlag == True and data["scriptData"] != ""):  
                            tempDicty = None                           
                            try:
                                tempData = sharedCode.rw_file(file = "_LLM_" + str(data["name"]).strip() + ".json", path = scriptsPath, mode = "load")
                                if(tempData != None and (str(tempData) != "" and str(tempData) != "None")):
                                    tempDicty = tempData
                                    #tempDicty = json.loads(str(tempData).replace("'",'"').replace("none",'"none"').replace("None",'"None"').replace('""', '"')) # .replace("'",'"')
                                    tempHolder.append(tempDicty) if tempDicty and tempDicty not in tempHolder else next                             
                                    yield(f"loaded _LLM_{data["name"]}") if yieldingFlag else print(f"loaded _LLM_{data["name"]}") 
                            except Exception as e:
                                msg = f"\njson.loads ERORR:\n----------------------------\n{"_LLM_" + str(data["name"])}\n{tempData}\n----------------------------\n"
                                error = f"An error occurred: {str(e)}: {msg}"
                                errorsList.append(error) if error not in errorsList else next        
                                yield(msg) if yieldingFlag else print(msg)
                                traceback.print_exc()                             

                        elif(checkFlag == False and data["scriptData"] != ""):                              # Implementare logica qui per esclusione scripts #
                            if(((str(data["variabili"]) != "") and (str(data["scriptData"]) != "") ) and not("SCENAR" in data["name"].upper() or "SWITCH" in data["name"].upper()) 
                               and int(tokens*1.5) < 16000):  
                                result = None           
                                    
                                userRequest = f"""Extract all the variables [{data["variabili"]}] that start with '$' from {data["scriptData"].encode('utf-8').decode('utf-8')}. 
                                                Afterwards extract the fellow associated with that variable and the logic value in the condition block. 
                                                Always return a json format like: {example}. Do not explain."""   
                    
                                jSonReq = {"userPrompt": userRequest, 
                                           "systemPrompt": sysPrompt, 
                                           "temperature": 0.015}
                                
                                serverStatus = check_server_status(urlAddress + 'health')
                                msg = (f"\n{indx}|{len(shared_data["ExtractedScriptData"])} : {data["name"]} (tokens: {tokens}) -> {data["variabili"]}\nserverStatus:{serverStatus}") 
                                yield (msg) if yieldingFlag else print(msg)
                                if(serverStatus == True):
                                    #print("Waiting for server...")    
                                    startLLM = time.time()
                                    response = requests.post(urlAddress + "elaborate", json = jSonReq)                                    
                                    if(response.status_code == 200):
                                        response_data = response.json()
                                        if("status" in response_data.keys() and "elaborated_data" in response_data.keys() and response_data["status"] == "success"):
                                            result = response_data["elaborated_data"]
                                            endLLM = time.time()
                                    else:
                                        yield(f"Faild to process data") if yieldingFlag else print("Faild to process data")
                                        
                                elif(serverStatus == False and localElab == True):  # localElab = True per elaborazione / estrazione dati con LLM locale
                                    msg = "Local Elaboration..."
                                    yield (msg) if yieldingFlag else print(msg)
                                    """
                                    elabora massimo 1.5 x lunghezza dello script, passa massimo numero di layer alla gpu se n_gpu_layers = -1 altrimenti CPU,
                                    - Phi-3.5-mini veloce ma poco preciso 
                                    - Llama-3.1-8B molto lento (CPU) ma risultati migliori
                                    """
                                    
                                    llm = Llama.from_pretrained(verbose = False, n_ctx = int(1.5*tokens) + 0, n_gpu_layers = 0,
                                        #repo_id="bartowski/Phi-3.5-mini-instruct-GGUF",
                                        #filename="Phi-3.5-mini-instruct-Q6_K.gguf"    
                                        #filename="Phi-3.5-mini-instruct-Q8_0.gguf"                                    
                                        repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
                                        filename="Meta-Llama-3.1-8B-Instruct-Q8_0.gguf",
                                        )
                                    #result = modelRunner(llm, sysPrompt, userRequest, temperature = 0.015, stream = True)                                       
                                    startLLM = time.time()
                                    for output in modelRunner(llm, sysPrompt, userRequest, temperature = 0.015, stream = True):
                                        yield {"stream": output}
                                global globalResult
                                if(globalResult):
                                    tempDicty = {"name": data["name"], "dati": globalResult}           
                                    tempHolder.append(tempDicty) if tempDicty not in tempHolder else next    
                                    if(data["scriptData"] != ""):
                                        print(tempDicty)
                                        sharedCode.rw_file(path = scriptsPath, file = "_LLM_" + data["name"] + ".json" , data = tempDicty)
                                    endLLM = time.time()
                                    msg = (f"{"{:.2f}".format(endLLM-startLLM)}s\ttokens: {tokens}\n{str(globalResult)}\n")
                                    yield msg if yieldingFlag else print(msg)
                        
                        msg = sharedCode.progressYield(indx + 1, len(shared_data["ExtractedScriptData"])) 
                        if msg:
                            yield msg 
                        
                    shared_data["ElaboratedScriptsData"] = tempHolder

                    """END LLM TEST""" 
                    
                    msg = (f"\nElaborazione dei dati...{dataChunks}\t tot elementi: {len(shared_data["sharedData"])}")       
                    yield msg if yieldingFlag else print(msg)   
                    shared_data["cpuCounter"] = 0
                    with multiprocessing.Pool(processes = usedCpuCores_Data) as pool:
                        dataElaborationResult = pool.starmap(
                            elaborate_loaded_data,
                            [
                                (usedCpuCores_Data, start, end, shared_data)
                                for start, end in dataChunks
                            ],
                        )   
                           
                    msg = ("\nUnione dfs....")   
                    yield msg if yieldingFlag else print(msg)  
                    df = pd.concat([pd.concat(result) for result in dataElaborationResult])
                    checkDupplicateRegisters(df)

                    for index, dicties in enumerate(shared_data["sharedData"]):
                        for key in dicties.keys():
                            if(key not in skipColumns):
                                df.loc[index, key] = str(dicties[key]).strip() if str(dicties[key]) != "None" else ""
                                
                        msg = sharedCode.progressYield(index + 1, len(shared_data["sharedData"])) 
                        if msg:
                            yield msg 
                                
                    df = df.sort_values(by='widgetArchetype')
                    df2 = fillImportColumns(df, "df2", "WIP")
                    dfs = {"WIP": df, "Import": df2}
 
                    msg = (f"Salvataggio: {sharedCode.rw_xlsx(path = downloadPath, file = savename, df = dfs)})") 
                    yield msg if yieldingFlag else print(msg)
                    #msg = f"""<a href="{downloadPath+outFileName}">{outFileName}</a>"""
                    msg = {"link": f"{downloadPath+savename}", "linkName": f"{savename}"}
                    links.append(msg) if msg not in links else next
                    #yield links if yieldingFlag else print(links)
                    """Salvataggio dei dati mancanti"""
                    sharedCode.rw_file(path = scriptsPath, file = f"missingWidgets_{nomeGalleria}.txt" , data = ",\n".join(shared_data["missingWidgets"])) if(len(shared_data["missingWidgets"]) != 0) else next
                    sharedCode.rw_file(path = scriptsPath, file = f"missingTags_{nomeGalleria}.txt" , data = ",  \n".join(shared_data["missingTags"])) if(len(shared_data["missingTags"]) != 0) else next                      
                
                else:
                    msg = (f"Salvataggio in corso di {len(shared_data["sharedData"])} elementi su dataframe...")
                    yield msg if yieldingFlag else print(msg)
                    df = pd.DataFrame(dtype=str)
                    for index, item in enumerate(shared_data["sharedData"]):
                        for key, value in shared_data["sharedData"][index].items():
                            df.loc[index, key] = str(value) if key not in skipColumns else ""  
                        
                        msg = sharedCode.progressYield(index+1, len(shared_data["sharedData"]))
                        if(msg): 
                            yield msg if yieldingFlag else sharedCode.progress(index, len(shared_data["sharedData"]))
                        
                    df = df.sort_values(by='widgetArchetype')
                    msg = (f"Salvataggio: {sharedCode.rw_xlsx(path = downloadPath, file = savename, df = df)}") 
                    yield msg if yieldingFlag else print(msg)
                    #msg = f"""<a href="{downloadPath+outFileName}">{outFileName}</a>"""
                    msg = {"link": f"{downloadPath+savename}", "linkName": f"{savename}"}                    
                    links.append(msg) if msg not in links else next
                    #yield links if yieldingFlag else print(links)
                    
                    """Salvataggio dei dati mancanti"""
                    msg =  """Salvataggio dei dati mancanti"""
                    yield msg if yieldingFlag else print(msg)
                    sharedCode.rw_file(path = scriptsPath, file = f"missingWidgets_{nomeGalleria}.txt" , data = ",\n".join(shared_data["missingWidgets"])) if(len(shared_data["missingWidgets"]) != 0) else next
                    sharedCode.rw_file(path = scriptsPath, file = f"missingTags_{nomeGalleria}.txt" , data = ",  \n".join(shared_data["missingTags"])) if(len(shared_data["missingTags"]) != 0) else next                      

                    if(len(errorsList) != 0):
                        yield "\n\n"
                        yield str({"errors": errorsList})

        if(links):
            yield {"links": links}
        else:
            yield "Errore nella generazione dei link!"
    except Exception as e:               
        error = f"An error occurred: {str(e)}"
        print(error)
        errorsList.append(error) if error not in errorsList else next
        traceback.print_exc()


def check_server_status(url): 
    """
    Verifica se il server AI / LLM è raggiungibile (Attualmente sempre offline salvo implementazione futura)
    """
    serverStatus = False
    try:
        # Send a GET request to the health check endpoint
        response = requests.get(url)        
        # Check if the server responds with status code 200
        if response.status_code == 200:
            #print("Server is up and running!")
            serverStatus = True
            return True
        else:
            print(f"Server responded with status code: {response.status_code}")    
    except requests.exceptions.ConnectionError:
        #print("Failed to connect to the server. The server might be down.")
        serverStatus = False
        return False
    except requests.exceptions.Timeout:
        serverStatus = False
        return False
        #print("The request to the server timed out.")
    except requests.exceptions.RequestException as e:
        serverStatus = False
        # Catch any other errors
        print(f"An error occurred: {e}")
    return serverStatus


def checkScriptFolder(archData, scriptFolder): 
    """
    Verifica se lo script attuale è stato già elaborato da LLM oppure no
    """
    scripts = [os.path.join(scriptFolder, f) for f in os.listdir(scriptFolder) if 
    os.path.isfile(os.path.join(scriptFolder, f))]
    scriptList = []
    if(archData["scriptData"] != ""):
        for script in scripts:
            scriptList.append(script.replace("\\" + scriptFolder,""))
        for scriptFIle in scriptList:
            if("_LLM_" + archData["name"].strip() in scriptFIle):
                return True
    return False


def modelRunner_OLD(llm, systemPrompt, userRequest, **kwargs):
    """
    Esegue il run del modello attualmente caricato con i parametri forniti per l'estrazione dei dati dallo script in input
    """
    output = None
    temperatura = kwargs.get("temperature", 0.47)
    top_p = kwargs.get("top_p", 0.95)   
    top_k = kwargs.get("top_k", 35)
    repeat_penalty = kwargs.get("repeat_penalty", 1.10)
    stream = kwargs.get("stream", False)    
    
    messages = [{"role": "user", "content": userRequest}]
    if systemPrompt:
        messages.insert(0, {"role": "system", "content": systemPrompt})
        
    llm.reset()
    llm._ctx.kv_cache_clear()
    msg = "Starting"
    yield msg
    #print(msg)
    if stream: 
        global stopFlag 
        schunks = ""
        #print(f"starting...")
        chunks = llm.create_chat_completion(
            temperature=temperatura, 
            top_k=top_k, 
            top_p=top_p, 
            repeat_penalty=repeat_penalty, 
            stream=True,
            messages=messages
        )
        for chunk in chunks:
            if "content" in chunk["choices"][0]["delta"].keys():
                schunk = chunk["choices"][0]["delta"]["content"]
                schunks += schunk
                if (stopFlag == True):
                    stopFlag = False
                    break
                #yield f"{schunk}" if yieldingFlag else print (schunk)
                print (schunk, end = "") if yieldingFlag == False else next
        output = schunks# schunks["choices"][0]["message"]["content"].replace("\'","'").replace("component.getName()+","")
        msg = "DoubleCheck"
        yield msg
        #print(msg)
        output = output.replace("component.getName()+","").replace("component.getName() +","")  # creare funzione per filtraggio migliore
        llm = Llama.from_pretrained(verbose = False, n_ctx = int(1.5*len(output)) + 0, n_gpu_layers = 0,
            #repo_id="bartowski/Phi-3.5-mini-instruct-GGUF",
            #filename="Phi-3.5-mini-instruct-Q6_K.gguf"                                        
            repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
            filename="Meta-Llama-3.1-8B-Instruct-Q6_K.gguf",
            )
        
        if("[" in output and "]" in output):
            messages = [{"role": "user", "content": f"Remove the unnecessary data that may break the JSON format: {(output[output.find("["):output.find("]")+1])}"},  {"role": "system", "content": sysPrompt2}]
            schunks = ""
            #print(f"starting...")
            chunks = llm.create_chat_completion(
                temperature=temperatura, 
                top_k=top_k, 
                top_p=top_p, 
                repeat_penalty=repeat_penalty, 
                stream=True,
                messages=messages
            )
            for chunk in chunks:
                if "content" in chunk["choices"][0]["delta"].keys():
                    schunk = chunk["choices"][0]["delta"]["content"]
                    schunks += schunk
                    if (stopFlag == True):
                        stopFlag = False
                        break
                    yield f"{schunk}" if yieldingFlag else print (schunk, end = "")
                    print (schunk, end = "") if not yieldingFlag else next
        output = schunks
        if("[" in output and "]" in output):
                try:
                    
                    output = json.loads((output[output.find("["):output.find("]")+1]).replace("'",'"').replace("component.getName()+","").replace("component.getName() +",""))
                except Exception as e:
                    msg = (f"\njson.loads ERORR:\n----------------------------\n{str(output)}\n----------------------------\n")                    
                    error = f"An error occurred: {str(e)}"
                    print (msg)
                    errorsList.append(error) if error not in errorsList else next
                    output = None
                    traceback.print_exc()
        return output
    else:
        output = llm.create_chat_completion(
            temperature=temperatura, 
            top_k=top_k, 
            top_p=top_p, 
            repeat_penalty=repeat_penalty, 
            messages=messages
        )
        if output:
            output = output["choices"][0]["message"]["content"].replace("\'","'").replace("component.getName()+","").replace("component.getName() +","")
            if("[" in output and "]" in output):
                try:
                    output = json.loads((output[output.find("["):output.find("]")+1]).replace('"','"'))
                    return output
                except Exception as e:
                    msg = (f"\njson.loads ERORR:\n----------------------------\n{str(output)}\n----------------------------\n")                    
                    error = f"An error occurred: {str(e)}"
                    print (msg)
                    errorsList.append(error) if error not in errorsList else next        
                    output = None
                    traceback.print_exc()
        return output
    

def modelRunner(llm, systemPrompt, userRequest, **kwargs):
    """
    Esegue il run del modello attualmente caricato con i parametri forniti per l'estrazione dei dati dallo script in input
    """
    global globalResult
    globalResult = None
    output = None
    temperatura = kwargs.get("temperature", 0.47)
    top_p = kwargs.get("top_p", 0.95)   
    top_k = kwargs.get("top_k", 35)
    repeat_penalty = kwargs.get("repeat_penalty", 1.10)
    stream = kwargs.get("stream", False)    
    
    messages = [{"role": "user", "content": userRequest}]
    if systemPrompt:
        messages.insert(0, {"role": "system", "content": systemPrompt})
        
    llm.reset()
    llm._ctx.kv_cache_clear()
    
    if stream: 
        global stopFlag 
        schunks = ""
        print(f"starting...")
        chunks = llm.create_chat_completion(
            temperature=temperatura, 
            top_k=top_k, 
            top_p=top_p, 
            repeat_penalty=repeat_penalty, 
            stream=True,
            messages=messages
        )
        for chunk in chunks:
            if "content" in chunk["choices"][0]["delta"].keys():
                schunk = chunk["choices"][0]["delta"]["content"]
                schunks += schunk
                if (stopFlag == True):
                    stopFlag = False
                    break
                #yield f"{schunk}" if yieldingFlag else print (schunk)
                yield schunk
                #print (schunk, end = "") #if yieldingFlag == False else next
                #print (schunk, end = "")
        output = schunks# schunks["choices"][0]["message"]["content"].replace("\'","'").replace("component.getName()+","")
        
        output = output.replace("component.getName()+","").replace("component.getName() +","").replace("'",'"').replace("null", '"null"').replace('""','"')
        output = quoteCheck(output)
        # disabilitato il double check -> llm cambiava i dati presenti nell'input
        #llm = Llama.from_pretrained(verbose = False, n_ctx = int(1.5*len(output)) + 0, n_gpu_layers = 0,
        #    #repo_id="bartowski/Phi-3.5-mini-instruct-GGUF",
        #    #filename="Phi-3.5-mini-instruct-Q6_K.gguf"                                        
        #    repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        #    filename="Meta-Llama-3.1-8B-Instruct-Q6_K.gguf",
        #    )
        
        """if("[" in output and "]" in output):
            messages = [{"role": "user", "content": f"Remove the unnecessary data that may break the JSON format: {(output[output.find("["):output.find("]")+1])}. Ensure the following structure: {example}.\nEnsure the correct enclousure in double quotes."},  {"role": "system", "content": sysPrompt2}]
            schunks = ""            
            llm.reset()
            llm._ctx.kv_cache_clear()
            print(f"\ndoubleCheck struttura JSON...")
            chunks = llm.create_chat_completion(
                temperature=temperatura, 
                top_k=top_k, 
                top_p=top_p, 
                repeat_penalty=repeat_penalty, 
                stream=True,
                messages=messages
            )
            for chunk in chunks:
                if "content" in chunk["choices"][0]["delta"].keys():
                    schunk = chunk["choices"][0]["delta"]["content"]
                    schunks += schunk
                    if (stopFlag == True):
                        stopFlag = False
                        break
                    #yield f"{schunk}" if yieldingFlag else print(schunk, end = "")
                    print (schunk, end = "") #if yieldingFlag == False else next
        output = schunks"""
        if("[" in output and "]" in output):
                try:                    
                    output = json.loads((output[output.find("["):output.find("]")+1]))
                    ##Scommentare per un ulteriore controllo in caso di fallimento dell'llm TODO replace with GEMINI
                    #output= modelRunner_OLD(llm, sysPrompt2, userRequest, **kwargs)
                    # chunks = llm.create_chat_completion(
                    #     temperature=temperatura, 
                    #     top_k=top_k, 
                    #     top_p=top_p, 
                    #     repeat_penalty=repeat_penalty, 
                    #     stream=True,
                    #     messages=messages
                    # )
                    # for chunk in chunks:
                    #     if "content" in chunk["choices"][0]["delta"].keys():
                    #         schunk = chunk["choices"][0]["delta"]["content"]
                    #         schunks += schunk
                    #         if (stopFlag == True):
                    #             stopFlag = False
                    #             break
                    #         #yield f"{schunk}" if yieldingFlag else print (schunk)
                    #         yield schunk
                    #         #print (schunk, end = "") #if yieldingFlag == False else next
                    #         #print (schunk, end = "")
                    # output = schunks# schunks["choices"][0]["message"]["content"].replace("\'","'").replace("component.getName()+","")
                    
                    # output = output.replace("component.getName()+","").replace("component.getName() +","").replace("'",'"').replace("null", '"null"').replace('""','"')
                except Exception as e:
                    msg = (f"\njson.loads ERORR:\n----------------------------\n{str(output)}\n----------------------------\n")                    
                    error = f"An error occurred: {str(e)}: {msg}"
                    print (error)
                    errorsList.append(error) if error not in errorsList else next        
                    output = None
                    traceback.print_exc()
                    
        globalResult = output
        #return output
        # senza stream disabilitato
    """ else:
        output = llm.create_chat_completion(
            temperature=temperatura, 
            top_k=top_k, 
            top_p=top_p, 
            repeat_penalty=repeat_penalty, 
            messages=messages
        )
        if output:
            output = output["choices"][0]["message"]["content"].replace("\'","'").replace("component.getName()+","").replace("component.getName() +","")
            if("[" in output and "]" in output):
                try:
                    output = json.loads((output[output.find("["):output.find("]")+1]).replace('"','"'))                    
                    messages = [{"role": "user", "content": f"Remove the unnecessary data that may break the JSON format: {(output[output.find("["):output.find("]")+1])}. Ensure the following structure: " + "[{'variable': '', 'fellow': '', 'label': '', 'logic': ''}].\nEnsure the correct enclousure in double quotes."},  
                                {"role": "system", "content": sysPrompt2}]
                    output = llm.create_chat_completion(
                        temperature=temperatura, 
                        top_k=top_k, 
                        top_p=top_p, 
                        repeat_penalty=repeat_penalty, 
                        messages=messages
                    )
                    output = json.loads((output[output.find("["):output.find("]")+1]).replace('"','"'))
                    return output
                except Exception as e:
                    msg = (f"\njson.loads ERORR:\n----------------------------\n{str(output)}\n----------------------------\n")                    
                    error = f"An error occurred: {str(e)}: {msg}"
                    #print (msg)
                    errorsList.append(error) if error not in errorsList else next        
                    output = None
                    traceback.print_exc()
        globalResult = output
        #return output
    
    """


def checkDupplicateRegisters(df):
    """
    Cerca se gli indirizzi sono duppplicati
    """
    adresses = []
    adrDict = {}
    for index, row in df.iterrows(): 
        adrDict[str(row["NewAddress"]).strip()] = 0
        if(str(row["NewAddress"]).strip() in adrDict.keys()):
            df.loc[index, "registriDupplicati"] = "True"
        else:
            df.loc[index, "registriDupplicati"] = ""
            adrDict[str(row["NewAddress"]).strip()] += 1
        
        #if(str(row["NewAddress"]).strip() not in adresses):
        #    adresses.append(str(row["NewAddress"]).strip())
        #else:
        #    df.loc[index, "registriDupplicati"] = "True"

def fillImportColumns(dfRif, dfimport_, sheetRif, **kwargs): 
    """
    riferimento ai dati dello sheet "WIP"
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


def sriptsExtraction(shared_data):
    archetypeCollection = []
    for data in shared_data:      
        existingArchetype = False
        for index, archData in enumerate(archetypeCollection):
            if(archetypeCollection[index]["name"] in data["widgetArchetype"]):
                existingArchetype = True
                if(not isinstance(data["archeTypeProperties"], str)):
                    archetypeCollection[index]["variabili"].append(data["archeTypeProperties"]["name"]) if data["archeTypeProperties"]["name"] not in archetypeCollection[index]["variabili"] else next
        if(existingArchetype == False):
            if(not isinstance(data["archeTypeProperties"], str)):
                scripty = (data["archetypeScript"]).encode('utf-8').decode('utf-8') #if data["archetypeScript"] != "" else (data["archetypeMainScript"]).encode('utf-8').decode('utf-8')
                archetypeCollection.append({"name": data["widgetArchetype"], "variabili": [data["archeTypeProperties"]["name"]], "scriptData": scripty})    

    for indx, archetype in enumerate(archetypeCollection):
        archetypeCollection[indx]["data"] = scriptExtractor.extractScriptData(archetype["name"], " ".join((archetype["scriptData"]).split()), None)
    return archetypeCollection


def findPlant(nomeGalleria, chosenDB):
    """
    Cerca l'impianto indicato 'nomeGalleria' all'interno del db indicato"""
    dbAddress = "MongoProductionClient" if chosenDB.startswith("PROD") or chosenDB.startswith("P") else "MongoQualityClient"
    client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
    currDB = client["scada"] 
    extractedData = mongoSearch.readCollectionData(currDB, "scada_system", name = nomeGalleria, regex = True)
    foundItems = []
    for indx, item in enumerate(extractedData):
        foundItems.append(item)

    if(len(foundItems) > 1):
        for indx, item in enumerate(foundItems):                       
            print(f"{indx}:>\t {item["name"]}")            
            if(item["name"].lower().startswith(nomeGalleria.lower())):
                return foundItems[indx]
        return foundItems[0]    #ritorna di default primo match
        #return foundItems[int(input("Indice della galleria da utilizzare: \t"))]   # implementare logica per gestione match multipli
    else:
        if(foundItems):
            return foundItems[0] if foundItems[0] else None


def popolaTempDict(index, currentPlant, subPlants, objectItem, extractedWidgetData, extractedArchetype, tagBind, extractedTagData, extractedUniverse, extractedDataSource, NumeroTag):
    """
    Prepara i dati 'grezzi' dal server nel formato atteso.
    """
    
    def extractArrDictData(inputDataList):
        dictyData = {}
        for inputData in inputDataList:
            tempId = None
            for key, value in inputData.items():
                if(key == "name" and not tempId):
                    tempId = value
                    dictyData[value] = value
                if(key == "value" and tempId):
                    dictyData[tempId] = value
        return dictyData
    
    
    scriptData = ""
    mainScriptData = ""
    archeTypeProperties = None
    dataSourceProperties = None
    
    if(extractedArchetype):
        if("properties" in extractedArchetype.keys() and extractedArchetype["properties"]): # scada_widget_archetype
            for archetypePropery in extractedArchetype["properties"]:
                if(archetypePropery["name"] == tagBind["property"]):
                    archeTypeProperties = copy.deepcopy(archetypePropery)

        if("detailLayout" in extractedArchetype.keys() and extractedArchetype["detailLayout"]):
            if("template" in extractedArchetype["detailLayout"].keys() and extractedArchetype["detailLayout"]["template"]):
                if("content" in extractedArchetype["detailLayout"]["template"].keys() and extractedArchetype["detailLayout"]["template"]["content"]):
                    scriptData = extractedArchetype["detailLayout"]["template"]["content"]

        elif(("detailLayout" in extractedArchetype.keys() and not extractedArchetype["detailLayout"]) and
             ("mainLayout" in extractedArchetype.keys() and extractedArchetype["mainLayout"])):
            if("template" in extractedArchetype["mainLayout"].keys() and extractedArchetype["mainLayout"]["template"]):
                if("content" in extractedArchetype["mainLayout"]["template"].keys() and extractedArchetype["mainLayout"]["template"]["content"]):
                    mainScriptData = extractedArchetype["mainLayout"]["template"]["content"]


    if(extractedDataSource and "configurations" in extractedDataSource.keys() and extractedDataSource["configurations"]):
        for propry in extractedDataSource["configurations"]:
            if(propry and "properties" in propry.keys() and propry["properties"]):      
                dataSourceProperties = extractArrDictData(propry["properties"])

    if("properties" in extractedTagData.keys()): 
        extractedTagData["properties"] = extractArrDictData(extractedTagData["properties"])  

    temp_DB_Data = {
                    "DATI GREZZI >>>": "",

                    "subplant": subPlants[index]["name"] if "name" in subPlants[index].keys() else "",
                    "description": subPlants[index]["description"] if "description" in subPlants[index].keys() else "",

                    "itemName": objectItem["itemName"],
                    "widgetDevice": extractedWidgetData["device"] if extractedWidgetData and "device" in extractedWidgetData.keys() else "",
                    "tagDevice": extractedTagData["device"] if extractedTagData and "device" in extractedTagData.keys() else "",

                    "WidgetName": extractedWidgetData["name"] if extractedWidgetData and "name" in extractedWidgetData.keys() else "",
                    "WidgetDescription": extractedWidgetData["description"] if extractedWidgetData and "description" in extractedWidgetData.keys() else "",
                    "widgetUniverse": extractedWidgetData["universe"] if extractedWidgetData and "universe" in extractedWidgetData.keys() else "",

                    "widgetArchetype": extractedWidgetData["archetype"] if extractedWidgetData and "archetype" in extractedWidgetData.keys() else "",
                    "archetypesDescription": extractedArchetype["description"] if "description" in extractedArchetype.keys() else "",

                    "tagVariable": tagBind["property"] if "property" in tagBind.keys() else "",

                    "tagName": extractedTagData["name"] if "name" in extractedTagData.keys() else "",
                    "tagDescription": extractedTagData["description"] if "description" in extractedTagData.keys() else "",

                    "tagUniverse": extractedTagData["universe"] if "universe" in extractedTagData.keys() else "",
                    "tagGalaxy": extractedTagData["galaxy"] if "galaxy" in extractedTagData.keys() else "",

                    "alarmClass": extractedTagData["alarmClass"] if "alarmClass" in extractedTagData.keys() else "",

                    "NumeroTag" : NumeroTag,
                    "tagProperties": extractedTagData["properties"] if "properties" in extractedTagData.keys() else "",

                    "archeTypeProperties": archeTypeProperties if archeTypeProperties else "",

                    "dataSource": extractedDataSource["name"] if extractedDataSource and "name" in extractedDataSource.keys() else "",                            
                    "dataSourceProperties": dataSourceProperties if dataSourceProperties else "",
                    "$offsetMODBUS": dataSourceProperties["offsetMODBUS"] if dataSourceProperties and "offsetMODBUS" in dataSourceProperties.keys() else "",
                    "$slaveId": dataSourceProperties["slaveId"] if dataSourceProperties and "slaveId" in dataSourceProperties.keys() else "",
                    "$IP": dataSourceProperties["ip"] if dataSourceProperties and "ip" in dataSourceProperties.keys() else "",
                    "dataSourceTenant" : extractedDataSource["tenant"] if extractedDataSource and "tenant" in extractedDataSource.keys() else "", 

                    "register": extractedTagData["properties"]["dataId"] if "properties" in extractedTagData.keys() and  extractedTagData["properties"] and "dataId" in extractedTagData["properties"].keys() else "",
                    "bitIndex": extractedTagData["properties"]["bitIndex"] if "properties" in extractedTagData.keys() and  extractedTagData["properties"] and "bitIndex" in extractedTagData["properties"].keys() else "",
                    "registerType": extractedTagData["properties"]["dataType"] if "properties" in extractedTagData.keys() and  extractedTagData["properties"] and "dataType" in extractedTagData["properties"].keys() else "",
                    "valueType": extractedTagData["properties"]["valueType"] if "properties" in extractedTagData.keys() and  extractedTagData["properties"] and "valueType" in extractedTagData["properties"].keys() else "",                            
                    "registerCount": extractedTagData["properties"]["registerCount"] if "properties" in extractedTagData.keys() and  extractedTagData["properties"] and "registerCount" in extractedTagData["properties"].keys() else "",

                    "archetypeScript": scriptData, #if scriptData != "" and mainScriptData == "" else mainScriptData,
                    "archetypeMainScript": mainScriptData,
                    
                    "galleria": currentPlant["name"] if "name" in currentPlant.keys() else "",
                    "width": subPlants[index]["width"] if "width" in subPlants[index].keys() else "",
                    "height": subPlants[index]["height"] if "height" in subPlants[index].keys() else "",
                    "main": subPlants[index]["main"] if "main" in subPlants[index].keys() else "",
                    "root": subPlants[index]["root"] if "root" in subPlants[index].keys() else "",
                    "posX_old": objectItem["x"] if "x" in objectItem.keys() else "",
                    "posY_old": objectItem["y"] if "y" in objectItem.keys() else ""

                    }
    
    return temp_DB_Data


def load_DB_Data(args):
    """
    Esegue il caricamento dei dati dal db per la galleria indicata...
    - genera 2 file con i dati non trovati/non censiti perchè vuoti missingWidgets & missingTags
    - multi-core
    """
    maxCpuCores, chosenDB, currentPlant, start_index, end_index, shared_data = args
    try: 
        currentCore = copy.copy(shared_data["cpuCounter"])
        shared_data["cpuCounter"] += 1
        shared_data["toDo"] += 1

        dbAddress = "MongoProductionClient" if chosenDB.startswith("PROD") or chosenDB.startswith("P") else "MongoQualityClient"
        client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
        currDB = client["scada"] 
        specificID = ""
        subPlants = currentPlant["views"]
        elementsPerSubPlant = 0
        for index in range(start_index, end_index):  
            for objectItem in subPlants[index]["items"]:   
                elementsPerSubPlant += 1             
                        
                extractedWidgetDatas = (mongoSearch.findCollectionData(currDB, "scada_widget", key = "name", value = objectItem["itemName"]))
                if(extractedWidgetDatas):
                    for extractedWidgetData in extractedWidgetDatas:
                        if("tagBindings" in extractedWidgetData.keys() and extractedWidgetData["tagBindings"]):
                            extractedArchetype = None
                            if("archetype" in extractedWidgetData.keys() and extractedWidgetData["archetype"]):                                
                                extractedArchetypes = (mongoSearch.findCollectionData(currDB, "scada_widget_archetype", key = "name", value = extractedWidgetData["archetype"]))
                                for extractedArchetype in extractedArchetypes:
                                    shared_data["archetypeCollection"].append(extractedArchetype) if extractedArchetype not in shared_data["archetypeCollection"] else next

                            NumeroTag = len(extractedWidgetData["tagBindings"])
                            for tagBind in extractedWidgetData["tagBindings"]:
                                if("tag" in tagBind.keys() and tagBind["tag"]):
                                    extractedTagDatas = (mongoSearch.findCollectionData(currDB, "scada_tag", key = "name", value = tagBind["tag"]))

                                    if(extractedTagDatas): # scada_tag   
                                        for extractedTagData in extractedTagDatas:                               
                                            extractedUniverse = None                         
                                            extractedDataSource = None

                                            if("universe" in extractedTagData.keys() and extractedTagData["universe"]):
                                                extractedUniverses = (mongoSearch.findCollectionData(currDB, "scada_universe", key = "name", value = extractedTagData["universe"]))
                                                
                                                for extractedUniverse in extractedUniverses:
                                                    if(extractedUniverse and "galaxies" in extractedUniverse.keys() and extractedUniverse["galaxies"]):
                                                        for galaxy in extractedUniverse["galaxies"]:
                                                            if(("dataSource" in galaxy.keys() and "name" in galaxy.keys() and "galaxy" in extractedTagData.keys() and extractedTagData["galaxy"]) and (galaxy["name"] in extractedTagData["galaxy"])):
                                                                extractedDataSources = (mongoSearch.findCollectionData(currDB, "scada_datasource", key = "name", value = galaxy["dataSource"]))
                                                                if(extractedDataSources):
                                                                    for extractedDataSourc in extractedDataSources:
                                                                        extractedDataSource = extractedDataSourc
                                            tempDict = popolaTempDict(index, currentPlant, subPlants, objectItem, extractedWidgetData, extractedArchetype, tagBind, extractedTagData, extractedUniverse, extractedDataSource, NumeroTag)
                                            shared_data["sharedData"].append(tempDict) if tempDict and tempDict not in shared_data["sharedData"] else next
                                else:
                                    if("device" in extractedWidgetData):
                                        tempMissingData = {"name": extractedWidgetData["name"], "device": str(extractedWidgetData["device"])}
                                    else:
                                        tempMissingData = {"name": extractedWidgetData["name"], "device": "None"}
                                    shared_data["missingTags"].append(str(tempMissingData)) if str(tempMissingData) not in shared_data["missingTags"] else next
                                    tempMissingData = None
                        else:
                            if("device" in extractedWidgetData):
                                tempMissingData = {"name": extractedWidgetData["name"], "device": str(extractedWidgetData["device"])}
                            else:
                                tempMissingData = {"name": extractedWidgetData["name"], "device": "None"}
                            shared_data["missingTags"].append(str(tempMissingData)) if str(tempMissingData) not in shared_data["missingTags"] else next
                            tempMissingData = None
                else:
                    tempMissingData = {"name": objectItem["itemName"]}
                    shared_data["missingWidgets"].append(str(tempMissingData)) if str(tempMissingData) not in shared_data["missingWidgets"] else next
                    tempMissingData = None
                    
        shared_data["toDo"] -= 1
        shared_data["done"] += 1
        #return f"\tElaborato part 1:> ({elementsPerSubPlant})\t start_index: {start_index} - end_index: {end_index}\t core: {currentCore}/{maxCpuCores - 1}\t ({shared_data["toDo"]})"
        return f"\tEstratti {elementsPerSubPlant} elementi | (CPU) core utilizzato: {currentCore}/{maxCpuCores - 1}\tProcessi rimasti da elaborare: ({shared_data["toDo"]})"
    
    except Exception as e:
        error = f"An error occurred: {str(e)}"
        print(error)
        errorsList.append(error) if error not in errorsList else next
        traceback.print_exc() 
        

def elaborate_loaded_data(maxCpuCores:int, start_index:int, end_index:int, shared_data):
    """
    Elabora i dati e salva e li salva in un dataframe
    """
    try:           
                  
        currentCore = copy.copy(shared_data["cpuCounter"])
        shared_data["cpuCounter"] += 1
        shared_data["toDo"] += 1
        
        msg = f"\tInizio (CPU) core:{currentCore}/{maxCpuCores - 1}\t\tProcessi attuali: ({shared_data["toDo"]})"
        print(msg)
        
        #if(client_id and sio):  
        #    sio.emit(f'response:{client_id}', msg, to=client_id)
        #    #currentProgress = sharedCode.progressYield(maxCpuCores-shared_data["toDo"], maxCpuCores)
        #    #await sio.emit(f'response:{client_id}', {"progress": currentProgress}, to=client_id)
        
        """creazione df"""
        df = pd.DataFrame(dtype=str) 
        
        for index in range(start_index, end_index):
            tempSharedData = shared_data["sharedData"][index]
            annotazioni = None
            funzioniUsate = None           

            tempNormData = None
            tempLOvers = None

            tagGalaxy = str(tempSharedData["tagGalaxy"])
            tagName = str(tempSharedData["tagName"].replace(tempSharedData["tagGalaxy"],""))
            tagDescription = str(tempSharedData["tagDescription"])

            tempSignal = None 
            tempDescr = None
            newLogic = None
            skipFlag = False
            dataSetA = ""
            dataSetB = ""
            normDevice = ""


            """Device: tagDevice > widgetDevice > itemName """ 
            tempDevice = None 
            if(not tempDevice and (tempSharedData["tagDevice"] and tempSharedData["tagDevice"] != "")):
                tempDevice = tempSharedData["tagDevice"]

            if(not tempDevice and ((not tempSharedData["tagDevice"] or tempSharedData["tagDevice"] == "") and (tempSharedData["widgetDevice"] and tempSharedData["widgetDevice"] != ""))):
                tempDevice = tempSharedData["widgetDevice"]
                annotazioni = sharedCode.noticeUpdate(annotazioni,"widget device")
            
            if(not tempDevice and ((not tempSharedData["tagDevice"] or tempSharedData["tagDevice"] == "") and (not tempSharedData["widgetDevice"] or tempSharedData["widgetDevice"] == "") and (tempSharedData["itemName"] and tempSharedData["itemName"] != ""))):
                tempDevice = "$" + tempSharedData["itemName"]
                annotazioni = sharedCode.noticeUpdate(annotazioni,"item device")

            """BitIndex"""
            bitIndex = "0" if tempSharedData["bitIndex"] == None or tempSharedData["bitIndex"] == "" else str(tempSharedData["bitIndex"])
            

            """TagVariable & TagVariable split"""
            tagVariable = tempSharedData["tagVariable"]
            splitTagVariable = sharedCode.camelCaseSplit(tagVariable)
            checkString = ["AP", "CH", "LOCAL", "REMOT", "AUTO", "MANU"]

            normTagNameDescr = normalizzatore.normalizzaDati(tagName + " " + tagDescription, dictionary, splitRule = splitRule, aliasArray = indexedAliasArray, dataType = "LIST")
            tempNormData = normalizzatore.normalizzaDati(str(splitTagVariable), dictionary, splitRule = splitRule, aliasArray = indexedAliasArray, dataType = "LIST")
            """Normalizza dati e dati non censiti"""
            tempLOvers = normalizzatore.paroleNonCensite(str(splitTagVariable)+ " " +tagName + " " + tagDescription, indexedAliasArray, splitRule = splitRule)
            if(sharedCode.any_AinB(checkString, normTagNameDescr)):
                tempNormData += normTagNameDescr

            normy = f"0: {" ".join(list(set(tempNormData)))}"

            """Profile name"""
            archeType = tempSharedData["widgetArchetype"]
            tempProfileName = str((archeType.replace("-SCRIPT","").replace("-DEVICE","").replace("-DETT","").replace("-STATO","")).replace("--","-"))
            if("@" in tempProfileName):
                tempProfileName = tempProfileName.split("@")[0]

            """Elaborazione segnali"""
            scriptLabel = None
            scriptData = None
                        
            SplitTagVariable = " ".join(splitTagVariable) if splitTagVariable and isinstance(splitTagVariable, list) else splitTagVariable if splitTagVariable and isinstance(splitTagVariable, str) else ""


            """ From LLM Start """
            for item in shared_data["ElaboratedScriptsData"]:
                if(archeType == item["name"]):
                    scriptData = item["dati"]
                    for data in item["dati"]:
                        if(isinstance(data, dict) and "variable" in data.keys() and tagVariable in data["variable"] and "logic" in data.keys()):
                            scriptLabel = data
                            newLogic = data["logic"]

            if(scriptLabel and (scriptLabel["label"] != "" and scriptLabel["label"] != "none" and scriptLabel["label"] != "null")):
                tempTag = normalizzatore.normalizeByType("TAG_Collection", f"{SplitTagVariable} {tagDescription}", dictionary, returnType = "descr")
                if(scriptLabel["label"] and not (scriptLabel["label"].lower()).startswith(tempTag.lower())):
                    tempDescr = f"{tempTag.capitalize()} {sharedCode.lowerFirstChar(str(scriptLabel["label"]))}"
                else:                        
                    tempDescr = f"{sharedCode.upperFirstChar(str(scriptLabel["label"]))}"
                tempSignal = (normalizzatore.normalizzaDati(tempDescr, dictionary, splitRule = splitRule, aliasArray = indexedAliasArray).strip()).replace(" ","-")
                funzioniUsate = sharedCode.noticeUpdate(funzioniUsate,"<script>")
            """ From LLM End """
            
            
            if(tempNormData):                  
                normDevice = normalizzatore.normalizeByType("Device_Collection miscItems_Collection", tempNormData, dictionary)                
                tempNormData = tempNormData.split() if isinstance(tempNormData, str) else tempNormData                                    
                rulesResult = applyRules.applyRules(currRules, tempNormData, dictionary, indexedAliasArray, device = normDevice)
                
                normy += f" 1: {" ".join(list(set(tempNormData)))}" if " ".join(list(set(tempNormData))) not in normy else ""
                if(rulesResult and not (tempSignal and tempDescr)):
                    tempSignal = rulesResult["signal"]
                    tempDescr = rulesResult["descr"] 
                    funzioniUsate = sharedCode.noticeUpdate(funzioniUsate,"<0a>")
                    
                elif(not rulesResult and not (tempSignal and tempDescr)):         
                    rulesResult = applyRules.applyRules(currRules, tempNormData, dictionary, indexedAliasArray)                    
                    if(rulesResult and not (tempSignal and tempDescr)):
                        tempSignal = rulesResult["signal"]
                        tempDescr = rulesResult["descr"] 
                        funzioniUsate = sharedCode.noticeUpdate(funzioniUsate,"<0b>")                    
                else:
                    tempNormData += normTagNameDescr                    
                    normy += f" 2: {" ".join(list(set(tempNormData)))}" if " ".join(list(set(tempNormData))) not in normy else ""
                    normDevice = normalizzatore.normalizeByType("Device_Collection miscItems_Collection", normTagNameDescr + tempNormData, dictionary)
                    if(tempNormData):
                        rulesResult = applyRules.applyRules(currRules, tempNormData, dictionary, indexedAliasArray, device = normDevice)
                        if(rulesResult and not (tempSignal and tempDescr)):
                            tempSignal = rulesResult["signal"]
                            tempDescr = rulesResult["descr"]
                            funzioniUsate = sharedCode.noticeUpdate(funzioniUsate,"<1a>")
                        else:
                            rulesResult = applyRules.applyRules(currRules, tempNormData, dictionary, indexedAliasArray)
                            if(rulesResult and not (tempSignal and tempDescr)):
                                tempSignal = rulesResult["signal"]
                                tempDescr = rulesResult["descr"]
                                funzioniUsate = sharedCode.noticeUpdate(funzioniUsate,"<1b>")
                            

            """
            TAG START
            """
            dataArrayForTags = ["ALR_Collection AlrType_Collection:ALR",
                                "MIS_Collection MeasureTypes_Collection:MIS",  
                                "ST_Collection Status_Collection:ST",
                                "CMD_Collection:CMD",
                                "PAR_Collection:PAR"]

            newTag = normalizzatore.normalizeByType("TAG_Collection", tagDescription + " " + SplitTagVariable, dictionary)

            for tagData in dataArrayForTags:
                startingNodes = tagData.split(":")[0].strip()
                tagAssign = tagData.split(":")[1].strip()
                tempTag = normalizzatore.normalizeByType(startingNodes, tagDescription + " " + SplitTagVariable, dictionary)
                newTag += f" {tagAssign}" if tempTag != "" and tagAssign not in newTag else ""
            
            if("BINARY" not in tempSharedData["valueType"]):                
                if (newTag == ""):
                    newTag = "MIS PAR"
                else:
                    newTag += " MIS" if "MIS" not in newTag else ""
                    newTag += " PAR" if "PAR" not in newTag else ""

            if(newTag != "" and tempSignal and not tempSignal.startswith(newTag)):
                annotazioni = sharedCode.noticeUpdate(annotazioni, "incongruenza tag?")
            """
            TAG END
            """

            auxTempNormData = []
            for item in tempNormData:
                auxTempNormData.append(item) if item not in auxTempNormData else next
            if(newTag):
                for taggy in newTag.split():
                    auxTempNormData.append(taggy) if taggy not in auxTempNormData else next
            tempNormData = auxTempNormData


            if(not (tempSignal and tempDescr)):            
                if(tempNormData):
                    rulesResult = applyRules.applyRules(currRules, tempNormData, dictionary, indexedAliasArray, device = normDevice)
                    if(rulesResult):
                        tempSignal = rulesResult["signal"]
                        tempDescr = rulesResult["descr"]
                        funzioniUsate = sharedCode.noticeUpdate(funzioniUsate,"<2a>")
                    else:
                        rulesResult = applyRules.applyRules(currRules, tempNormData, dictionary, indexedAliasArray)
                        if(rulesResult):
                            tempSignal = rulesResult["signal"]
                            tempDescr = rulesResult["descr"]
                            funzioniUsate = sharedCode.noticeUpdate(funzioniUsate,"<2b>")
                        

            if(tempSharedData["archetypeScript"] != ""):
                if(tagVariable.strip() not in str(tempSharedData["archetypeScript"])):
                    annotazioni = sharedCode.noticeUpdate(annotazioni, f"{tagVariable} non presente nello script?")

            """Popola dati"""
            tempDict = {#"stepNorm" : normy,
                        "NewSubplant": "",
                        "Escludi Profili": "",
                        "NewTag": newTag.strip() if newTag else "",
                        "numeroSegnali": tempSharedData["NumeroTag"],
                        "NewProfileName": str(tempProfileName) if tempProfileName else "",
                        "NewDevice": str(tempDevice) if tempDevice else "",
                        "NewSignalName": str(tempSignal).strip() if tempSignal else "",
                        "NewSignalDescription": str(tempDescr).strip() if tempDescr else "",
                        "NewAlarmClass": "",
                        "NewAlarmDescription": "",
                        "NewLogica": str(newLogic) if newLogic else "",

                        "variabileArchetype" : str(tempSharedData["tagVariable"]),
                        "ScriptLabel": str(scriptLabel) if scriptLabel else "",
                        "ScriptData": str(scriptData).replace("{'id'","\n{'id'") if scriptData else "",

                        "registriDupplicati": "",
                        "NewAddress": str(tempSharedData["register"]) + "." + bitIndex,
                        "NewRegister": str(tempSharedData["register"]),
                        "NewBitIndex": bitIndex,
                        "NewDataValueType": sharedCode.fill_DataType(str(tempSharedData["valueType"]), dataTypeDict) ,
                        "NewRegisterType": sharedCode.fill_DataType(str(tempSharedData["registerType"]), registerTypeDict),

                        "SplitTagVariable": SplitTagVariable, 
                        "NormalizedData": " ".join(tempNormData) if tempNormData and isinstance(tempNormData, list) else tempNormData if tempNormData and isinstance(tempNormData, str) else "",
                        "LeftOvers":  str(tempLOvers) if tempLOvers else "",
                        "ExtractedIds": "",
                        "<Note>" : " | ".join(annotazioni) if annotazioni and isinstance(annotazioni, list) else annotazioni if annotazioni and isinstance(annotazioni, str) else "",
                        "<Used Functions>" : " | ".join(funzioniUsate) if funzioniUsate and isinstance(funzioniUsate, list) else funzioniUsate if funzioniUsate and isinstance(funzioniUsate, str) else "",
                        
                        "NewUOM": "",
                        "NewCabina": "",
                        "NewDirezione": ""
                    }
            

            """Salva dati in df"""
            for key, value in tempDict.items():
                df.loc[index, key] = str(value)
        
        shared_data["toDo"] -= 1
        #print(f"\tElaborato part 2:> ({end_index-start_index})\tstart_index: {start_index} - end_index: {end_index}\t\t core:{currentCore}/{maxCpuCores - 1}\t\t ({shared_data["toDo"]})")
        msg = f"\tElaborato (CPU) core:{currentCore}/{maxCpuCores - 1}\t\tProcessi rimasti: ({shared_data["toDo"]})"
        print(msg)
        
        #if(client_id and sio):  
        #    await sio.emit(f'response:{client_id}', msg, to=client_id)
        #    currentProgress = sharedCode.progressYield(maxCpuCores-shared_data["toDo"], maxCpuCores)
        #    await sio.emit(f'response:{client_id}', {"progress": currentProgress}, to=client_id)
        return [df]
    except Exception as e:
        error = f"An error occurred: {str(e)}"
        print(error)
        errorsList.append(error) if error not in errorsList else next
        traceback.print_exc()

def format_json_with_newlines(json_str):
    # Rimuove tutti gli spazi bianchi e newline esistenti
    json_str = ''.join(json_str.split())
    
    formatted = ""
    indent_level = 0
   
    for i, char in enumerate(json_str):
        if char == '{':
            formatted += char + "\n"
            indent_level += 1
            formatted += "  " * indent_level
        elif char == '}':
            formatted += "\n" + "  " * (indent_level-1) + char
            indent_level -= 1
        elif char == ',':
            formatted += char + "\n" + "  " * indent_level
        else:
            formatted += char
           
    return formatted

def quoteCheck(json_str):
    # Prima formattiamo il JSON con newline
    json_str = format_json_with_newlines(json_str)
    
    lines = json_str.split('\n')
    fixed_lines = []
   
    for line in lines:
        if ':' in line:  # Solo per linee che contengono key-value pairs
            key_part, value_part = line.split(':', 1)
           
            # Fix value part if it has unclosed quotes
            value_part = value_part.strip()
            if value_part.count('"') % 2 != 0:  # Se c'è un numero dispari di virgolette
                    # Se inizia con virgoletta ma non finisce con virgoletta
                value_part = value_part + '"'
           
            line = f'{key_part}:{value_part}'
       
        fixed_lines.append(line)
   
    return '\n'.join(fixed_lines)
if __name__ == "__main__":
    """
    Per esecuzione "manuale":
    - accertarsi che upload / download siano corretti
    - aggiungere alla lista 'gallerie' le gallerie che si desidera scaricare & elaborare
    """     
    
    #gallerie = ["Scanzano", "Vetranico"]
     
    skipScriptExtraction = False
    yieldingFlag = False
    
    
    fileAnagrafica = None     
    
    soloScarico = False #Scegli
    chosenDB = "PROD" # Selezionare il database da cui scaricare: PROD oppure QUAL
    
    
    import datetime
    x = datetime.datetime.now()
    timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")
    scriptFoldername = "Scarichi Dragonfly"

    if(soloScarico == False):        
        scriptFoldername = "Scarichi ed Elaborazione Dragonfly"

    UploadsFileFolder = project_root + sharedCode.loadSettings("paths", "uploadsFolder") + f"{timeStamptFolder}\\"
    DownloadsFileFolder = f"{project_root + sharedCode.loadSettings("paths", "downloadsFolder")}{scriptFoldername}\\{timeStamptFolder}\\"


    os.makedirs(DownloadsFileFolder, exist_ok=True)
    os.makedirs(f"{DownloadsFileFolder}\\scriptsFolder\\", exist_ok=True)
     
     
    
    auxName = "dragonfly"  
    currUploadsFolder = UploadsFileFolder#project_root + "\\scripts\\Analisi_Elaborazione\\MappaturaDragonfly\\File Elaborati\\"
    currDownloadsFolder =  DownloadsFileFolder #project_root + "\\scripts\\Analisi_Elaborazione\\MappaturaDragonfly\\File Elaborati\\"

    offsetCPU = 0#int(os.cpu_count()/2)
    CpuCoreNumber = os.cpu_count() - offsetCPU
    CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)
    


    gallerie = ["CORENNO","DORIO"]
    #gallerie = ["Pellegrino", "Collecapretto", "Tescino", "Libero", "Liberati", "Valnerina", "Passignano"]
   
    for galleria in gallerie:
        start = time.time()
        # aggiungere '+"--scarico"' per eseguire solo lo scarico delle gallerie -> galleria.strip() +"--scarico",
        for output in mainCall(galleria.strip(), currUploadsFolder, currDownloadsFolder, fileAnagrafica, auxName, CpuCoreNumber, chosenDB, yieldingFlag = yieldingFlag, soloScarico = soloScarico):
            if(isinstance(output, dict)):
                if("progress" in output.keys()):
                    sharedCode.progress(output["progress"], 100)
                if("stream" in output.keys()):
                    print(f"{output["stream"]}",end = "") if output else next                    
            else:
                print(f"{output}") if output else next
        end = time.time()
        print(f"Tempo elaborazione: {sharedCode.elapsedTimeFormatted(start, end)}")

