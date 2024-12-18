from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, APIRouter, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import subprocess
import threading
import asyncio
import uuid
import json
import logging
from typing import List, Dict, Union

import importlib.util
import socketio

from fastapi_socketio import SocketManager

import pymongo

import os, sys, time, datetime

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, mongoSearch


# ----------------------------------- START COSTANTI -----------------------------------#  

x = datetime.datetime.now()
timeStamptFolder = (f"{x.day}-{x.month}-{x.year}")


LOG_FILENAME = project_root + f'/backend/tmp/logging_{timeStamptFolder}.out'
os.makedirs(project_root + "/backend/tmp/", exist_ok=True)
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

UPLOAD_DIR = project_root + sharedCode.loadSettings("paths", "uploadsFolder") #+ f"{timeStamptFolder}\\"
DOWNLOAD_DIR = project_root + sharedCode.loadSettings("paths", "downloadsFolder") #+ f"{timeStamptFolder}\\"

#os.makedirs(DOWNLOAD_DIR + f"{timeStamptFolder}\\", exist_ok=True)
os.makedirs(UPLOAD_DIR + f"{timeStamptFolder}\\", exist_ok=True)

SCRIPTS_DIR = project_root + sharedCode.loadSettings("paths", "scripts")
TEMPLATES_DIR = project_root + sharedCode.loadSettings("paths", "templates")
STATICDATA_DIR = project_root + sharedCode.loadSettings("paths", "staticData")
LOGS_DIR = project_root + sharedCode.loadSettings("paths", "logs")

DBDUMPS_DIR = project_root + sharedCode.loadSettings("paths", "dbDump")

TUTORIAL_DIR = project_root + sharedCode.loadSettings("paths", "tutorials")
SETTINGS_DIR = project_root + sharedCode.loadSettings("paths", "settingsFolder")

ROOT_PATH = os.path.join(project_root, "backend")

listaGallerie = "listaGallerie.json"    # gestire generazione automatica -> attualmente è un file statico

raw_scriptsList = sharedCode.loadSettings("files", "raw_scriptsList")
scriptsList = sharedCode.loadSettings("files", "scriptsList")

gallerieSmartScada_Quality = []
gallerieSmartScada_Prod = []

gallerieDragonfly_Quality = []
gallerieDragonfly_Prod = []

#activeTasks = {}
if(sharedCode.fileExists(path = STATICDATA_DIR, file = f"activeTasks-{sharedCode.timeStamp()}.json")):
    activeTasks = sharedCode.rw_file(path = STATICDATA_DIR, file = f"activeTasks-{sharedCode.timeStamp()}.json")
else:
    activeTasks = {}
client_to_socket = {}

# ------------------------------------ END COSTANTI ------------------------------------# 
app = FastAPI()
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #http://0.0.0.0:4200 < angular server / port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Socket.IO server with detailed configuration
sio = socketio.AsyncServer(
    async_mode="asgi", 
    cors_allowed_origins="*",
    ping_timeout=30,  
    ping_interval=10,
    #logger=True,  # Enable detailed logging
    #engineio_logger=True
)

# Add SocketIO middleware to FastAPI app
socket_app = socketio.ASGIApp(
    sio, 
    other_asgi_app=app, 
    socketio_path="/socket.io/"  # Explicitly set the path
)


# routes #

