from pymongo import MongoClient

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]

def insertChatMessage(message: str):
    chat_collection = db["chat"]
    chat_collection.insert_one({"username":"Guest","message":message}) #Mongodb automatically creates unique IDs for each message