#subPlantCreator

from bson import ObjectId
from bson.dbref import DBRef
from bson.int64 import Int64
from bson import json_util
import sys
import os
import re

project_root = os.getcwd()
sys.path.append(project_root)

from scripts.Operazioni_DB.Cardinator_OLD import groupCreator
#from scripts.SharedCode import sharedCode
from scripts.Operazioni_DB.Cardinator_OLD import sharedCode


def devicePositionTemplate(tempID):
    #print("ID:",tempID)
    devicePosition = {
                        "deviceId": tempID,
                        "top": "0",
                        "left": "0",
                        "rotation": "0",
                        "scale": "1",
                        "layers": [],
                        "zIndex": "1",
                        "show": True
                    }
    return devicePosition

def newDocument(nome, descrizione, parentId, groupID, plantIcon, devicePosition, order, larghezza, altezza, bg, root, sinottico, templateConfig):
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
          #for inx, cabina in enumerate(tempCabine): 
          for cabina in tempCabine: 
              posCabina = posCabX[cabCounter]
              #if("sx" in cabina.lower()):
              #  posCabina = posCabX[0]
              #if("dx" in cabina.lower()):
              #  posCabina = posCabX[1]
              #
              #if(":" in cabina.lower()):
              #  cabina = cabina.split(":")[0]

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
        #dirTemplateSx = "indicatore_sinistra_AS" if "AS:" in arrDati[index].dirSx else "indicatore_sinistra_SS"
        #direzioneSx = ""
        #direzioneDx = ""
        #if(":" in arrDati[index].dirSx or ":" in arrDati[index].dirDx):            
        #    direzioneSx = arrDati[index].dirSx.split(":")[1].strip() if ":" in arrDati[index].dirSx else arrDati[index].dirSx
        #    direzioneDx = arrDati[index].dirDx.split(":")[1].strip() if ":" in arrDati[index].dirDx else arrDati[index].dirDx
#
        #else:
        #    direzioneSx = arrDati[index].dirSx
        #    direzioneDx = arrDati[index].dirDx
        direzioneSx = arrDati[index].dirSx.split(":")[1].strip() if ":" in arrDati[index].dirSx else arrDati[index].dirSx.strip() if arrDati[index].dirSx else arrDati[index].dirSx
        direzioneDx = arrDati[index].dirDx.split(":")[1].strip() if ":" in arrDati[index].dirDx else arrDati[index].dirDx.strip() if arrDati[index].dirDx else arrDati[index].dirDx
        
        #if(arrDati[index].dirSx.upper().startswith("AS:") or arrDati[index].dirSx.upper().startswith("SA:")):
        #  dirTemplateSx = "indicatore_sinistra_AS" 
        #  dirTemplateDx = "indicatore_destra_AS" 
        #else:
        #  dirTemplateSx = "indicatore_sinistra_SS" 
        #  dirTemplateDx = "indicatore_destra_SS" 
            
            
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


    # ce 1: x: 145      y: 725 
    # ce 2: x: 1790     y: 725 

    # dir_SX: x: 95     y: 85
    # dir_DX: x: 1870   y:695
    


def creaSottoimpianti(client, parentId, arrDati):
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

        tempDoc = newDocument(arrDati[0].nomeGalleria.replace(" ","-") + "-" + arrDati[i].subPlantName,
                              arrDati[i].subPlantDescr,
                              parentId,
                              groupCreator.creaGruppo(client, arrDati, i),  #groupID,
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
       subPlantsIDsArry.append(insert_document(client, "smartscada", "subPlant", tempDocArry[i]))
    return subPlantsIDsArry
        

if __name__ == '__main__':
    x = 0


"""
    customTemplateConfigs: [
      {
        "name": "GROSSETO",
        "template": "indicatore_sinistra_SS",
        "params": {
          "direzione": {
            "type": "static",
            "staticValue": "GROSSETO"
          }
        },
        "actions": {},
        "position": {
          "top": 35,
          "left": 834,
          "rotation": 0,
          "scale": 1,
          "zIndex": 1
        }
      },
      {
        "name": "SIENA",
        "template": "indicatore_destra_SS",
        "params": {
          "direzione": {
            "type": "static",
            "staticValue": "SIENA"
          }
        },
        "actions": {},
        "position": {
          "top": 185,
          "left": 1133,
          "rotation": 0,
          "scale": 1,
          "zIndex": 1
        }
      },
      {
        "name": "ELETTRICO",
        "template": "pop-up",
        "params": {
          "img": {
            "type": "static",
            "staticValue": "parcodellareggia/ventilzione.png"
          }
        },
        "actions": {},
        "position": {
          "top": 871,
          "left": 1017,
          "rotation": 0,
          "scale": 1,
          "zIndex": 1
        }
      },
      {
        "name": "qplc",
        "template": "link-impianto",
        "params": {
          "img": {
            "type": "static",
            "staticValue": "link/link_quadri.png"
          },
          "plant": {
            "type": "static",
            "staticValue": "ARTIFICIALE1-ARTIFICIALE2-ARTIFICIALE3"
          },
          "w": {
            "type": "static",
            "staticValue": "32"
          },
          "tooltip": {
            "type": "static",
            "staticValue": "QPLC"
          },
          "h": {
            "type": "static",
            "staticValue": "32"
          },
          "subPlant": {
            "type": "static",
            "staticValue": "ARTIFICIALE1-ARTIFICIALE2-ARTIFICIALE3-QPLC"
          }
        },
        "actions": {},
        "position": {
          "top": 595,
          "left": 723,
          "rotation": 0,
          "scale": 1,
          "zIndex": 1
        }
      },
      {
        "name": "qmt",
        "template": "link-impianto",
        "params": {
          "img": {
            "type": "static",
            "staticValue": "link/link_quadri.png"
          },
          "plant": {
            "type": "static",
            "staticValue": "ARTIFICIALE1-ARTIFICIALE2-ARTIFICIALE3"
          },
          "w": {
            "type": "static",
            "staticValue": "32"
          },
          "tooltip": {
            "type": "static",
            "staticValue": "QMT"
          },
          "h": {
            "type": "static",
            "staticValue": "32"
          },
          "subPlant": {
            "type": "static",
            "staticValue": "ARTIFICIALE1-ARTIFICIALE2-ARTIFICIALE3-QMT"
          }
        },
        "actions": {},
        "position": {
          "top": 587,
          "left": 889,
          "rotation": 0,
          "scale": 1,
          "zIndex": 1
        }
      },
      {
        "name": "qgbt",
        "template": "link-impianto",
        "params": {
          "img": {
            "type": "static",
            "staticValue": "link/link_quadri.png"
          },
          "plant": {
            "type": "static",
            "staticValue": "ARTIFICIALE1-ARTIFICIALE2-ARTIFICIALE3"
          },
          "w": {
            "type": "static",
            "staticValue": "32"
          },
          "tooltip": {
            "type": "static",
            "staticValue": "QGBT"
          },
          "h": {
            "type": "static",
            "staticValue": "32"
          },
          "subPlant": {
            "type": "static",
            "staticValue": "ARTIFICIALE1-ARTIFICIALE2-ARTIFICIALE3-QGBT"
          }
        },
        "actions": {},
        "position": {
          "top": 629,
          "left": 1159,
          "rotation": 0,
          "scale": 1,
          "zIndex": 1
        }
      },
      
    ]
"""