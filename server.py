import socketserver
import util.dbHandler as dbHandler 
#Importing as dbHandler will prevent me from having to type util.dbHandler.<function> everytime I wanna use a function from that file
# so I can just do dbHandler.<function>. I could have imported all (*), but this would reduce code clarity as I wouldn't know where a function
# came from when calling it.
from util.request import Request


class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        received_data = self.request.recv(2048)
        print(self.client_address)
        print("--- received data ---")
        print(received_data)
        print("--- end of data ---\n\n")
        request = Request(received_data)

        # TODO: Parse the HTTP request and use self.request.sendall(response) to send your response
        # NOTE: .decode converts bytes to string, .encode converts string to bytes
        # NOTE: sendall method sends information back to the client

        req_body = request.body
        req_method = request.method
        req_path = request.path
        req_http = request.http_version
        req_headers = request.headers
        req_cookies = request.cookies

        #Root path: If path is "/", then respond with the public/index.html file
        if (req_path == "/"):
            readfile = fileReader("./public/index.html")
            visits_counter = int(req_cookies.get("visits", 0))
            visits_counter += 1 #Increment visits counter by 1
            visits_str = str(visits_counter)
            readfile = readfile.replace("{{visits}}", visits_str)
            encoded_file = readfile.encode()
            length_of_file = str(len(encoded_file))
            self.request.sendall(("HTTP/1.1 200 OK\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: " + length_of_file + "\r\nSet-Cookie: visits=" + visits_str + "; Max-Age=3600\r\n\r\n").encode() + encoded_file)
            #self.request.sendall(buildResponse("200 OK", "text/plain; charset=utf-8", readfile))

        #If path is to /public/functions.js, then serve that js code
        elif (req_path == "/public/functions.js"):
            readfile = fileReader("./public/functions.js")
            self.request.sendall(buildResponse("200 OK", "text/javascript; charset=utf-8", readfile))

        #If path is to /public/webrtc.js, then serve that js code
        elif (req_path == "/public/webrtc.js"):
            readfile = fileReader("./public/webrtc.js")
            self.request.sendall(buildResponse("200 OK", "text/javascript; charset=utf-8", readfile))

        #If path is to /public/style.css, then serve that css code
        elif (req_path == "/public/style.css"):
            readfile = fileReader("./public/style.css")
            self.request.sendall(buildResponse("200 OK", "text/css; charset=utf-8", readfile))

        #If path is to /public/favicon.ico, then serve that icon
        elif (req_path == "/public/favicon.ico"):
            readfile = imageReader("./public/favicon.ico")
            self.request.sendall(buildImageResponse("200 OK", "image/x-icon", readfile))

        #If path is to /chat-messages (POST request), then store the incoming message in the database
        #The message sent, the username, and a unique id for the message is stored.
        elif (req_path == "/chat-messages"):
            if (req_method == "POST"):
                dbHandler.insertChatMessage(req_body)
                self.request.sendall(buildResponse("200 OK", "text/plain; charset=utf-8", "Message Sent Successfully"))
            if (req_method == "GET"):
                chat_messages = dbHandler.getAllChatMessages() #chat_messages is a list of json objects
                self.request.sendall(buildResponse("200 OK", "application/json; charset=utf-8", chat_messages))
                # replace_string = ""
                # for chat_message in chat_messages:
                #     current_message = chat_message["message"] #Now curent_message contains the actual message
                #     replace_string += "<p>" + current_message + "</p>\n"


                

        # #If path is to an image path, read the image file and determine what image to send
        # #Use a variable for the image name so we can serve multiple images
    
        # elif ("/public/image" in req_path):
        #     image_path = req_path.split("/")
        #     image_name = image_path[2]  #image_name contains the name of the image and the image type like "cat.jpg" or "elephant.jpg"
        #     readfile = imageReader("public/image/" + image_name)
        #     self.request.sendall(buildResponse("200 OK", "image/jpeg", readfile))

        elif (req_path == "/public/image/cat.jpg"):
             readfile = imageReader("./public/image/cat.jpg")
             self.request.sendall(buildImageResponse("200 OK", "image/jpeg", readfile))

        elif (req_path == "/public/image/dog.jpg"):
             readfile = imageReader("./public/image/dog.jpg")
             self.request.sendall(buildImageResponse("200 OK", "image/jpeg", readfile))

        elif (req_path == "/public/image/eagle.jpg"):
             readfile = imageReader("./public/image/eagle.jpg")
             print("EAGLE IMAGES RECIEVED")
             self.request.sendall(buildImageResponse("200 OK", "image/jpeg", readfile))
        
        elif (req_path == "/public/image/elephant.jpg"):
             readfile = imageReader("./public/image/elephant.jpg")
             self.request.sendall(buildImageResponse("200 OK", "image/jpeg", readfile))

        elif (req_path == "/public/image/elephant-small.jpg"):
             readfile = imageReader("./public/image/elephant-small.jpg")
             self.request.sendall(buildImageResponse("200 OK", "image/jpeg", readfile))

        elif (req_path == "/public/image/flamingo.jpg"):
             readfile = imageReader("./public/image/flamingo.jpg")
             self.request.sendall(buildImageResponse("200 OK", "image/jpeg", readfile))           

        elif (req_path == "/public/image/kitten.jpg"):
             readfile = imageReader("./public/image/kitten.jpg")
             self.request.sendall(buildImageResponse("200 OK", "image/jpeg", readfile))     

        #Else, if path is anything that shouldn't received content, reuturn a 404 response with msg saying content wasn't found. (plain text)
        else:
            self.request.sendall(buildResponse("404 Not Found", "text/plain; charset=utf-8", "The requested content does not exist :("))
        



#---buildResponse Function---#
#   A helper function to build responses to be sent from the client to the server after receiving a request
#   Takes a response code, a MIME type, and the content as strings
#   Decodes those arguments, finds the length of the data, and puts together the whole response and returns as bytes
#   Currently only works with 200 and 404 responses
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

#---buildImageResponse Function---#
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
        

def main():
    host = "0.0.0.0"
    port = 8080

    socketserver.TCPServer.allow_reuse_address = True

    server = socketserver.TCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))

    server.serve_forever()


if __name__ == "__main__":
    main()
