from util.request import Request
from util.requestHandler import *
import re

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


class Router:

    #---Router Class---#
    #  -Parameters: None
    #  -Router objects will have routes as a state variable. These will be dictionaries mapping a tuple of http_method and path as a key
    #   and functions as values. So we link functions to specific paths based on http methods.
    def __init__(self):
        self.routes = {}

    #---add_route Method---#
    #  -Parameters: A The HTTP method (str), the path (str), and a function that takes a Request object (from util/request.py) and that returns bytes of response
    #  -Return: Nothing
    #  -Objective: Adds a route to the router. The route is a http method and path with a corresponding function. 
    #   The method is called on server start up.
    #---#
    def add_route(self, http_method: str, path: str, function):
        route_key = (http_method, re.compile(path))
        self.routes[route_key] = function
        return
    
    #---route_request Method---#
    #  -Parameters: A request object (from util/request.py)
    #  -Return: Byte array from function associated with given path
    #  -Objective: Checks the method and path of the request, then determines which added path should be used
    #   calls the function associated with that path, and then returns the bytes returned by that method.
    #   If no path for request, return 404. If multiple paths, use route added first with the add_route method.
    #---#
    def route_request(self, request: Request):
        req_method = request.method #Use as part of key lookup
        req_path = request.path #Use as part of key lookup
        route_key = (req_method, req_path)

        #Get the function associated with the request and call it if it exists. If it doesn't exist, send a 404 response
        requestHandlerFunction = self.routes.get(route_key)
        if requestHandlerFunction:
            requestHandlerFunction(request)
        else:
            #Send 404 response
            return buildResponse("404 Not Found", "text/plain; charset=utf-8", "The requested content does not exist :(")
        
        return
    
