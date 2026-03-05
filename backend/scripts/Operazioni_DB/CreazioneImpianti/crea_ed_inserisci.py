from bson import ObjectId
from bson.dbref import DBRef
from bson.int64 import Int64
from bson import json_util
import re
import uuid

from backend.scripts.SharedCode import sharedCode, mongoSearch



# ----------------------------------- START COSTANTI -----------------------------------#  

# ----------------------------------- END COSTANTI -----------------------------------# 

def newSpDocument(nome, descrizione, parentId, groupID, plantIcon, devicePosition, order, larghezza, altezza, bg, root, sinottico, templateConfig):
    oggetto = {
                "_id": ObjectId(),
                "name": nome.upper(),
                "description": descrizione,
                "parentId": parentId,
                "group" : DBRef("group", ObjectId(groupID)),
                "renderDevices": True,
                "icon": plantIcon,
                "iconSource": "system",
                "devicePositions": devicePosition,
                "order": order,
                "width": larghezza,#1920,
                "height": altezza,#1200,
                "backgroundImg": bg,#"parcodellareggia/background/bg_qv1.svg",
                "root": root,
                "main": sinottico,
                "hideSubPlantBallMenu": False,
                "customTemplateConfigs": templateConfig,
                "type": "DEFAULT",
                "typeConfig": {
                    "embedded": False
                },
                "created": sharedCode.get_current_time(),
                "modified": sharedCode.get_current_time(),
                "origin": Int64(0),
                "_class": "com.tecnositaf.smartscada.domain.meta.SubPlant"
                }
    return oggetto



def creaSottoimpianti(currDB, parentId, arrDati):
    subPlantsIDsArry = []
    sinottico = "true"
    root = "true"
    flag = False
    devicePositionEmpty = []
    tempDocArry = []
    for i in range(1, len(arrDati)):
        if("ELETTRICO" in arrDati[i].subPlantDescr.upper() and flag == True):
            root = "false"
        else:
            root = "true"

        if(("PAG" in arrDati[i].subPlantName.upper() or "PAG" in arrDati[i].subPlantDescr.upper()) and "1" not in arrDati[i].subPlantName):
            root = "false"
        
        templateConfig = customTemplateBuilder(arrDati, i)

        tempDoc = newSpDocument(arrDati[0].nomeGalleria.replace(" ","-") + "-" + arrDati[i].subPlantName,
                              arrDati[i].subPlantDescr,
                              parentId,
                              creaGruppo(currDB, arrDati, i),  #groupID,
                              arrDati[i].icona,
                              devicePositionEmpty,
                              arrDati[i].posizione,
                              arrDati[i].larghezza,
                              arrDati[i].altezza,
                              arrDati[i].pathBG,
                              root, 
                              sinottico,
                              templateConfig
                              )
        tempDocArry.append(tempDoc) if tempDoc not in tempDocArry else next

        if("ELETTRICO" in arrDati[i].subPlantDescr.upper() ):
            flag = True
        if("SINOTTICO" in arrDati[i].subPlantDescr.upper()):
            sinottico = "false"
    
    for i in range (len(tempDocArry)):
       print(json_util.dumps(tempDocArry[i], indent = 4))
       subPlantsIDsArry.append(insert_document(currDB, "subPlant", tempDocArry[i]))
    return subPlantsIDsArry



def linkBuilder(arrDati, index):
    posX = 200
    posY = 200
    plantName = arrDati[0].nomeGalleria#"MONACO"
    tempTemplateHolder = []
    electricPlantFlag = False
    for data in arrDati:
        #if(data.subPlantDescr == "Impianto Elettrico" or (data.posizione and data.posizione > 10)):
        #    electricPlantFlag = True

        #if(electricPlantFlag == True):
        if(data.subPlantDescr and ("elettrico" in data.subPlantDescr.lower() or (data.icona and "electric_icon.png" in data.icona.lower())) and "Impianto Elettrico" != data.subPlantDescr):
                  
          nomeQuaddro = data.subPlantName.replace(plantName + "-","")#"QBT-CE-01"
          
          toolTip = nomeQuaddro#"QBT CE-01"
          subPlant = plantName + "-"+ nomeQuaddro if not nomeQuaddro.startswith(plantName) else nomeQuaddro #"MONACO-QBT-CE-01"

          protoLink = {
                    "name": nomeQuaddro,
                    "template": "link-impianto",
                    "params": {
                    "img": {
                        "type": "static",
                        "staticValue": "link/link_quadri.png"
                    },
                    "plant": {
                        "type": "static",
                        "staticValue": plantName
                    },
                    "w": {
                        "type": "static",
                        "staticValue": "32"
                    },
                    "tooltip": {
                        "type": "static",
                        "staticValue": toolTip
                    },
                    "h": {
                        "type": "static",
                        "staticValue": "32"
                    },
                    "subPlant": {
                        "type": "static",
                        "staticValue": subPlant
                    }
                    },
                    "actions": {},
                    "position": {
                    "top": posY,
                    "left": posX,
                    "rotation": 0,
                    "scale": 1,
                    "zIndex": 1
                    }
            }
          tempTemplateHolder.append(protoLink) if protoLink not in tempTemplateHolder else next
          posX += 100
          if(posX > 1000):
              posX = 200
              posY += 100 

    return tempTemplateHolder if (len(tempTemplateHolder) != 0) else None



