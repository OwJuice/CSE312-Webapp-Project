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
import json
import uuid
import util.multipart as multipart
import util.websockets as websockets


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

#---get_username---#
#   A helper function that takes the cookies of a request and finds a username associated with the auth_token sent with the request.
#   If no auth token found or no username associated with the auth token, then the user is a Guest.
#   TLDR: Determines whether or not a user is successfully logged in and returns username.
def get_username(req_cookies: dict):
    auth_token_cookie = req_cookies.get("auth_cookie")
    username = ""
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
    return username

# A helper function to create a chat message payload when using websockets
def create_chat_message(username, safe_message):
    #Insert the message into the database
    message_id = dbHandler.insertChatMessage(username, safe_message)

    # Create a dictionary representing the message content
    message_dict = {
        'messageType': 'chatMessage',
        'username': username,
        'message': safe_message,
        'id': message_id
    }
    
    # Convert the dictionary into a JSON string
    json_string = json.dumps(message_dict)
    
    # Encode the JSON string into bytes using UTF-8 encoding
    payload = json_string.encode('utf-8')
    return payload

def server_root(request:Request):
    req_cookies = request.cookies

    readfile = fileReader("./public/index.html")
    visits_counter = int(req_cookies.get("visits", 0))
    visits_counter += 1 #Increment visits counter by 1
    visits_str = str(visits_counter)
    readfile = readfile.replace("{{visits}}", visits_str)
    # Check if user is logged/authenticated
    auth_token_cookie = req_cookies.get("auth_cookie")
    if auth_token_cookie:
        auth_token_hashed = hashlib.sha256(auth_token_cookie.encode()).hexdigest()
        xsrf_token = dbHandler.xsrf_token_check(auth_token_hashed)
        if xsrf_token is None:
            # The user doesn't have an xsrf token yet, so generate one and store it
            
            xsrf_token = secrets.token_urlsafe(32)
            dbHandler.insert_xsrf_token(auth_token_hashed, xsrf_token)
            # Put the xsrf token in the html
            readfile = readfile.replace("{{xsrf_token}}", xsrf_token)

        elif xsrf_token == "0":
            pass
        else:
            # The user currently has an xsrf token so use it
            readfile = readfile.replace("{{xsrf_token}}", xsrf_token)

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
    req_body = request.body #This contains the message and the xsrf token
    req_cookies = request.cookies
    req_body_decoded = req_body.decode()
    req_body_dict = json.loads(req_body_decoded)
    chat_message = req_body_dict['message']
    xsrf_token = req_body_dict['xsrf_token']

    print("$$$$$ The body is: " + req_body_decoded)

    #Determine whether or not the user is successfully logged in
    username = get_username(req_cookies)
    #At this point, the username is the one associated with auth token from DB
    #If no auth token or no user associated, then username is "Guest"
        
    # Now check if the user's submitted xsrf token matches the stored xsrf token
    print("$$$$$ username is: " + str(username))
    if username != "Guest":
        print("$$$$$ username is not 'Guest'")
        # User is not a guest and is logged in
        stored_xsrf_token = dbHandler.xsrf_token_from_username(username)
        print("$$$$$ stored xsrf is: " + str(stored_xsrf_token))
        print("$$$$$  xsrf is: " + str(xsrf_token))
        if stored_xsrf_token != xsrf_token:
            # Bad xsrf token
            return buildResponse("403 Not Authorized", "text/plain; charset=utf-8", "Invalid XSRF token >:O")
        else:
            pass # If xsrf token is valid, pass through and send a chat message
            #Todo: GOTTA HAVE SOMETHING HERE

    # User is either a guest or their xsrf token is valid
    #Escape HTML before inserting msg into database
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
    req_http = request.http_version
    req_path = request.path
    req_cookies = request.cookies

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
        # Determine if we have the authentification to delete the message
        # Use the auth_token to get the username
        auth_token_cookie = req_cookies.get("auth_cookie")
        if auth_token_cookie:
            auth_token_to_check = hashlib.sha256(auth_token_cookie.encode()).hexdigest()
            username = dbHandler.get_username_from_token(auth_token_to_check)
            # Lookup the username associated with the message id and check if usernames are the same
            stored_username = dbHandler.get_username_from_chat(message_id)
            # If the current username matches the username associated with the id, delete message
            if username == stored_username:
                dbHandler.deleteChatMessage(message_id)
                return "HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n".encode()
            else:
                # Usernames don't match, so not authorized to delete
                return buildResponse("403 Not Authorized", "text/plain; charset=utf-8", "You can't delete someone else's message >:O")
        else:
            # The user is not logged in. (Doesn't have auth_token) Just redirect to homepage.
            return buildRedirectResponse(req_http, "302 Found", "/")
    
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

