from util.request import Request

#---extract_credentials Method---#
#  -Parameters: A request object (from util/request.py)
#  -Return: List of 2 elements (A username and a password both strs)
#  -Objective:
#---#
def extract_credentials(request: Request):
    username = None
    password = None
    req_body = request.body
    body_string = req_body.decode()

    key_val_pairs = body_string.split("&")
    for key_val_pair in key_val_pairs:
        key, val = key_val_pair.split("=")
        #Decode percent encoded values
        decoded_val = decode_percent_encoding(val)

        if key == "username":
            username = decoded_val
        elif key == "password":
            password = decoded_val

    credential_list = [username, password]
    return credential_list

def decode_percent_encoding(value):
    # Replace percent-encoded characters with their decoded equivalents
    decoded_value = value.replace('%21', '!').replace('%40', '@').replace('%23', '#').replace('%24', '$').replace('%25', '%').replace('%5E', '^').replace('%26', '&').replace('%28', '(').replace('%29', ')').replace('%2D', '-').replace('%5F', '_').replace('%3D', '=')

#---validate_password Method---#
#  -Parameters: A string representing a password
#  -Return: A boolean 
#  -Objective: Specifies true or false if the password meets all 6 criteria to be considered acceptable
#       1. The length of the password is at least 8
#       2. The password contains at least 1 lowercase letter
#       3. The password contains at least 1 uppercase letter
#       4. The password contains at least 1 number
#       5. The password contains at least 1 of the 12 special characters ('!', '@', '#', '$', '%', '^', '&', '(', ')', '-', '_', '=')
#       6. The password does not contain any invalid characters (eg. any character that is not an alphanumeric or one of the 12 special characters)
#---#
def validate_password():
    return