from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from multiprocessing import Manager
import traceback 

import copy
from collections import OrderedDict
from datetime import datetime
import pandas as pd
import time, json

import os, sys

import numpy as np
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import requests
import hashlib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

project_root = os.getcwd()
sys.path.append(project_root)


from backend.scripts.SharedCode import sharedCode, normalizzatore, applyRules, rulesDefiner, localLLM



# ----------------------------------- START COSTANTI -----------------------------------#  

dataArrayForTags = ["ALR_Collection AlrType_Collection:ALR",
                    "MIS_Collection MeasureTypes_Collection:MIS",  
                    "ST_Collection Status_Collection:ST",
                    "CMD_Collection:CMD",
                    "PAR_Collection:PAR"]


SheetsName = ["WIP", "Import"]

uploadsFolderPath = project_root + sharedCode.loadSettings("globalSettings", "uploadsFolderPath") 
dataTypeDict = sharedCode.loadSettings("globalSettings", "dataType") 
registerTypeDict = sharedCode.loadSettings("globalSettings", "registerTypes") 

dictFolder = project_root + sharedCode.loadSettings("globalSettings", "dictionaryFolderPath") 
dictFileName = sharedCode.loadSettings("globalSettings", "mainDictionary")
auxFilesFolder = project_root + sharedCode.loadSettings("globalSettings", "auxFolderPath") 

splitRule = sharedCode.loadSettings("globalSettings", "splitRule")

rulesPath = project_root + sharedCode.loadSettings("globalSettings", "rulesFolderPath")
rawRulesFile =  sharedCode.loadSettings("globalSettings", "raw_descrRules") 
newRulesFile =  sharedCode.loadSettings("globalSettings", "descrRules")

colonneInput = sharedCode.loadSettings("analisiSorgenteSettings", "colonneIN")
filePrefix = sharedCode.loadSettings("analisiSorgenteSettings", "filePrefix")
fileSuffix = sharedCode.loadSettings("analisiSorgenteSettings", "fileSuffix")

dictionary = (sharedCode.rw_file(path = dictFolder, file = dictFileName))
indexedAliasArray = normalizzatore.aliasIndexArray(dictionary)

currRules = copy.copy(rulesDefiner.loadRulesData(rulesPath, rawRulesFile, newRulesFile))

encoder = SentenceTransformer("all-mpnet-base-v2")#'all-MiniLM-L6-v2')
#encoder = SentenceTransformer('all-MiniLM-L6-v2')

tfidf = TfidfVectorizer(analyzer='word', token_pattern=r'\b\w+\b')



sysPrompt = """You are an AI assistant designed to provide detailed, step-by-step responses. Your outputs should follow this structure:
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
                
                Your task is to compare the <rawData> with <matches> and return the best matching 'Nome dispositivo'in JSON format.
                Start comparing 'DESCRIZIONE' and 'NormalizedData' from <rawData> with 'Nome dispositivo' and 'NormalizedData' from <matches>.
                Return the best matching 'Nome dispositivo' as json. Never return 'NormalizedData'.
                <example>
                    Compare this: 
                    <reference_string>
                    {"DESCRIZIONE": "QVE2 -V3 DX CONTATTORE BY-PASS AVVIATORE", "NormalizedData": "BYP V3 DX CONTATT START QVE 2 21K3", "NOME SPECIFICO /NUMERAZIONE": "21K3"}
                    <reference_string>
                    with:
                    <matches_List>
                    {'index': 150, 'data': {'Nome dispositivo': 'SANGIULIANO-QVE1-CONT-8K2-V4DX-CE-01', 'NormalizedData': 'CE01 CONTATT CE'}}
                    {'index': 151, 'data': {'Nome dispositivo': 'SANGIULIANO-QVE1-CONT-22K3-V4DX-CE-01', 'NormalizedData': 'CE01 CONTATT CE'}}
                    {'index': 149, 'data': {'Nome dispositivo': 'SANGIULIANO-QVE1-CONT-8K1-V4DX-CE-01', 'NormalizedData': 'CE01 CONTATT CE'}}
                    {'index': 147, 'data': {'Nome dispositivo': 'SANGIULIANO-QVE1-CONT-8K2-V3SX-CE-01', 'NormalizedData': 'CE01 CONTATT CE'}}
                    {'index': 161, 'data': {'Nome dispositivo': 'SANGIULIANO-QVE1-SEL-AUTO-MAN-8S1-V4DX-CE-01', 'NormalizedData': 'CE01 SELETT AUTO MAN CE'}}
                    {'index': 161, 'data': {'Nome dispositivo': 'SANGIULIANO-QVE1-CONT-21K3-CE-01', 'NormalizedData': 'CE01 CONTATT CE'}}
                    <matches_List>

                    and return: 
                    <extracted_data>
                    {'Nome dispositivo': 'SANGIULIANO-QVE1-CONT-21K3-CE-01'}
                    <extracted_data>
                <example>

                ! Remember that the matches could be wrong. Check the ID inside each string and compare them. !
                Return an empty json {'Nome dispositivo': 'None'} if there is no match.
                """