def customTemplateBuilder(arrDati, index):
    tempArr = []
    nomeGalleria = arrDati[0].nomeGalleria.replace(" ","-")
    nomeSubPlnt = arrDati[0].nomeGalleria.replace(" ","-") + "-IMPIANTO-ELETTRICO"

    if(arrDati[index].subPlantName == "IMPIANTO-ELETTRICO"):
      links = linkBuilder(arrDati, index)

      if(links):
        tempArr += links

    if(arrDati[index].cabine != None):
        tempCabine = re.split(r"[,;/]", str(arrDati[index].cabine.strip()))
        cabCounter = 0
        posCabX = [1790, 145]
        if(arrDati[index].cabine != "" or str(arrDati[index].cabine.strip()) != "nan"):
          for cabina in tempCabine: 
              posCabina = posCabX[cabCounter]
              

              templateCabina = "riquadro_cabina"          
              templatename = nomeGalleria + "-" + cabina.replace(" ", "-")
              if("uscite di sicurezza" in arrDati[index].subPlantDescr):
                templateCabina = "riquadro_cabina_bypass"

              customCabina = {"name": templatename, 
                              "template": templateCabina, 
                              "params": {"plant": {"type": "static", "staticValue": nomeGalleria},
                                         "nome": {"type": "static", "staticValue": cabina},
                                         "subPlant": {"type": "static", "staticValue": nomeSubPlnt}}, 
                              "actions": {},
                              "position": {"top": 725, "left": posCabina, "rotation": 0, "scale": 1, "zIndex": 0}
                              }

              tempArr.append(customCabina) if customCabina not in tempArr else next
    
    if(arrDati[index].dirSx != None and arrDati[index].dirDx != None):
        
        direzioneSx = arrDati[index].dirSx.split(":")[1].strip() if ":" in arrDati[index].dirSx else arrDati[index].dirSx.strip() if arrDati[index].dirSx else arrDati[index].dirSx
        direzioneDx = arrDati[index].dirDx.split(":")[1].strip() if ":" in arrDati[index].dirDx else arrDati[index].dirDx.strip() if arrDati[index].dirDx else arrDati[index].dirDx
        
            
        dirTemplateSx = "indicatore_sinistra_SS" if arrDati[index].dirSx.startswith("SS:") else "indicatore_sinistra_AS"
        dirTemplateDx = "indicatore_destra_SS" if arrDati[index].dirDx.startswith("SS:")  else "indicatore_destra_AS"    


        customDirSx = {"name": direzioneSx, 
                        "template": dirTemplateSx, 
                        "params": {"direzione": {"type": "static", "staticValue": direzioneSx}}, 
                        "actions": {}, 
                        "position": {"top": 91, "left": 85, "rotation": 0, "scale": 1, "zIndex": 1}
                        }
        
        tempArr.append(customDirSx) if customDirSx not in tempArr else next

        customDirDx = {"name": direzioneDx, 
                        "template": dirTemplateDx, 
                        "params": {"direzione": {"type": "static", "staticValue": direzioneDx}}, 
                        "actions": {}, 
                        "position": {"top": 695, "left": 1870, "rotation": 0, "scale": 1, "zIndex": 1}
                        }

        tempArr.append(customDirDx) if customDirDx not in tempArr else next

    return  tempArr




def newGroupDocument(nome, descrizione):
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



    
def creaGruppo(currDB, arrDati, i):
    groupID = ""
    print("crea Gruppi")
    tempGroupName = (arrDati[0].nomeGalleria.replace(" ","-") + "-" + arrDati[i].subPlantName).upper()
    newGroupDoc = newGroupDocument(tempGroupName, tempGroupName)
    print(json_util.dumps(newGroupDoc, indent = 4))
    groupID = insert_document(currDB, "group", newGroupDoc)
    return groupID



