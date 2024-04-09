from pymongo import MongoClient
import json
from bson import json_util

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]
chat_collection = db["chat"]
users_collection = db["users"]

#Helper function to increment message ID
def get_next_message_id():
    counter_doc = db.message_counter.find_one_and_update(
        {"_id": "message_id"},
        {"$inc": {"value": 1}},
        return_document=True
    )
    return counter_doc["value"]

#---insertChatMessage---#
#  -Takes a username and a message. 
#  -Creates a collection of counters for message # if it doesnt exist
#  -Puts the message with the id and username into the chat collection
def insertChatMessage(username, message):
    print("&&&&& message in insertChatMessage: " + str(type(message)))
    #Create a collection for counters if it doesn't exist
    if "message_counter" not in db.list_collection_names():
        db["message_counter"].insert_one({"_id": "message_id", "value": 0})
    
    #message is a JSON string. We need JSON.loads() to turn it python dictionary compatible
    #python_message_dictionary = json.loads(message)
    #python_message = python_message_dictionary['message']
    message_id = get_next_message_id()
    chat_collection.insert_one({"_id": message_id, "username":username, "message":message}) #Mongodb automatically creates unique IDs for each message
    
    #Return the chat message that we just inserted into the database. (AO1 purposes)
    json_message = json.dumps({"_id": message_id, "username":username, "message":message})
    return json_message

def getAllChatMessages():
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
    query = {"_id": id}
    target_message = chat_collection.find_one(query)
    if target_message:
        json_message = json.dumps(target_message)
        return json_message
    else:
        return None
    
def deleteChatMessage(id):
    query = {"_id": id}
    chat_collection.delete_one(query)
    return None

def update_document(id, new_message_document):
    # Check if the document with the given ID exists
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
    
def register_user(username, salt, salted_hashed_password):
    users_collection.insert_one({
            "username": username,
            "salt": salt,
            "salted_hashed_password": salted_hashed_password
        })
    return

def get_user_credentials(username):
    query = {"username": username}
    return users_collection.find_one(query) # This is a dictionary of DB fields

def insert_token(username, hashed_auth_token):
    users_collection.update_one({"username": username}, {"$set": {"auth_token": hashed_auth_token}})
    return

def insert_xsrf_token(hashed_auth_token, xsrf_token):
    users_collection.update_one({"auth_token": hashed_auth_token}, {"$set": {"xsrf_token": xsrf_token}})
    return

#---get_username_from_token---#
#   A helper function that returns a username associated with a given auth token.
#   Returns none if no associated username exists.
def get_username_from_token(hashed_auth_token):
    query = {"auth_token": hashed_auth_token}
    user_document = users_collection.find_one(query)

    if user_document:
        return user_document["username"]
    else:
        return None
    
#---delete_auth_token---#
#  -Deletes the auth token after looking it up.
#  -Returns True if auth token was valid and token was deleted from DB. False otherwise.
def delete_auth_token(hashed_auth_token):
    # Update the user document to remove the auth token
    query = {"auth_token": hashed_auth_token}
    user_document = users_collection.find_one(query)

    if user_document:
        users_collection.update_one({"auth_token": hashed_auth_token}, {"$unset": {"auth_token": ""}})
        return True
    else:
        return False
    
#---get_username_from_chat---#
#  -Retrieves the username associated with a given chat message id
def get_username_from_chat(message_id):
    query = {"_id": message_id}
    chat_document = chat_collection.find_one(query)
    return chat_document["username"]

#---get_xsrf_token---#
#  -Retrieves the xsrf token associated with the user's auth token.
#  -Returns that xsrf token if it exists, None if it doesn't exist
def xsrf_token_check(hashed_auth_token):
    query = {"auth_token": hashed_auth_token}
    user_document = users_collection.find_one(query)
    print("$$$$$ user_document when xsrf check is: " + str(user_document))

    if user_document:
        xsrf_token = user_document.get("xsrf_token")
        if xsrf_token is not None:
            return xsrf_token # If user exist and has xsrf token
        else:
            return None # For user doesn't have xsrf token
    else:
        return "0" # For user doesn't exist for auth token
    
def xsrf_token_from_username(username):
    query = {"username": username}
    user_document = users_collection.find_one(query)
    if user_document:
        return user_document["xsrf_token"]
    else:
        return None
    
#This function checks if a filename already exists in our chat collection (for image purposes)
#It returns False if file doesn't exist, true if it does
def filename_checker(filename):
    # Query the database to check if the filename exists
    query = {"filename": filename}
    result = chat_collection.find_one(query)
    if result is not None:
        return True
    else:
        return False