class Request:

    def __init__(self, request: bytes):
        # TODO: parse the bytes of the request and populate the following instance variables
        
        #Separate headers & request line from body
        total_request = request.split(b"\r\n\r\n")
        reqline_headers = total_request[0].decode() #reqline_headers contains the string of the request line and the headers together
        
        #Separate request line from headers
        all_lines = reqline_headers.split("\r\n")

        #Parse request line by splitting on white space
        reqline = all_lines[0].split() #reqline contains the separated request line values

        #Get all of the headers (everything after the first line in all_lines from splitting on new lines)
        all_header_lines = all_lines[1:] #Contains all the lines of the headers

        #Parse header lines to fit them into a dictionary
        headers_dict = {}
        cookies_dict = {}
        for header_line in all_header_lines:
            split_header = header_line.split(":", 1)
            header_key = split_header[0]
            header_val = split_header[1].strip()
            #Add those key-val pairs to the header dictionary
            headers_dict[header_key] = header_val

            #Check if the key is a cookie (If it is, store that header into a cookie dictionary as well)
            if header_key == "Cookie":
                headers_dict[header_key] = header_val
                separate_cookie_pairs = header_val.split(";")   #separate_cookie_pairs contains each cookie key-val pair (ex: id=123)
                for cookie_pair in separate_cookie_pairs:
                    stripped_cookie_pair = cookie_pair.strip()
                    cookie_key_val = stripped_cookie_pair.split("=")
                    cookie_key = cookie_key_val[0]
                    cookie_val = cookie_key_val[1]
                    cookies_dict[cookie_key] = cookie_val


        self.body = total_request[1]
        self.method = reqline[0] #This is the request type
        self.path = reqline[1]
        self.http_version = reqline[2]
        self.headers = headers_dict
        self.cookies = cookies_dict



def test1():
    request = Request(b'GET / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    assert request.method == "GET"
    print(request.method)
    print(request.path)
    print(request.http_version)
    assert "Host" in request.headers
    print(request.headers)
    assert request.headers["Host"] == "localhost:8080"  # note: The leading space in the header value must be removed
    assert request.body == b""  # There is no body for this request.
    # When parsing POST requests, the body must be in bytes, not str

    # This is the start of a simple way (ie. no external libraries) to test your code.
    # It's recommended that you complete this test and add others, including at least one
    # test using a POST request. Also, ensure that the types of all values are correct


if __name__ == '__main__':
    test1()
