from request import Request
import re

class Router:

    #Constructor with no parameters
    def __init__(self):
        print("I'm an object with no parameters :)")

    #---add_route Method---#
    #  -Parameters: A The HTTP method (str), the path (str), and a function that takes a Request object (from util/request.py) and that returns bytes of response
    #  -Return: Nothing
    #  -Objective: Adds a route to a router
    #---#
    def add_route(self, http_method: str, path: str, function):
        return
    
    #---route_request Method---#
    #  -Parameters: A request object (from util/request.py)
    #  -Return: Byte array from function associated with given path
    #  -Objective: Checks the method and path of the request, then determines which added path should be used
    #   calls the function associated with that path, and then returns the bytes returned by that method.
    #   If no path for request, return 404. If multiple paths, use route added first with the add_route method.
    #---#
    def route_request(self, request: Request):
        return