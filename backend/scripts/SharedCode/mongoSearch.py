
from bson import ObjectId 
import uuid
import re


def readCollectionData(currentDB, collectionName:str, **kwargs):
    """    
    Ricerca su db per id/nome/descrizione all'interno della collezione indicata
    - collectionName es: plant, subplants
    - kwargs: id, name, description
    """
    id = kwargs.get("id")
    name = kwargs.get("name")
    description= kwargs.get("description")
    
    collection = currentDB[collectionName] # Find all the documents in the collection
    if(not id and not name and not description):
        result = collection.find()         #find() returns a cursor
    elif(id and not name and not description):
        if(isinstance(id,str) and "-" in id):
            result = collection.find_one({"_id": id})
        else:
            result = collection.find_one({"_id": ObjectId(id)})
    elif(not id and name and not description):
        if("regex" in kwargs.keys()):
            #result = collection.find({"name": {"$regex": name.upper()}}) 
            result = collection.find({"name": {"$regex": re.compile(name, re.IGNORECASE)}}) 
        else:
            result = collection.find_one({"name": name}) 
    elif(not id and not name and description):
        result = collection.find_one({"description": description}) 
    return result


def findCollectionData(currentDB, collectionName:str, **kwargs):
    """    
    Ricerca su db per id/nome/descrizione all'interno della collezione indicata
    - collectionName es: plant, scada_tag
    - kwargs: key & value / querry / returrnList / regex
    """
    result = None
    results = []
    key = kwargs.get("key")
    value = kwargs.get("value")
    querry = kwargs.get("querry")
    returnList = kwargs.get("returnList")
    collection = currentDB[collectionName]
    
    if(key and value and not querry):        
        fquery = { key: value}        
        if("regex" in kwargs.keys()):
            result = collection.find({key: {"$regex": re.compile(value, re.IGNORECASE)}}) 
        else:
            result = collection.find(fquery)
            
    elif(querry and not key and not value):  
        result = collection.find({"$and": [querry]})
        
    if(result and returnList):
        for x in result:
            results.append(x) if x not in results else next
        return results        
    elif(result and not returnList):
        return result
          

def updateOne(currentDB, collectionName:str, **kwargs):
    """kwargs:
    - key + oldValue & newValue
    - !not working! old_key + oldValue & new_key +newValue !not working!
    - searchQuerry & updateQuerry
    """
    key = kwargs.get("key")
    oldValue = kwargs.get("oldValue")
    newValue = kwargs.get("newValue")
    
    searchQuerry = kwargs.get("searchQuerry")
    updateQuerry = kwargs.get("updateQuerry") 
    
    collection = currentDB[collectionName]
    success = False
    if(key and oldValue and not searchQuerry and not updateQuerry):
        myquery = { key: oldValue }
        newvalues = { "$set": { key: newValue} }
        #collection.update_one(myquery, newvalues)
        result = collection.update_one(myquery, newvalues)
        if result.matched_count == 1:
            success = True
            
        return f"{collectionName}: {myquery} --> {newvalues}"
    elif(searchQuerry and updateQuerry and not key and not oldValue):
        myquery = {"$and": [searchQuerry]}
        newvalues = { "$set": updateQuerry }
        #collection.update_one(myquery, newvalues)
        result = collection.update_one(myquery, newvalues)
        if result.matched_count == 1:
            success = True
        msg = (f"{collectionName}: {myquery} --> {newvalues}")
        return {"flag": success, "message":  msg}
    
       
def generate_random_id():
    """
    genera un random uID di 32 char
    """
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


def newUniqueID(currentDB):
    """
    creazione e controllo di un uID
    """
    currCollection = currentDB["plant"].find()
    random_ID = generate_random_id()
    if(checkUniqueID(currCollection, "-".join(random_ID))):
        random_ID = "-".join(random_ID)
        return random_ID
    else:
        print("ID già esistente!:", random_ID)
        return None


def checkUniqueID(currCollection, curr_ID):
    """
    verifica se l'ID è univoco nella collection indicata
    """
    collectionArray = loadIds(currCollection)
    for i in range(len(collectionArray)):
        if(collectionArray[i] == curr_ID):
            return None
    return curr_ID
    
    
def loadIds(collezione):
    """
    carica tutti gli ID in un array per confronto
    """
    IdsArray = []
    for document in collezione:
        IdsArray.append(f"{document['_id']}") if document['_id'] not in IdsArray else next
    return IdsArray  