# ----------------------------------- END COSTANTI -----------------------------------# 


def mainCall(fileSorgente:str, filePath:str, fileAnagrafica, auxName:str, CPUCores:int):
    
    def multyCoreProcessing(df):
        try:            
            if(checkColumns(df)):
                chunks = sharedCode.defineChunkSize(CPUCores, len(df))

                with Manager() as manager:            
                    shared_data = manager.dict()
                    shared_data["sharedData"] = manager.list()
                    shared_data['dataHolder'] = manager.list()
                    shared_data["cpuCounter"] = 0
                    shared_data["toDo"] = 0

                    #print(f"multiprocessing part 1...{chunks}")     
                    #with multiprocessing.Pool(processes = CPUCores) as pool:
                    #    resultsElab = pool.starmap(
                    #        elaboraChunk,
                    #        [
                    #            (CPUCores, df, start, end, shared_data)
                    #            for start, end in chunks
                    #        ],
                    #    )                
                    #
                    #print("\nMergind df....")        
                    #processed_dfs = [pd.concat(result) for result in resultsElab]
                    #df = pd.concat(processed_dfs)
                    #print("Riempimento colonne...") 
                    #df2 = sharedCode.fillImportColumns(df, "df2", "WIP")
                    #dfs = {"WIP": df, "Import": df2}
                    #outFileName = f"{filePrefix}{fileSorgente}"
                    #print(f"Salvataggio: {sharedCode.rw_xlsx(path = filePath, file = outFileName, df = dfs)}") 
                    print(f"{filePrefix}{fileSorgente}")
            else:
                print(f"Colonnne essenziali mancanti !!!")
        except Exception as e:
            print(f"An error occurred: {str(e)}:")
            traceback.print_exc()

            
    sharedCode.currentTimeHMS("start")
    rowsAn = None
    dfA = None
    embeddings_Anagrafica = None
    if(fileAnagrafica and fileAnagrafica != "" ): # 
        includedColumns = ["Nome Galleria", "Impianto", "Tipologia Dispositivo", "Nome dispositivo", "Locale tecnico", "Corsia", "Direzione", "NormalizedData"]

        print(f"Preparazione anagrafica: {fileAnagrafica}...")
        dfA = sharedCode.rw_xlsx(path = filePath, file = fileAnagrafica, sheet = "Dispositivi")
        dfA["NormalizedData"] = None
        dfA = dfA[includedColumns]
        print("NormalizedData fileAnagrafica...")
        for index, row in dfA.iterrows():
            dfA.loc[index, "NormalizedData"] = str(normalizzatore.normalizzaDati(str(row["Nome dispositivo"]), dictionary, splitRule=splitRule, aliasArray=indexedAliasArray))
            dfA.loc[index, "NormalizedData"] += f" {" ".join(list(set(str(row["Nome dispositivo"]).split("-"))))}".replace("-"," ")
        sharedCode.progress(index, len(dfA))
        dfA = dfA[["Nome dispositivo", "NormalizedData"]]
        # Converting each row to JSON format using apply and filtering by includedColumns
        rowsAn = dfA.apply(lambda row: json.dumps(
            {col: str(row[col]) for col in includedColumns if col in dfA.columns}), axis=1).tolist()
        print(f"{dfA.head()}\n {dfA.columns}")
        fileAnagrafica = fileAnagrafica+".xlsx" if not fileAnagrafica.endswith(".xlsx") else fileAnagrafica
        embeddings_Anagrafica = load_or_create_embeddings(dfA, filePath + fileAnagrafica)

    #for item in rowsAn:
    #    input(f"{item}")
    
    #dfRf = sharedCode.rw_xlsx(path = filePath, file = fileAnagrafica, sheet = "Dispositivi")
    print("loading df...")
    df = sharedCode.rw_xlsx(path = filePath, file = fileSorgente) 
    print("NormalizedData...")
    df["NormalizedData"] = None
    for index, row in df.iterrows():
        df.loc[index, "NormalizedData"] = str(normalizzatore.normalizzaDati(f"{str(row["DESCRIZIONE"])} {str(row["QUADRO"])} {str(row["DISPOSITIVO"])} {str(row["NOME SPECIFICO /NUMERAZIONE"])}", dictionary, splitRule=splitRule, aliasArray=indexedAliasArray))
        df.loc[index, "NormalizedData"] += str(list(set(" ".join(list(set(f"{str(row["NOME SPECIFICO /NUMERAZIONE"])} {str(row["NOME CABINA"])}".split("-")))).split())))
    
    #rowsRif = dfRf.apply(lambda x: ', '.join(x.astype(str)), axis=1).tolist()
    #rows = df.apply(lambda x: ', '.join(x.astype(str)), axis=1).tolist()
    #rows = df.apply(lambda row: json.dumps({col: str(row[col]) for col in df.columns}), axis=1).tolist()
    #includedColumn = ["QUADRO", "DISPOSITIVO", "NOME SPECIFICO /NUMERAZIONE", "DESCRIZIONE"]
    print("apply lambda...")
    includedColumn = ["DESCRIZIONE", "NormalizedData"]
    #rows = df.apply(lambda row: json.dumps(
    #    {col: str(row[col]) for col in includedColumn if col in df.columns}), axis=1).tolist()
    
    rows = df.apply(lambda row: json.dumps(
    {col: str(row[col]) for col in includedColumn if col in df.columns}), axis=1).tolist()

    # Remove duplicates by converting to a set and back to a list
    rows = list(set(rows))

    #print(f"{rowsAn}\nlen: {len(rowsAn)}")

    #for row in rows:
    #    print(row)
    #embeddings = []
    #for _, row in dfRf.iterrows():
    #    text = " ".join(str(val) for val in row)
    #    embedding = encoder.encode(text)
    #    embeddings.append(embedding)
    #
    #embeddings = np.array(embeddings)
    
    #embeddings = load_or_create_embeddings(dfRf, filePath + "Normalized_profili_smartScada clean 2.xlsx")

   # embeddings_anagrafica = load_or_create_embeddings(dfRf, filePath + "Normalized_profili_smartScada clean 2.xlsx")

    print("next...")
    finalResults = []
    for idx, roo in enumerate(rows):        
        search_results = search_excel(embeddings_Anagrafica, dfA, roo)
        # Use llama.cpp to process the query and search results    
        #prompt = f"Query: {roo}\n\nRelevant information:\n" + "\n".join(search_results)
        prompt = f"Compare 'NormalizedData' from: <rawData>{str(roo)}<rawData> and return a json with the best matching data from: <matches>{str(search_results)}<matches>."
        print(f"{idx}|{len(rows)} >> {roo} <<\n")
        for search_result in search_results:
            print(f"{search_result}")
        print(f"\n")
        #result = testFunction(prompt)
        inputData = {"userPrompt": prompt, "systemPrompt": sysPrompt, "temperatura": 0.43}
        startLLM = time.time()  
        result1 = localLLM.LlmCall(inputData)
        #
        ##inputData["userPrompt"] = f"Check if {result} found in {search_results} and return the best matching 'Nome dispositivo' in json format."
        #inputData = {"userPrompt": f"{prompt}. Compare 'NormalizedData' fields. return a json with the best matching 'Nome dispositivo'. ", "systemPrompt": sysPrompt}
        #result2 = localLLM.LlmCall(inputData)
        #
        #inputData["userPrompt"] = f"compare those result1 and result2 and pick the best.\n result1: {str(result1)} & result2: {str(result2)}. return a json with 'Nome dispositivo'"
        inputData["userPrompt"] = "Extract the JSON data in this format {'Nome dispositivo': 'Extracted_device_name'} from "+str(result1)+". Ensure the formatting is correct. Do not add any other comments or suggestions."
        inputData["systemPrompt"] = "Extract the json data and ensure the format is correct. Example json: {'Nome dispositivo': 'Extracted_device_name'}. Do not add any other comments. If there's no correct JSON DATA {'Nome dispositivo': 'None'} "
        inputData["temperatura"]= 0.05
        result = localLLM.LlmCall(inputData)
        endLLM = time.time()
        print(f"{result}\n\n{"{:.2f}".format(endLLM-startLLM)}s")
        print("############################\n")
        #print(f"{result}\n\n{roo}\n")
        #input("---")
        finalResults.append(f"{roo},{result}") if f"{roo},{result}" not in finalResults else next

        if(idx == 20):
            sharedCode.rw_file(file = "test.txt", data = finalResults)
    sharedCode.rw_file(file = "test.txt", data = finalResults)

    #multyCoreProcessing(df)
    
    sharedCode.currentTimeHMS("end")


