from request import Request

#===multipart file===#
#  -This file contains a class and a function for LO1.

#---Multipart_Data Class---#
#  -Fields: 
#    ->boundary: Value of boundary from Content-Type header as a string
#    ->parts: List of part objects
class Multipart_Data:
    def __init__(self, boundary: str, parts: list):
        self.boundary = boundary
        self.parts = parts

#---Part_Data Class---#
#  -Fields: 
#    ->headers: Dictionary of all headers for the part in same format as a Request object
#    ->name: str of the Content-Disposition header that matches name of that part in the HTML form
#    ->content: bytes of that part's content. (Content may contain b'\r\n\r\n', which should not corrupt data)
class Part_Data:
    def __init__(self, headers, name, content):
        self.headers = headers
        self.name = name
        self.content = content
        
#---parse_multipart---#
#  -Objective: This function exracts relevant values of a multipart request.
#  -Parameters: A Request object from util.request. Request is in bytes.
#  -Return: An object of Multipart_data
def parse_multipart(request: Request):
    boundary = ""
    part_list = []

    # #todo: Parse the multipart request.
    # total_request = request.split(b"\r\n\r\n", 1)
    # reqline_headers = total_request[0]
    # all_parts = total_request[1]

    # #Get the boundary from content header as a string
    # all_lines = reqline_headers.split(b"\r\n") #[0] is req_line, [1] is headers
    # headers = all_lines[1]

    # Get the boundary from content header as a string:
    headers_dict = request.headers #The key-vals are strings
    content_type_val = headers_dict.get("Content-Type")

    if content_type_val and content_type_val.startswith("multipart/form-data;"):
        #print(headers_dict)
        #return Multipart_Data(boundary, part_list)
        content_type_val_boundary_split = content_type_val.split("boundary=")
        boundary = content_type_val_boundary_split[1].strip()
    else:
        return "No boundary found :("

    print("BOUNDARY: " + boundary)

    # Put all parts into a list
    all_parts = request.body 
    print("BODY IS: ")
    print(all_parts)

    parts = request.body.split(b"--" + boundary.encode())
    print("BODY IS:", parts)
    for part in parts[1:-1]:  # Skip the first and last empty parts
        # Split each part into headers and content
        headers_content = part.split(b"\r\n\r\n", 1)
        part_headers = headers_content[0].decode().split("\r\n")
        part_body = headers_content[1]

        # Extract name and filename from Content-Disposition header
        part_name = None
        part_filename = None
        for header in part_headers:
            if header.startswith("Content-Disposition"):
                disposition_params = header.split(";")
                for param in disposition_params:
                    param = param.strip()
                    if param.startswith("name="):
                        part_name = param.split("=")[1].strip('"')
                    elif param.startswith("filename="):
                        part_filename = param.split("=")[1].strip('"')

        # Create Part_Data object and append to part_list
        part_list.append(Part_Data(part_headers, part_name, part_body))

    return Multipart_Data(boundary, part_list)



def test1():
    request = Request(b"""POST /form-path HTTP/1.1\r\n
    Content-Length: 9937\r\n
    Content-Type: multipart/form-data; boundary=----WebKitFormBoundarycriD3u6M0UuPR1ia\r\n\r\n
    ------WebKitFormBoundarycriD3u6M0UuPR1ia\r\n
    Content-Disposition: form-data; name="commenter"\r\n\r\n
    Jesse\r\n
    ------WebKitFormBoundarycriD3u6M0UuPR1ia\r\n
    Content-Disposition: form-data; name="upload"; filename="discord.png"\r\n
    Content-Type: image/png\r\n\r\n
    <bytes_of_the_file>\r\n
    ------WebKitFormBoundarycriD3u6M0UuPR1ia--""")

    multipart_data = parse_multipart(request)

    assert multipart_data.boundary == "----WebKitFormBoundarycriD3u6M0UuPR1ia"
    assert len(multipart_data.parts) == 2

    part1 = multipart_data.parts[0]
    assert part1.name == "commenter"
    assert part1.headers == {'Content-Disposition': 'form-data; name="commenter"'}
    assert part1.content == b"Jesse"

    part2 = multipart_data.parts[1]
    assert part2.name == "upload"
    assert part2.headers == {'Content-Disposition': 'form-data; name="upload"; filename="discord.png"', 'Content-Type': 'image/png'}
    assert part2.content == b"<bytes_of_the_file>"


if __name__ == '__main__':
    test1()