def server_user_image(request:Request):
    req_path = request.path

    image_path = req_path.split("/")
    #If path is: "/public/user-image/cat.jpg"
    #image_path looks like: ['', 'public', 'image', 'cat.jpg']

    #Check if image path is invalid path
    if len(image_path) != 4 or image_path[3] == "":
        return buildResponse("400 Bad Request", "text/plain", "Invalid image path")

    image_name = image_path[3]  
    #image_name contains the name of image & image type like "cat.jpg" or "elephant.jpg"
    image_file_path = "public/user-image/" + image_name

    #See if requested image exists
    if not os.path.exists(image_file_path):
        return buildResponse("404 Not Found", "text/plain", "Image not found")
    
    readfile = imageReader(image_file_path)
    return buildImageResponse("200 OK", "image/jpeg", readfile)

def server_user_video(request:Request):
    req_path = request.path

    video_path = req_path.split("/")
    #If path is: "/public/user-video/cat.mp4"
    #image_path looks like: ['', 'public', 'image', 'cat.mp4']

    #Check if video path is invalid path
    if len(video_path) != 4 or video_path[3] == "":
        return buildResponse("400 Bad Request", "text/plain", "Invalid image path")

    video_name = video_path[3]  
    #image_name contains the name of video & video type like "cat.mp4" or "elephant.mp4"
    video_file_path = "public/user-video/" + video_name

    #See if requested video exists
    if not os.path.exists(video_file_path):
        return buildResponse("404 Not Found", "text/plain", "Image not found")
    
    readfile = imageReader(video_file_path)
    return buildImageResponse("200 OK", "video/mp4", readfile)

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

    #Check if password meets criteria
    if not auth.validate_password(password):
        return buildRedirectResponse(req_http, "302 Found", "/")
    else:
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

#---handle_image_upload---#
#  -Helper function to send chat messages regarding image uploads
def handle_image_upload(part, username):
    # Create a new filename and path for the image
    filename = str(uuid.uuid4()) + ".jpg"
    if dbHandler.filename_checker(filename):
        while dbHandler.filename_checker(filename):
            filename = filename = str(uuid.uuid4()) + ".jpg"
    upload_path = os.path.join("/public/user-image", filename)

    if not os.path.exists("/public/user-image"):
        os.makedirs("/public/user-image")

    #Write image file to image directory
    f = open(upload_path[1:], "wb") #Python did not like the first "/" in the file path before public as in </>public/...
    f.write(part.content)
    f.close()

    # Create chat message for image
    message = f'<img src="{upload_path}" alt="User Uploaded Image"/>'
    dbHandler.insertChatMessage(username, message)

#---handle_video_upload---#
#  -Helper function to send chat messages regarding video uploads
def handle_video_upload(part, username):
    # Create a new filename and path for the video
    filename = str(uuid.uuid4()) + ".mp4"
    if dbHandler.filename_checker(filename):
        while dbHandler.filename_checker(filename):
            filename = filename = str(uuid.uuid4()) + ".mp4"
    upload_path = os.path.join("/public/user-video", filename)

    if not os.path.exists("/public/user-video"):
        os.makedirs("/public/user-video")

    #Write image file to image directory
    f = open(upload_path[1:], "wb") #Python did not like the first "/" in the file path before public as in </>public/...
    f.write(part.content)
    f.close()

    # Create chat message for video using HTML video element
    message = f'<video width="320" height="240" controls><source src="{upload_path}" type="video/mp4"></video>'
    dbHandler.insertChatMessage(username, message)