# Define Socket.IO events
@sio.event
async def connect(sid, environ):
    client_id = environ.get('HTTP_CLIENT_ID')  # Pass client ID from the client, if available
    client_to_socket[client_id] = sid
    print(f"Client connected: sid={sid}, client_id={client_id}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


@app.get("/api/file-tree/{directory}")
async def get_file_tree(directory: str):
    """
    Crea la struttura ad albero della cartella download/upload.
    """
    base_path = DOWNLOAD_DIR
    if(directory == 'uploads'):
        base_path = UPLOAD_DIR
    if(directory == 'tutorials'):
        base_path = TUTORIAL_DIR
    if(directory == 'settings'):
        base_path = SETTINGS_DIR        
    if(directory == 'dumps'):
        base_path = STATICDATA_DIR   
    if(directory == 'root'):
        base_path = ROOT_PATH
        
        
    #base_path = UPLOAD_DIR if directory == 'uploads' else DOWNLOAD_DIR
    
    def scan_directory(path: str) -> List[Dict[str, Union[str, List]]]:
        try:
            items = []
            for entry in os.scandir(path):
                item = {
                    'name': entry.name,
                    'path': entry.path,
                    'type': 'directory' if entry.is_dir() else 'file',
                    'children': scan_directory(entry.path) if entry.is_dir() else []
                }
                items.append(item)
            return items
        except PermissionError:
            return []
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Directory not found")    
    return scan_directory(base_path)


@app.get("/api/download/{filename:path}")
async def download_file(filename: str):
    """
    Download a del file selezionato dalla cartella uploads/downloads.
    """
    if(project_root not in filename):
        filename = os.path.join(project_root, "backend", "downloads", "File di riferimento & Esempio", filename) # forzatura -> gestire meglio anche altri casi
        #print(f"project_root + filename: {filename}")
    file_path = filename
    #print(f"file_path: {file_path}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    print(f"file_path: {file_path}")
    return FileResponse(
        path=file_path, 
        filename=os.path.basename(filename), 
        media_type='application/octet-stream'
    )


@app.get("/api/getGallerieList")
async def getGallerieList():
    return sharedCode.rw_file(path = TEMPLATES_DIR, file = listaGallerie)


@app.get("/api/getScriptList")
async def getScriptsList():
    return sharedCode.rw_file(path = STATICDATA_DIR, file = scriptsList)


# Endpoint single file upload
@app.post("/api/upload-single")
async def upload_single(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR + f"{timeStamptFolder}\\", file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return {"message": f"File '{file.filename}' caricamento avvenuto con successo!"}


# Endpoint multiple file uploads
@app.post("/api/upload-multiple")
async def upload_multiple(files: List[UploadFile] = File(...)):
    uploaded_files = []
    for file in files:
        file_location = os.path.join(UPLOAD_DIR + f"{timeStamptFolder}\\", file.filename)
        with open(file_location, "wb") as f:
            f.write(await file.read())
        uploaded_files.append(file.filename)
    return {"message": f"{len(uploaded_files)} - {len(uploaded_files)} file caricati con successo!", "files": uploaded_files}


@app.post("/api/runScript")
async def eseguiScript(requestData: Request): 
    client_host = requestData.client.host    
    clientname = ipBinding(client_host)
    #print(f"client_host: {client_host} -> clientname {clientname}")
    data = await requestData.json()
    allScripts = sharedCode.rw_file(path = STATICDATA_DIR, file = scriptsList)
    for group in allScripts:
        for script in group["scripts"]:
            if(script["viewName"] == data["script"]):
                threadId = threading.get_ident()
                client_id = data.get("userId", None)
                if(not clientname):
                    clientname = client_host
                else:
                    data["clientName"] = clientname
                if(client_id):
                    thread = threading.Thread(target=thread_target, args=(client_id, clientname, threadId, data, script))
                    thread.start()
    return {"client_id": client_id}


def thread_target(client_id, clientName, threadId, data, script):
    asyncio.run(execute_scriptv(client_id, clientName, threadId, data, script))
    
    
async def execute_scriptv(client_id, clientName, threadId, data, script):
    global activeTasks    
    tempTask = {"id": f"{client_id}", "clientName": clientName, "task": script["name"], "message": [], "progress": 0, "data": data, "timestamp": sharedCode.timeStamp(fullDate = True), "links": []}        
    activeTasks[f"{client_id}"] = tempTask
    #activeTasks["data"] = data
    userTask = {}
    script_path = os.path.join(SCRIPTS_DIR, script["name"])
    spec = importlib.util.spec_from_file_location("script_module", script_path)
    script_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script_module)
    try:
        for output in script_module.process_files(sio, client_id, data, script): 
            response = None            
            if(isinstance(output, dict) and ("progress" in output.keys() or "links" in output.keys())):
                response = output
                if("progress" in output.keys()):                    
                    if(client_id):          
                        await sio.emit(f'response:{client_id}', response, to=client_id)
                    tempTask["progress"] = output["progress"] + 0.5   # offset per compensare un errore non ancora gestito     
                    
                if("links" in output.keys() and output["links"]):
                    tempTask["links"] += output["links"]
                    
                    if(client_id):  
                        await sio.emit(f'response:{client_id}', output, to=client_id)
                    print(output)                                  
                    
            elif(isinstance(output, dict) and "status" in output.keys()):
                if(client_id):  
                    await sio.emit(f'response:{client_id}', output, to=client_id)
                    
            elif(isinstance(output, dict) and "stream" in output.keys()):  
                if(client_id):  
                    await sio.emit(f'response:{client_id}', output, to=client_id)
                    tempTask["message"].append(output)    
                    #tempTask["message"] += output["stream"]
            else:                  
                response = {'data': output}
                tempTask["message"].append({"message": output})  
                #tempTask["message"] += output
                          
                if(response):
                    if(client_id):          
                        await sio.emit(f'response:{client_id}', response, to=client_id)
                    else:              
                        await sio.emit('response', {'data': output})
            activeTasks[f"{client_id}"] = tempTask           

        sharedCode.rw_file(path = STATICDATA_DIR, file = f"activeTasks-{sharedCode.timeStamp()}.json", data = activeTasks)
    except Exception as e:   
        print(f"ERRORE: {e}")     
        if(client_id):          
            await sio.emit(f'response:{client_id}', {'data': str({str(e)})}, to=client_id)
        else:              
            await sio.emit('response', {'data': {str(e)}})            
        logging.debug(f'{e}')
    

@app.get("/api/getalltasks/")
async def getAllTasks():
    return activeTasks


# funzioni varie #
def generateRawScriptsList():            
    """Prepare il file 'raw_scriptsList.json' """
    script_list = sharedCode.get_script_list(SCRIPTS_DIR)
    if(sharedCode.fileExists(path = STATICDATA_DIR, file = raw_scriptsList)):
        newList = sharedCode.rw_file(path = STATICDATA_DIR, file = raw_scriptsList, mode = "load")
    else:
        newList = []
    for script in script_list:
        foundFlag = False
        newItem = {
                    "name": script, 
                    "viewName": "_descrizione_", 
                    "tooltip": "",
                    "gruppo": "",
                    "templateFile": "",
                    "requirements": 
                    {
                        "database" : False,
                        "collection" : False,
                        "subCollection" : False,
                        "text" : False,
                        "file" : False
                    },
                    "options":{
                        "disabled": True,
                        "img": ""
                    }
                }
        for item in newList:
            if(item["name"] == script):
                foundFlag = True
                
        newList.append(newItem) if not foundFlag and newItem not in newList else next
    sharedCode.rw_file(path = STATICDATA_DIR, file = raw_scriptsList, data = newList, mode = "save")
    generateScriptsList()
    
    
def generateScriptsList():
    """Partendo da 'generateRawScriptsList & raw_scriptsList' > genera 'scriptsList.json'  """
    gruppi = []
    listaScript = sharedCode.rw_file(path = STATICDATA_DIR, file = raw_scriptsList)
    for script in listaScript:
        foundFlag = False
        if(script["gruppo"] != ""):
            tempDict = {"name": script["gruppo"], "includedScripts": [], "scripts": []}
            for gruppo in gruppi:
                if(script["options"]["disabled"] == False and gruppo["name"] == script["gruppo"]):
                    foundFlag = True
            if(not foundFlag):
                gruppi.append(tempDict) if tempDict not in gruppi else next
    
    for gruppo in gruppi:
        for script in listaScript:
            if(script["gruppo"] != "" and gruppo["name"] == script["gruppo"] and script["options"]["disabled"] == False):
                gruppo["includedScripts"].append(script["viewName"]) if script["viewName"] not in gruppo["includedScripts"] else next
                foundFlag = False
                for groupScript in gruppo["scripts"]:
                    if(groupScript["name"] == script["name"]):
                        foundFlag = True
                if(not foundFlag):
                    gruppo["scripts"].append(script) if script not in gruppo["scripts"] else next
                    ## CHECK DOUBLES !!!!
    if(gruppi):
        sharedCode.rw_file(path = STATICDATA_DIR, file = scriptsList, data = gruppi, mode = "save")
    
    

    
    
############### < TO CLEAN > ###############

@app.get("/api/getScriptTutorial/{scriptName}")
async def getScriptTutorial(scriptName: str):
    if(not scriptName or "default" in scriptName):
        return sharedCode.rw_file(path = TUTORIAL_DIR, file = f"default.txt")
    else:        
        return sharedCode.rw_file(path = TUTORIAL_DIR, file = f"{scriptName}.txt")



def ipBinding(clientIp): 
    ipBindings = sharedCode.rw_file(path = STATICDATA_DIR, file = "ipsbindings.json") 
    if(ipBindings):
        for ipB in ipBindings:
            if(ipB["ip"] != "" and clientIp and ipB["ip"] == clientIp):
                return ipB["name"]
            

@app.post("/api/getSpecificListaGallerie")
async def getSpecificListaGallerie(requestData: Request):
    """
    Gestire l'update automatico dei file in 'dbDump' !
    """
    data = await requestData.json()
    subCollection = None
    db = data.get("db")
    if(db == "Quality"):
        dbAddress = "MongoQualityClient"
    if(db == "Produzione"):
        dbAddress = "MongoProductionClient"
        
    mainCollection = data.get("collection")
    if(mainCollection == "DragonFly"):
        subCollection = "scada_system"
        mainCollection = "scada"
    if(mainCollection == "SmartScada"):
        mainCollection = "smartscada"
        subCollection = "plant"
    
    tempList = []
    currFileName = f"{mainCollection} - {dbAddress}.json"
    loadedData = sharedCode.rw_file(path = DBDUMPS_DIR, file = currFileName)
    if(subCollection and not loadedData):
        print("Generating...")
        client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
        results = mongoSearch.readCollectionData(client[mainCollection], subCollection)
        for result in results:
            print(result["name"])
            tempList.append(result["name"]) if result["name"] not in tempList else next
        tempList.sort()
        print(sharedCode.rw_file(path = DBDUMPS_DIR, file = currFileName, data = {"data": tempList}, mode = "save"))
    if(loadedData):
        #print("Loading...", loadedData)
        tempList = loadedData["data"]
    return {"message": tempList}



@sio.event
async def message(sid, data):
    print(f"Message from {sid}: {data}")
    await sio.emit('response', {'data': 'Message received'}, to=sid)
    


    
active_tasks = {}

activeClients = []

tasksStatus = {}


endFlag = False
current_progress = 0


@app.get("/api/getScriptOptions/{scriptName}")
async def getScriptOptions():
    0
    
@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    global endFlag
    print(current_progress)
    await websocket.accept()
    await websocket.send_json({"progress": current_progress, "fine": endFlag})
    await websocket.close()
    

progressValue = 0

@app.get("/api/getProgress")
async def getProgress():
    await asyncio.sleep(1)
    time.sleep(1)
    global progressValue
    if(progressValue == 100):
        progressValue = 0
    progressValue += 1
    return {"progress": progressValue}


@app.websocket("/ws/getProgress")
async def startUpMessage(websocket: WebSocket):
    await websocket.accept()
    try:
        for i in range(100): 
            await websocket.send_text(str(i))
    except WebSocketDisconnect:
        0


@app.get("/api/getScriptStatus/{client_id}")
async def getScriptProgress(client_id: str):
    if(client_id in activeTasks.keys()):        
        return activeTasks[client_id]["message"]


@app.post("/api/sendPrompt")
async def post_test(request: Request):
    data = await request.json()  # This reads the raw JSON body
    print("Received data:", data)
    return {"message": f"Received data: {data}"}


def execute_script(script_path, client_id):
    process = subprocess.Popen(
        ['python3', script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    active_tasks[client_id] = process

    for line in process.stdout:
        print(f"[{client_id}] {line.strip()}")

    process.stdout.close()
    process.wait()
    del active_tasks[client_id]


if __name__ == "__main__":        
    generateRawScriptsList()
    generateScriptsList()

    import uvicorn
    porta = 5001
    ##uvicorn.run(app, host = sharedCode.get_ip(), port = porta)#, log_level="debug")
    uvicorn.run(socket_app, host = sharedCode.get_ip(), port = porta)#, log_level="debug")

