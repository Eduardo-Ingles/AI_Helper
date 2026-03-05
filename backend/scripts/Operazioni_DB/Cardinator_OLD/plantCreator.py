#plantCreator

import pymongo
import uuid
from bson import json_util
import traceback
import os
import sys

project_root = os.getcwd()
sys.path.append(project_root)

#from scripts.SharedCode import sharedCode
from scripts.Operazioni_DB.Cardinator_OLD import sharedCode


# genera un random uID di 32 char
def generate_random_id():
    random_uuid = uuid.uuid4()
    id_string = str(random_uuid).replace('-', '')
    id_parts = [
        id_string[:8],   
        id_string[8:12], 
        id_string[12:16],
        id_string[16:20],
        id_string[20:]   
    ]
    return id_parts

    
# lettura nel DB e ritorno della collezione: se ID è specificato ritorna l'elemento trovato, altrimenti tutti gli elementi del DB indicato    
def readDB_wID(client, dbName, collectionName, specificID):
    db = client[dbName]             # Get the collection
    collection = db[collectionName] # Find all the documents in the collection
    if(specificID == ""):
        collezione = collection.find()
    else:
        collezione = collection.find({"_id": specificID})
    return collezione

# creazione e controllo di un uID
def newUniqueID(client):
    flag = True
    random_ID = ""
    collection = readDB_wID(client, "smartscada", "plant", "")
    while(flag == True):
        random_ID = generate_random_id()
        flag = sharedCode.checkUniqueID(client, collection, "-".join(random_ID))
        if(flag == True):
            print("ID già esistente!:", random_ID)
        else:
            random_ID = "-".join(random_ID)
            print("New_ID:", random_ID)
    return random_ID

# crea un nuovo documento 
def newDocument(client, nome, descrizione, titolo, sottotitolo, latitude, longitude, soc,wip, subPlants):
    oggetto = {
                "_id": newUniqueID(client),
                "name": nome,
                "description": descrizione,
                "title": titolo,
                "subtitle": sottotitolo,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "icon": "/assets/images/scada-icons/tunnel.png",
                "iconSource": "system",
                "tenants": [soc],
                "tags": ["633d872e1ca5875ca1bf0014"],
	            "externalIds" : [],
                "subPlants": subPlants,
                "created": float(sharedCode.get_current_time()),    # Double
                "modified": float(sharedCode.get_current_time()),   # Double
                "origin": 0,
                "_class": "com.tecnositaf.smartscada.domain.meta.Plant",
                "externalIds": [],
                "location" : {
                    "roadName" : "",
                    "roadDescription" : "",
                    "pkstart" : 0.0,
                    "pkstop" : 0.0
                },
                "wip" : wip
              }
    return oggetto

# inserisce il documento nel DB
def insert_document(client, dbName, collectionName, document):
    db = client[dbName]
    collection = db[collectionName]
    result = collection.insert_one(document) 
    if result.inserted_id:
        print(f"Document inserted with ID: {result.inserted_id}")
    else:
        print("Failed to insert document")
    return result.inserted_id

# aggiorna subPlants nell'impianto identificato da ID
def update_document_by_id(client, dbName, collection_name, document_id, updated_subPlants):
    try:
        db = client[dbName] 
        collection = db[collection_name]
        filter = {"_id": document_id}
        update_data = {"subPlants": updated_subPlants}
        result = collection.update_one(filter, {"$set": update_data})
        if result.matched_count == 1:
            print("Document updated successfully")
        else:
            print("Document not found or not updated")
    except Exception as e:
        print(f"An error occurred: {str(e)}:", collection_name, document_id, updated_subPlants)
        traceback.print_exc() 


def creaEdInserisci(client, arrayDati):    
    plantID = ""
    nuovoDoc = newDocument(client,
                           arrayDati.nomeGalleria.upper(),
                           arrayDati.plantDescr,
                           arrayDati.plantTitle,
                           arrayDati.plantSubTitle,
                           arrayDati.latitudine,
                           arrayDati.longitudine,
                           arrayDati.SOC, 
                           arrayDati.wip,
                           arrayDati.subPlants)
    plantID = insert_document(client, "smartscada", "plant", nuovoDoc)
    print(json_util.dumps(nuovoDoc, indent = 4))
    return plantID

def trovaImpiantoEsistente(client, nomeGalleria): #aaggiunto 04/03/26
    db = client["smartscada"]
    collection = db["plant"]
    return collection.find_one({"name": nomeGalleria.upper()})


def update_document_by_id_old(client, dbName, collection_name, document_id, updated_subPlants):
    db = client[dbName]  # Replace "your_database" with your actual database name
    collection = db[collection_name]
    # Define the filter to match the document by its _id
    filter = {"_id": document_id}
    # Construct the update data for the "subPlants" field
    update_data = {"subPlants": updated_subPlants}
    # Update the document
    result = collection.update_one(filter, {"$set": update_data})
    # Check the result of the update operation
    if result.matched_count == 1:
        print("Document updated successfully")
    else:
        print("Document not found or not updated")


if __name__ == '__main__':
    0