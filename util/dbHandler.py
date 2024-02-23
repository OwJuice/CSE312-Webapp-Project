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
    decoded_message = message.decode() #This is a JSON string. We need JSON.loads()
    python_message_dictionary = json.loads(decoded_message)
    python_message = python_message_dictionary['message']
    message_id = get_next_message_id()
    chat_collection.insert_one({"_id": message_id, "username":"Guest","message":python_message}) #Mongodb automatically creates unique IDs for each message

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
    print(list_of_messages)
    json_messages = json.dumps(list_of_messages)

    #return json.dumps(documents, default=json_util.default)
    return json_messages