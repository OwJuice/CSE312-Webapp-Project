from util.request import Request
import util.dbHandler as dbHandler 

#===requestHandler.py===#
#  -This file holds functions that handle building responses to requests.

def server_root(request:Request):
    #ToDo: read index.html
    return b"This is where response would go"

#Some other function (Functions for endpoints of server)
def server_js(request:Request):
    #ToDo: read function.js
    return b"This is where response would go"

#Some other function (Functions for endpoints of server)
def server_image(request:Request):
    #ToDo: read filename from the path and read that file
    return b"This is where response would go"