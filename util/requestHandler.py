from util.request import Request
import util.dbHandler as dbHandler
#Importing as dbHandler will prevent me from having to type util.dbHandler.<function> everytime I wanna use a function from that file
# so I can just do dbHandler.<function>. I could have imported all (*), but this would reduce code clarity as I wouldn't know where a function
# came from when calling it.
import os
import util.auth as auth
import secrets
import hashlib
import bcrypt


#===requestHandler.py===#
#  -This file holds functions that handle building responses to requests.

#---buildResponse Function---#
#   A helper function to build responses to be sent from the client to the server after receiving a request
#   Takes a response code, a MIME type, and the content as strings
#   Decodes those arguments, finds the length of the data, and puts together the whole response and returns as bytes
#   Currently only works with 200 and 404 responses
#   NOTE: .decode converts bytes to string, .encode converts string to bytes
#---#
def buildResponse(responseCode, mimeType, content) :
    content_bytes = content.encode()
    content_len = len(content_bytes)
    response = "HTTP/1.1 " + responseCode + "\r\n"
    response += "X-Content-Type-Options: nosniff\r\n"
    response += "Content-Type: " + mimeType + "\r\n"    # Concatenate: "; charset=utf-8" after the mimeType for text
    response += "Content-Length: " + str(content_len)
    response += "\r\n\r\n"
    response += content
    encoded_response = response.encode()

    return encoded_response

#---buildImageResponse Functon---#
#   Same as buildResponse, except it doesn't encode the content because images are already in bytes
#---#
def buildImageResponse(responseCode, mimeType, content) :
    content_len = len(content)
    response = "HTTP/1.1 " + responseCode + "\r\n"
    response += "X-Content-Type-Options: nosniff\r\n"
    response += "Content-Type: " + mimeType + "\r\n"
    response += "Content-Length: " + str(content_len)
    response += "\r\n\r\n"
    response = response.encode() + content

    return response

#---buildRedirectResponse Function---#
#   A helper function to build redirect responses after receiving a request
#   Takes a protocol(http version), response code, and a url to redirect to
#   Also takes a list of cookies if provided.
#   Content length is 0 since no content is being sent
#   NOTE: .decode converts bytes to string, .encode converts string to bytes
#---#
def buildRedirectResponse(protocol, responseCode, redirect_url, cookies=None) :
    response = protocol + " " + responseCode + "\r\n"
    response += "Content-Length: 0" + "\r\n"
    response += "Location: " + redirect_url + "\r\n"

    # Add cookies if provided
    if cookies:
        for cookie in cookies:
            response += "Set-Cookie: " + cookie + "\r\n"

    response += "\r\n"  # End of headers
    return response.encode()

#---fileReader---#
#   A helper function that just takes in a file as a string, opens it, reads it, and returns the entire file as a string
def fileReader(filename):
    f = open(filename, "r")
    readfile = f.read()

    return readfile

#---imageReader---#
#   A helper function that just takes in an image file as a string, opens it, reads it in bytes, and returns the file in a byte array
def imageReader(filename):
    f = open(filename, "rb")
    readfile = f.read()

    return readfile

#---htmlInjectionPreventer---#
#   A helper function that takes in a string and returns a string that escapes html characters
def htmlInjectionPreventer(string):
    safe_string = string.replace("&", "&ammp")
    safe_string = safe_string.replace("<", "&lt")
    safe_string = safe_string.replace(">", "&gt")
    return safe_string

def server_root(request:Request):
    req_cookies = request.cookies

    readfile = fileReader("./public/index.html")
    visits_counter = int(req_cookies.get("visits", 0))
    visits_counter += 1 #Increment visits counter by 1
    visits_str = str(visits_counter)
    readfile = readfile.replace("{{visits}}", visits_str)
    encoded_file = readfile.encode()
    length_of_file = str(len(encoded_file))
    return ("HTTP/1.1 200 OK\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: " + length_of_file + "\r\nSet-Cookie: visits=" + visits_str + "; Max-Age=3600\r\n\r\n").encode() + encoded_file

def server_js(request:Request):
    readfile = fileReader("./public/functions.js")
    return buildResponse("200 OK", "text/javascript; charset=utf-8", readfile)

def server_webrtc_js(request:Request):
    readfile = fileReader("./public/webrtc.js")
    return buildResponse("200 OK", "text/javascript; charset=utf-8", readfile)