def load_or_create_embeddings(df, excel_path):    
    def get_file_hash(file_path):
        """Generate a hash of the file contents."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    """Load embeddings if they exist, otherwise create and save them."""
    file_hash = get_file_hash(excel_path)
    embedding_file = f"embeddings_{file_hash}.npy"
    
    if os.path.exists(embedding_file):
        print("Loading existing embeddings...")
        return np.load(embedding_file)
    
    print("Creating new embeddings...")
    embeddings = []
    for _, row in df.iterrows():
        text = " ".join(str(val) for val in row)
        embedding = encoder.encode(text)
        embeddings.append(embedding)
    
    embeddings = np.array(embeddings)
    np.save(embedding_file, embeddings)
    print(f"Embeddings saved to {embedding_file}")
    return embeddings


def search_excel(embeddings, df, query, top_k=5):
    # Encode the query
    query_embedding = encoder.encode(query)    
    # Compute cosine similarity
    similarities = np.dot(embeddings, query_embedding) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding))    
    # Get top k results
    top_indices = np.argsort(similarities)[-top_k:][::-1]    
    results = []
    seen = set()  # To keep track of unique results
    for idx in top_indices:
        row = df.iloc[idx]
        #result = f"Similarity: {similarities[idx]:.4f}"
        result = f"{idx}:> " + "{"
        row_tuple = tuple(row.items())  # Convert row to hashable type
        if row_tuple not in seen:
            seen.add(row_tuple)
            for col, val in row.items():
                #result += f" | {col}: {val}"
                result += ""+f"{col}: {val}, "
            if(result.endswith(", ")):
                result = result[:len(result)-2]
            result += "}"
            results.append(result) if result not in results else next    
    return results


def search_excel_lastWorking(embeddings, df, query, top_k=6, similarity_threshold=0.37):
    query_embedding = encoder.encode(query)
    
    # Compute cosine similarity
    similarities = np.dot(embeddings, query_embedding) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding))
    
    # Get top k results above the similarity threshold
    top_indices = np.where(similarities > similarity_threshold)[0]
    top_indices = top_indices[np.argsort(similarities[top_indices])][::-1][:top_k]
    results = []
    seen = set()    
    for idx in top_indices:
        row = df.iloc[idx]
        row_key = tuple(row[df.columns.drop('NormalizedData')].items())  # Exclude NormalizedData from uniqueness check
        
        if row_key not in seen:
            seen.add(row_key)
            #result = {
            #    "index": idx,
            #    #"similarity": similarities[idx],
            #    "data": row.to_dict()
            #}
            #results.append(result)    
            result = f"{idx}> {row.to_dict()}"
            results.append(result)
    return results


def search_excel_oldy(embeddings, df, query, top_k=6, semantic_weight=0.2, similarity_threshold=0.30):
    def preprocess_text(text):
        return ' '.join(text.split())  # Simple whitespace normalization
    
    query_dict = eval(query)
    query_text = ' '.join(str(v) for v in query_dict.values())
    query_embedding = encoder.encode(query_text)
    
    # Compute semantic similarity
    semantic_similarities = np.dot(embeddings, query_embedding) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding))
    
    # Compute TF-IDF similarity
    df_text = df['NormalizedData'].apply(preprocess_text)
    tfidf_matrix = tfidf.fit_transform(df_text)
    query_tfidf = tfidf.transform([preprocess_text(query_text)])
    tfidf_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
    
    # Combine similarities
    combined_similarities = semantic_weight * semantic_similarities + (1 - semantic_weight) * tfidf_similarities
    
    # Get top k results above the similarity threshold
    top_indices = np.where(combined_similarities > similarity_threshold)[0]
    top_indices = top_indices[np.argsort(combined_similarities[top_indices])][::-1][:top_k]
    results = []
    seen = set()    
    for idx in top_indices:
        row = df.iloc[idx]
        row_key = tuple(row[df.columns.drop('NormalizedData')].items())
        
        if row_key not in seen:
            seen.add(row_key)
            #result = {
            #    "index": idx,
            #    "similarity": combined_similarities[idx],
            #    "data": row.to_dict()
            #}
            result = f"{idx}> {row.to_dict()}"
            results.append(result)
    
    return results



def checkColumns(df):
    print("\nCheck colonne...")
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


def elaboraChunk(CPUCore, df, start_index, end_index, shared_data):
    0
    
    
    #rulesResult = applyRules.applyRules(currRules, tempNormData, dictionary, indexedAliasArray, device = normDevice)


if __name__ == "__main__":
    #currFileFolder =  project_root + "\\scripts\\Analisi_Elaborazione\\MappaturaDragonfly\\File Elaborati\\"
    offsetCPU = 0#int(os.cpu_count()/2)
    CpuCoreNumber = os.cpu_count() - offsetCPU
    CpuCoreNumber = (1 if CpuCoreNumber < 1 else CpuCoreNumber)
    
    fileAnagrafica = "xx-xxx-xx_Anagrafica San Giuliano_2024-08-26_rev1_v1"
    
    skipScriptExtraction = True
    auxName = "dragonfly"
    chosenDB = "P"

    Sorgenti = ["Galleria San Giuliano e Casola_Esemplificativo Mappa PLC TO ELABORATE"]


    for sorgente in Sorgenti:
        start = time.time()
        
        mainCall(sorgente, uploadsFolderPath, fileAnagrafica, auxName, CpuCoreNumber)
        end = time.time()
        minuti = int((end - start)/60)
        secondi = int((end - start) - (minuti *60))
        if(secondi < 10):
            secondi = "0" + str(secondi)
        #print("(total: {:.3f} s)".format(end - start), "({:.2f}) min".format((end - start)/60) )
        print("Tempo elaborazione: {:.2f} secondi\t-\t".format(end - start), f"{minuti}.{secondi} minuti")
