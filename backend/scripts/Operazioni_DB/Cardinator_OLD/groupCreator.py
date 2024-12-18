# groupCreator

import pymongo
from bson import ObjectId 
from bson.int64 import Int64
from bson import json_util

import os
import sys

project_root = os.getcwd()
sys.path.append(project_root)

#from scripts.SharedCode import sharedCode
from scripts.Operazioni_DB.Cardinator_OLD import sharedCode


def readDB_wID(client, dbName, collectionName, specificID):
    db = client[dbName]             # Get the collection
    collection = db[collectionName] # Find all the documents in the collection
    if(specificID == ""):
        collezione = collection.find()
    else:
        collezione = collection.find({"_id": ObjectId(specificID)})
    return collezione


def newDocument(nome, descrizione):
    oggetto =  {
                    "_id" : ObjectId(),
                    "name" : nome.upper(),
                    "groupContext" : "Device",
                    "description" : descrizione,
                    "created" : sharedCode.get_current_time(),     # Long
                    "modified" : sharedCode.get_current_time(),    # Long
                    "origin" : Int64(0),                # Long
                    "_class" : "com.tecnositaf.smartscada.domain.meta.Group"
                }
    return oggetto


def insert_document(client, dbName, collectionName, document):
    db = client[dbName]
    collection = db[collectionName] # Insert the document into the collection
    result = collection.insert_one(document) # Check if the insertion was successful
    if result.inserted_id:
        print(f"Document inserted with ID: {result.inserted_id}")
    else:
        print("Failed to insert document")
    #client.close()
    return result.inserted_id


def creaDocumento(client, nome, descrizione):
    newGroupDoc = newDocument(nome, nome)
    currentID = insert_document(client, "smartscada", "group", newGroupDoc)
    return currentID


def creaGruppi(client, arrDati):
    ids = []
    print("crea Gruppi")
    for i in range(1,len(arrDati)):
        tempGroupName = (arrDati[0].nomeGalleria.replace(" ","-") + "-" + arrDati[i].subPlantName).upper()
        newGroupDoc = newDocument(tempGroupName, tempGroupName)
        print(json_util.dumps(newGroupDoc, indent = 4))
        #ids.append(insert_document(client, "smartscada", "group", newGroupDoc))
    return ids


def creaGruppo(client, arrDati, i):
    groupID = ""
    print("crea Gruppi")
    tempGroupName = (arrDati[0].nomeGalleria.replace(" ","-") + "-" + arrDati[i].subPlantName).upper()
    newGroupDoc = newDocument(tempGroupName, tempGroupName)
    print(json_util.dumps(newGroupDoc, indent = 4))
    groupID = insert_document(client, "smartscada", "group", newGroupDoc)
    return groupID


if __name__ == '__main__':
    0