def server_css(request:Request):
    readfile = fileReader("./public/style.css")
    return buildResponse("200 OK", "text/css; charset=utf-8", readfile)

def server_favicon(request:Request):
    readfile = imageReader("./public/favicon.ico")
    return buildImageResponse("200 OK", "image/x-icon", readfile)

def server_post_chat_msgs(request:Request):
    req_body = request.body
    req_cookies = request.cookies

    #Determine whether or not the user is successfully logged in
    auth_token_cookie = req_cookies.get("auth_cookie")
    if auth_token_cookie:
        #Hash the retrieved cookie to see if it matches the stored hash
        auth_token_to_check = hashlib.sha256(auth_token_cookie.encode()).hexdigest()
        username = dbHandler.get_username_from_token(auth_token_to_check)
        # See if the username exists in database
        if not username:
            username = "Guest"

    else:
        # Auth token cookie doesn't exist
        username = "Guest"
    #At this point, the username is the one associated with auth token from DB
    #If no auth token or no user associated, then username is "Guest"
    

    #Escape HTML before inserting msg into database
    chat_message = req_body.decode()
    safe_message = htmlInjectionPreventer(chat_message)
    message_document = dbHandler.insertChatMessage(username, safe_message)
    return buildResponse("201 Created", "application/json; charset=utf-8", message_document)

def server_get_chat_msgs(request:Request):
    chat_messages = dbHandler.getAllChatMessages() #chat_messages is a list of json objects
    return buildResponse("200 OK", "application/json; charset=utf-8", chat_messages)

def server_get_chat_msg(request:Request):
    req_path = request.path

    stripped_path = req_path.strip("/")
    message_path = stripped_path.split("/") #Message_path is a string at this point, including the id
    #Try to convert the message to an int, if it doesn't work, then send a 404 error because the id wasn't int compatible
    try:
        message_id = int(message_path[1])
        #print("--------------THE MESSAGE_ID IS: " + str(message_id))
    except ValueError:
        # Handle the case where message_id_str is not a valid integer
        return buildResponse("404 Not Found", "text/plain; charset=utf-8", "Message ID is not valid >:(")
    else:
        target_message = dbHandler.getOneChatMessage(message_id)
        if target_message != None:
            return buildResponse("200 OK", "application/json; charset=utf-8", target_message)
        else:
            return buildResponse("404 Not Found", "text/plain; charset=utf-8", "Message not found :(")

def server_delete_chat_msg(request:Request):
    req_path = request.path

    stripped_path = req_path.strip("/")
    message_path = stripped_path.split("/") #Message_path is a string at this point, including the id
    #Try to convert the message to an int, if it doesn't work, then send a 404 error because the id wasn't int compatible
    try:
        message_id = int(message_path[1])
        #print("--------------THE MESSAGE_ID IS: " + str(message_id))
    except ValueError:
        # Handle the case where message_id_str is not a valid integer
        return buildResponse("404 Not Found", "text/plain; charset=utf-8", "Message ID is not valid >:(")
    else:
        dbHandler.deleteChatMessage(message_id)
        return "HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n".encode()
    
def server_update_chat_msg(request:Request):
    req_path = request.path
    req_body = request.body

    stripped_path = req_path.strip("/")
    message_path = stripped_path.split("/") #Message_path is a string at this point, including the id
    #Try to convert the message to an int, if it doesn't work, then send a 404 error because the id wasn't int compatible
    try:
        message_id = int(message_path[1])
        #print("--------------THE MESSAGE_ID IS: " + str(message_id))
    except ValueError:
        # Handle the case where message_id_str is not a valid integer
        return buildResponse("404 Not Found", "text/plain; charset=utf-8", "Message ID is not valid >:(")
    else:
        update_check = dbHandler.update_document(message_id, req_body)
        if update_check is True:
            updated_message = dbHandler.getOneChatMessage(message_id)
            return buildResponse("200 OK", "application/json; charset=utf-8", updated_message)
        else:
            return buildResponse("404 Not Found", "text/plain; charset=utf-8", "Message not found :(")

