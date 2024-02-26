from pymongo import MongoClient
import json
from bson import json_util

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]

#Helper function to increment message ID
def get_next_message_id():
    counter_doc = db.message_counter.find_one_and_update(
        {"_id": "message_id"},
        {"$inc": {"value": 1}},
        return_document=True
    )
    return counter_doc["value"]

def insertChatMessage(message):
    #Create a collection for counters if it doesn't exist
    if "message_counter" not in db.list_collection_names():
        db["message_counter"].insert_one({"_id": "message_id", "value": 0})
    
    chat_collection = db["chat"]
    #message is a JSON string. We need JSON.loads() to turn it python dictionary compatible
    python_message_dictionary = json.loads(message)
    python_message = python_message_dictionary['message']
    message_id = get_next_message_id()
    chat_collection.insert_one({"_id": message_id, "username":"Guest","message":python_message}) #Mongodb automatically creates unique IDs for each message
    
    #Return the chat message that we just inserted into the database. (AO1 purposes)
    json_message = json.dumps({"_id": message_id, "username":"Guest","message":python_message})
    return json_message

def getAllChatMessages():
    chat_collection = db["chat"]
    all_chat_messages = chat_collection.find()


    # documents = list(all_chat_messages)
    # for document in documents:
    #     document['_id'] = str(document['_id'])


    list_of_messages = []
    for message in all_chat_messages:

        #Create dictionary for each message so that we can have a list of objects to be converted to JSON and returned to the user
        chat_message_dictionary = {
            "message": message["message"],
            "username": message["username"],
            "_id": str(message['_id'])
        }

        list_of_messages.append(chat_message_dictionary)
    #print(list_of_messages)
    json_messages = json.dumps(list_of_messages)

    #return json.dumps(documents, default=json_util.default)
    return json_messages

def getOneChatMessage(id):
    chat_collection = db["chat"]
    query = {"_id": id}
    target_message = chat_collection.find_one(query)
    if target_message:
        json_message = json.dumps(target_message)
        return json_message
    else:
        return None
    
def deleteChatMessage(id):
    chat_collection = db["chat"]
    query = {"_id": id}
    chat_collection.delete_one(query)
    return None

def update_document(id, new_message_document):
    # Check if the document with the given ID exists
    chat_collection = db["chat"]
    query = {"_id": id}
    old_message = chat_collection.find_one(query)
    if old_message is None:
        return False  # Document message not found
    else:
        # Process the incoming document data (bytes) by decoding bytes to string
        if isinstance(new_message_document, bytes):
            new_message_document = new_message_document.decode('utf-8')

        # Parse the JSON string into a dictionary
        try:
            new_message_document = json.loads(new_message_document)
        except json.JSONDecodeError:
            # Handle invalid JSON format
            return False

        # Update the existing document with the new message document
        new_message = new_message_document["message"]
        new_username = new_message_document["username"]
        chat_collection.update_one({"_id": id}, {"$set": {"message": new_message, "username": new_username}})
        return True  # Document message updated successfully