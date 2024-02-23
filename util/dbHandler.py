from pymongo import MongoClient
import json
from bson import json_util

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]

def insertChatMessage(message: str):
    chat_collection = db["chat"]
    decoded_message = message.decode()
    chat_collection.insert_one({"username":"Guest","message":decoded_message}) #Mongodb automatically creates unique IDs for each message

def getAllChatMessages():
    chat_collection = db["chat"]
    all_chat_messages = chat_collection.find()


    # documents = list(all_chat_messages)
    # for document in documents:
    #     document['_id'] = str(document['_id'])


    list_of_messages = []
    for message in all_chat_messages:
        message['id'] = str(message['_id'])

        #Create dictionary for each message so that we can have a list of objects to be converted to JSON and returned to the user
        chat_message_dictionary = {
            "message": message["message"],
            "username": message["username"],
            "id": message['_id']
        }

        list_of_messages.append(chat_message_dictionary)
    json_messages = json.dumps(list_of_messages)

    #return json.dumps(documents, default=json_util.default)
    return json_messages