def newDocument(tipo:str, **kwargs): 
    tempDocument = None
    if(tipo == "gruppo"):
        tempDocument =  {
                "_id" : ObjectId(),
                "name" : kwargs.get("name").upper(),
                "groupContext" : "Device",
                "description" : kwargs.get("descrizione"),
                "created" : sharedCode.get_current_time(),     # Long
                "modified" : sharedCode.get_current_time(),    # Long
                "origin" : Int64(0),                # Long
                "_class" : "com.tecnositaf.smartscada.domain.meta.Group"
            }

    elif(tipo == "subplant"):
        tempDocument = {
            "_id": ObjectId(),
            "name": kwargs.get("name").upper(),
            "description": kwargs.get("descrizione"),
            "parentId": kwargs.get("parent"),
            "group" : DBRef("group", ObjectId(kwargs.get("groupid"))),
            "renderDevices": True,
            "icon": kwargs.get("icon"),
            "iconSource": "system",
            "devicePositions": kwargs.get("position"),
            "order": kwargs.get("order"),
            "width": kwargs.get("larghezza"),#1920,
            "height": kwargs.get("altezza"),#1200,
            "backgroundImg": kwargs.get("bg"),#"parcodellareggia/background/bg_qv1.svg",
            "root": kwargs.get("root"),
            "main": kwargs.get("sinottico"),
            "hideSubPlantBallMenu": False,
            "customTemplateConfigs": kwargs.get("template"),
            "type": "DEFAULT",
            "typeConfig": {
                "embedded": False
            },
            "created": sharedCode.get_current_time(),
            "modified": sharedCode.get_current_time(),
            "origin": Int64(0),
            "_class": "com.tecnositaf.smartscada.domain.meta.SubPlant"
            }
    
    return tempDocument



def newDocument_group(name:str, descrizione:str): 
    if(name and name != ""):
        tempDocument =  {
                "_id" : ObjectId(),
                "name" : name.upper(),
                "groupContext" : "Device",
                "description" : descrizione,
                "created" : sharedCode.get_current_time(),     # Long
                "modified" : sharedCode.get_current_time(),    # Long
                "origin" : Int64(0),                # Long
                "_class" : "com.tecnositaf.smartscada.domain.meta.Group"
            }
        return tempDocument



def newDocument_subPlant(name:str, descrizione:str, parentId:ObjectId, groupid:str, icon:str, devicePositions:list, order:int, larghezza:int, altezza:int, bg:str, **kwargs):
    root = kwargs.get("root") if "root" in kwargs.keys() else True
    sinottico = kwargs.get("sinottico") if "sinottico" in kwargs.keys() else False
    hidden = kwargs.get("hidden") if "hidden" in kwargs.keys() else False
    customTemplate = []
    tempDocument = {
            "_id": ObjectId(),
            "name": name.upper(),
            "description": descrizione,
            "parentId": parentId,
            "group" : DBRef("group", ObjectId(groupid)),
            "renderDevices": True,
            "icon": icon,
            "iconSource": "system",
            "devicePositions": devicePositions,
            "order": order,
            "width": larghezza,#1920,
            "height": altezza,#1200,
            "backgroundImg": bg,#"parcodellareggia/background/bg_qv1.svg",
            "root": root ,
            "main": sinottico,
            "hideSubPlantBallMenu": hidden,
            "customTemplateConfigs": customTemplate,
            "type": "DEFAULT",
            "typeConfig": {
                "embedded": False
            },
            "created": sharedCode.get_current_time(),
            "modified": sharedCode.get_current_time(),
            "origin": Int64(0),
            "_class": "com.tecnositaf.smartscada.domain.meta.SubPlant"
            } 
        


def newDocument_Plant(plantData, currDB):
    new_uuid = mongoSearch.newUniqueID(currDB)
    if(new_uuid and plantData and plantData["nomeGalleria"] != ""):
        newPlant = {
                "_id": new_uuid,
                "name": plantData["nomeGalleria"],
                "description": plantData["plantDescr"],
                "title": plantData["plantTitle"],
                "subtitle": plantData["plantSubTitle"],
                "coordinates": {
                    "latitude": plantData["latitudine"],
                    "longitude": plantData["longitudine"]
                },
                "icon": "/assets/images/scada-icons/tunnel.png",
                "iconSource": "system",
                "tenants": [plantData["SOC"]],
                "tags": ["633d872e1ca5875ca1bf0014"],
	            "externalIds" : [],
                "subPlants": [],
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
               "wip": plantData["wip"],
              }
        
        
        #newPlantID = insert_document(currDB, "plant", newPlant)
        #if(newPlantID):
        #    print(json_util.dumps(newPlant, indent = 4))
        #    return newPlantID
        #else:
        #    return None



# inserisce il documento nel DB
def insert_document(currDB, collectionName, document):
    collection = currDB[collectionName]
    result = collection.insert_one(document) 
    if result.inserted_id:
        print(f"Document inserted with ID: {result.inserted_id}")
    else:
        print("Failed to insert document")
    return result.inserted_id



def creaSubPlants(inputData, **kwargs):
    0
    #if(isinstance(inputData, dict)):
    #    print(inputData.keys())
    #elif(isinstance(inputData, list)):
    #    print(inputData[0].keys())
    
    #for subPlants in inputData:
    #    nome = kwargs.get("galleria").replace(" ","-") + "-" + subPlants["subPlantName"]
    #    descr = nome 
    #    doc = newDocument(tipo = "gruppo", name = nome, descrizione = descr)
        