def server_image(request:Request):
    req_path = request.path

    image_path = req_path.split("/")
    #If path is: "/public/image/cat.jpg"
    #image_path looks like: ['', 'public', 'image', 'cat.jpg']

    #Check if image path is invalid path
    if len(image_path) < 4 or image_path[3] == "":
        return buildResponse("400 Bad Request", "text/plain", "Invalid image path")

    image_name = image_path[3]  
    #image_name contains the name of image & image type like "cat.jpg" or "elephant.jpg"
    image_file_path = "public/image/" + image_name

    #See if requested image exists
    if not os.path.exists(image_file_path):
        return buildResponse("404 Not Found", "text/plain", "Image not found")
    
    readfile = imageReader(image_file_path)
    return buildImageResponse("200 OK", "image/jpeg", readfile)

#---server_register---#
#   -Parameters: A request object
#   -Returns: 302 Found redirect (sends user back to homepage)
#   -Objective: Store usernames and salted hash of password into database.
#    The password must pass criteria using validate_password method or reg fails.
#    No failed reg message required.
def server_register(request:Request):
    req_http = request.http_version

    #Extract username and password
    credential_list = auth.extract_credentials(request)
    username = credential_list[0]
    password = credential_list[1]

    print("$$$$$$$$$ Username: " + str(username))
    print("$$$$$$$$$ Password: " + str(password))
    #Check if password meets criteria
    if not auth.validate_password(password):
        print("&&&&&&& Password invalid checked")
        return buildRedirectResponse(req_http, "302 Found", "/")
    else:
        print("&&&&&&& Password is indeed valid checked")
        #Create salted hash of password
        salt = bcrypt.gensalt()
        salted_hashed_password = bcrypt.hashpw(password.encode(), salt)

        #Input username, salt, and the salted hash of password into the database
        dbHandler.register_user(username, salt, salted_hashed_password)
        
        return buildRedirectResponse(req_http, "302 Found", "/")
        

#---server_login---#
#   -Parameters: A request object
#   -Returns: 302 Found redirect (sends user back to homepage)
#   -Objective: Authenticates requests based on data from database. If salted hash of pw
#    matches what we have in database, then user is authenticated. On successful login,
#    set an auth token as a cookie (with HttpOnly directive). Tokens should be random vals and have
#    hash stored in database to verify on subsequent requests.
def server_login(request:Request):
    req_http = request.http_version
    req_cookies = request.cookies

    #Extract username and password
    credential_list = auth.extract_credentials(request)
    username = credential_list[0]
    password = credential_list[1]

    #Retrieve stored salt and hashed pw.
    user_document = dbHandler.get_user_credentials(username)
    
    if user_document:
        stored_password = user_document["salted_hashed_password"]
        stored_salt = user_document["salt"]
        
        # Compare password with stored salted, hashed password
        #password_to_check = bcrypt.hashpw(password.encode(), stored_salt)
        if bcrypt.checkpw(password.encode(), stored_password):
            # Generate an auth token and its hash
            token = secrets.token_urlsafe(32)  # Token is a string
            hashed_token = hashlib.sha256(token.encode()).hexdigest() # Hashed token is a hex string (and is stored that way in DB)
            # Store hashed_token into database
            dbHandler.insert_token(username, hashed_token)
            # Set an auth token as cookie (with HttpOnly directive set)
            set_cookie_list = [str("auth_cookie=" + token + "; Max-Age=3600; HttpOnly")]
            return buildRedirectResponse(req_http, "302 Found", "/", set_cookie_list)
        else:
            return buildRedirectResponse(req_http, "302 Found", "/")

    return buildRedirectResponse(req_http, "302 Found", "/")

#---server_logout---#
#  -Logs a user out and invalidates their auth token. It will delete their auth token from the database 
def server_logout(request:Request):
    req_http = request.http_version
    req_cookies = request.cookies

    #Determine whether or not the user is successfully logged in
    auth_token_cookie = req_cookies.get("auth_cookie")
    if auth_token_cookie:
        # Attempt to delete that cookie from the database
        auth_token_to_check = hashlib.sha256(auth_token_cookie.encode()).hexdigest()
        delete_check = dbHandler.delete_auth_token(auth_token_to_check)
        if delete_check is True:
            #Set the cookie to ""
            set_cookie_list = [str('auth_cookie=""; HttpOnly')]
            return buildRedirectResponse(req_http, "302 Found", "/", set_cookie_list)
        else:
            return buildRedirectResponse(req_http, "302 Found", "/")
    else:
        return buildRedirectResponse(req_http, "302 Found", "/")