#---server_multipart_form---#
#  -Objective: Respond to an image upload by sending the filename as a chat message 
def server_multipart_form(request:Request):
    print("1--- WE ARE GOING TO DO MULTIPART")
    req_cookies = request.cookies
    req_http = request.http_version
    multipart_data = multipart.parse_multipart(request)
    username = get_username(req_cookies)

    #Check each part of the multipart form for the uploaded image
    for part in multipart_data.parts:
        if part.name == "upload":
            #Get user given filename to determine type of file
            filename = part.filename
            print("5---THE FILENAME IS: ", str(filename))

            if filename.endswith(".jpeg") or filename.endswith(".jpg"):
                print("2--- WE ARE ABOUT TO HANDLE IMAGE UPLOAD: ")
                handle_image_upload(part, username)
            elif filename.endswith(".mp4"):
                print("3--- WE ARE ABOUT TO HANDLE VIDEO UPLOAD")
                handle_video_upload(part, username)

    print("4--- WE ARE ABOUT TO REDIRECT BACK TO HOME AFTER MULTIPART")
    return buildRedirectResponse(req_http, "302 Found", "/")

#---server_websocket---#
#  -When this function is called, the TCP wants to be upgraded to websockets.
#  -This function will add the socket to socket_dict, a global dictionary of usernames to socket connections
socket_set = set()
def server_websocket(request:Request, socket):
    #---The General Flow---#
    #check if user is authenticated, using cookies from socket's request , request.cookies
    #send the handshake, by computing the accept, socket.request.sendall(HANDSHAKE)
    #add socket to a list of websocket connections, maybe a dictionary associated socket -> username (from cookies)
    #begin the while true loop, where you will recv 2048 bytes
    #in initial recv you may recieve multiple frames (back to back)
    #check fin bit if 0, need to aggregate body over next couple frames
    #buffer for current frame *always* even if fin bit is 0, as fin and buffering NOT mutually exclusive
    #----------------------#

    #check if user is authenticated, using cookies from socket's request , request.cookies
    username = get_username(request.cookies)
    
    #send the handshake, by computing the accept, socket.request.sendall(HANDSHAKE)
    websocket_key = request.headers.get("Sec-WebSocket-Key", "")
    accept_key = websockets.compute_accept(websocket_key)

    encoded_string = "Upgraded to Websockets".encode
    length_of_string = str(len(encoded_string))
    socket.request.sendall("HTTP/1.1 101 Switching Protocols\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: " + length_of_string + "\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Accept: " + accept_key + "\r\n\r\n").encode() + encoded_string
    
    #add socket to a list of websocket connections, maybe a dictionary associated socket -> username (from cookies)
    socket_set.add(socket)

    # Variable containing extra bytes due to overreading back to back frames
    extra_bytes = bytearray()
    # Variable containing the running payload if we have continuation frames
    running_payload = bytearray()
    #begin the while true loop, where you will recv 2048 bytes (We are in websocket mode now baby)
    while True:
        # Our received data from reading will be prepending by potential extra bytes from previous iteration of the loop. This means that we will
        # have seen continuation frames before with a fin bit = 0. We will subtract this from 2048, meaning we will always work with <= 2048 bytes 
        # at a time
        received_data = extra_bytes + socket.request.recv(2048 - len(extra_bytes))
        parsed_frame_data = websockets.parse_ws_frame(received_data)

        # Handle disconnections here:
        if parsed_frame_data.opcode == 8:
            socket_set.discard(socket)
            break

        official_payload_length = parsed_frame_data.payload_length
        read_payload_length = len(parsed_frame_data.payload)

        #Check the fin bit. If 0, then we have continuation frames. If 1, then we can send a response.
        if parsed_frame_data.fin_bit == 0:
            # Check the official payload length vs what we read to determine buffering or backtoback extra bytes

            # Buffering:
            if read_payload_length < official_payload_length:
                running_payload.extend(parsed_frame_data.payload) # This uses the initial data we read
                while official_payload_length > read_payload_length:
                    new_data = socket.request.recv(min(2048, official_payload_length - read_payload_length))
                    read_payload_length += len(new_data)
                    if not new_data:
                        break
                    running_payload.extend(new_data) # This uses the new data we are getting
                # After finishing buffering to get the whole frame, go back to top of loop until we hit that fin bit of 1
                continue

            # Back to back (Extra):
            elif read_payload_length >= official_payload_length:
                extra_bytes = parsed_frame_data.payload[official_payload_length:] #Extra is everything after official payload bytes
                running_payload.extend(parsed_frame_data.payload[:official_payload_length]) #We are concatenating one frame we have just read, without the extra bytes
                # After finishing storing extra bytes and concatenating to our running payload, go back to top of loop until we hit that fin bit of 1
        
        elif parsed_frame_data.fin_bit == 1:
            # Check the official payload length vs what we read to deter                                                                                                                                                                mine buffering or backtoback extra bytes

            # Buffering:
            if read_payload_length < official_payload_length:
                running_payload.extend(parsed_frame_data.payload) # This uses the initial data we read
                while official_payload_length > read_payload_length:
                    new_data = socket.request.recv(min(2048, official_payload_length - read_payload_length))
                    read_payload_length += len(new_data)
                    if not new_data:
                        break
                    running_payload.extend(new_data) # This uses the new data we are getting
                # Now we have a full message that we can extract from the payload
                full_message = websockets.extract_payload_message(running_payload)
                safe_message = htmlInjectionPreventer(full_message)
                # Create the payload response and insert message into database
                payload_response = create_chat_message(username, safe_message)
                
                # Send the payload message to all websocket connections in our datastructure of sockets
                for websocket_connection in socket_set:
                    websocket_connection.request.sendall(payload_response)
                # Now the full message has been saved to the database AND sent to all websocket connections we have stored
            
            # TODO: DO back to back for fin bit of 1.
            elif read_payload_length >= official_payload_length:
                extra_bytes = parsed_frame_data.payload[official_payload_length:] #Extra is everything after official payload bytes
                running_payload.extend(parsed_frame_data.payload[:official_payload_length]) #We are concatenating one frame we have just read, without the extra bytes
                # Now we have a full message that we can extract from the payload
                full_message = websockets.extract_payload_message(running_payload)
                safe_message = htmlInjectionPreventer(full_message)
                # Create the payload response and insert message into database
                payload_response = create_chat_message(username, safe_message)
                
                # Send the payload message to all websocket connections in our datastructure of sockets
                for websocket_connection in socket_set:
                    websocket_connection.request.sendall(payload_response)
                # Now the full message has been saved to the database AND sent to all websocket connections we have stored




        #------------------------------THE FOLLOWING IS OLD CODE: -------------------------------#

        if current_data:
            #There are extra bytes/current data to be used
            #Use those bytes as beginning of the next frame
            pass

        #Prepend current data to newly received data. The prepended data might be extra 
        #current_data = current_data + socket.request.recv(2048 - )
        else:
            # We have no previous data so this is the beginning of a frame.
            current_data = socket.request.recv(2048)
            parsed_frame = websockets.parse_ws_frame(current_data) #Keep in mind that this might be less than or more than 1 actual frame
            # Find out how many frames we've read
            actual_payload_length = parsed_frame.payload_length
            read_payload_length = len(parsed_frame.payload) #This might not be 1 payload, but may have a payload and headers of next frame
            # If read < actual payload length bytes, buffer
            if read_payload_length < actual_payload_length:
                while actual_payload_length > read_payload_length:
                    new_data = socket.request.recv(min(2048, actual_payload_length - read_payload_length))
                    read_payload_length += len(new_data)
                    if not new_data:  # Check if no more data is received
                        break
                    current_data += new_data
                # Now we have all data for a single frame that we needed to buffer for
                # Create a frame as the response
                response = websockets.generate_ws_frame(current_data)
                pass
            # If read > actual payload length bytes, store extra bytes as start of next frame
            elif read_payload_length > actual_payload_length

                pass

            # Keep parsing until fin bit is 1. So if 0, keep parsing
            current_fin_bit = parsed_frame.fin_bit
            if (current_fin_bit == 0):
                pass
                
            

        received_data = socket.request.recv(2048) #This received data should be one, part of, or multiple websocket frame(s)
        #in initial recv you may recieve multiple frames (back to back)

        #check fin bit if 0, need to aggregate body over next couple frames
        #buffer for current frame *always* even if fin bit is 0, as fin and buffering NOT mutually exclusive
