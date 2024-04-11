from util.request import Request

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
    def __init__(self, headers: dict, name: str, content: bytes, filename: str):
        self.headers = headers
        self.name = name
        self.content = content
        self.filename = filename
        
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


    # Put all parts into a list
    all_parts = request.body 

    #Todo: Parse the body to convert all parts into part objects and add to the part_list
    raw_parts = all_parts.split(b"--" + boundary.encode())
    raw_parts = raw_parts[1:-1] #Removes the first empty string as well as everything after the end boundary.

    for part in raw_parts:
        #Split each part into subheaders and subcontent. Only split on \r\n once so we don't potentially corrupt content
        subheaders_subcontent = part.split(b'\r\n\r\n', 1)
        subheaders = subheaders_subcontent[0]

        # Retrieve the content
        subcontent = subheaders_subcontent[1]
        if subcontent.endswith(b'\r\n'):
            # Remove the last two bytes ('\r\n') using slicing
            subcontent = subcontent[:-2]
        subheaders_list = subheaders.split(b'\r\n')[1:] #Slice out the first item which will be a \r\n

        #Build the subheader dictionary
        subheader_dict = {}
        for subheader in subheaders_list:
            split_subheader = subheader.split(b':', 1)
            subheader_key = split_subheader[0].strip()
            subheader_val = split_subheader[1].strip()
            subheader_dict[subheader_key] = subheader_val
        
        #print("^^^ subheader_dict: " + str(subheader_dict))
        
        #Retrieve the name from the content-disposition header
        content_disposition = subheader_dict.get(b"Content-Disposition")
        #print("^^^ content_disposition: " + str(content_disposition))
        content_disposition_split = content_disposition.split(b';')
        name = None
        filename = None

        for content_disposition_part in content_disposition_split:
            content_disposition_part = content_disposition_part.strip()

            if content_disposition_part.startswith(b'name='):
                name = content_disposition_part.split(b'=')[1].strip(b'"')
            
            if content_disposition_part.startswith(b'filename='):
                filename = content_disposition_part.split(b'=')[1].strip(b'"')


        # Build the part objects and put them into the part_list
        #print("NAME IS: " + str(name))
        #print("subheader_dict: " + str(subheader_dict))
        #print("subcontent: " + str(subcontent))
            
        #Convert dictionary and name to strings:
        decoded_subheader_dict = {}

        for key, value in subheader_dict.items():
            decoded_key = key.decode()
            decoded_value = value.decode()
            decoded_subheader_dict[decoded_key] = decoded_value

        decoded_name = name.decode()
        if filename is not None:
            filename = filename.decode()

        part_list.append(Part_Data(decoded_subheader_dict, decoded_name, subcontent, filename))

    return Multipart_Data(boundary, part_list)



def test1():
    request = Request(b'POST /form-path HTTP/1.1\r\nContent-Length: 9937\r\nContent-Type: multipart/form-data; boundary=----WebKitFormBoundarycriD3u6M0UuPR1ia\r\n\r\n------WebKitFormBoundarycriD3u6M0UuPR1ia\r\nContent-Disposition: form-data; name="commenter"\r\n\r\nJesse\r\n------WebKitFormBoundarycriD3u6M0UuPR1ia\r\nContent-Disposition: form-data; name="upload"; filename="discord.png"\r\nContent-Type: image/png\r\n\r\n<bytes_of_the_file>\r\n------WebKitFormBoundarycriD3u6M0UuPR1ia--')

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