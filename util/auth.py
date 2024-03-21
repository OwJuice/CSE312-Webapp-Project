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

    #Fully decode the whole body before parsing.
    fully_decoded_body_string = decode_percent_encoding(body_string)

    key_val_pairs = fully_decoded_body_string.split("&")
    for key_val_pair in key_val_pairs:
        key, val = key_val_pair.split("=")

        if key == "username":
            username = val
        elif key == "password":
            password = val

    credential_list = [username, password]
    return credential_list

def decode_percent_encoding(value):
    # Replace percent-encoded characters with their decoded equivalents
    decoded_value = value.replace('%21', '!').replace('%40', '@').replace('%23', '#').replace('%24', '$').replace('%25', '%').replace('%5E', '^').replace('%26', '&').replace('%28', '(').replace('%29', ')').replace('%2D', '-').replace('%5F', '_').replace('%3D', '=')
    return decoded_value

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
def validate_password(password):
    # Criteria 1: Length of the password is at least 8
    if len(password) < 8:
        return False

    lowercase_present = False
    uppercase_present = False
    number_present = False
    special_character_present = False

    # Iterate over each character in the password
    for char in password:
        # Criteria 2: Check for lowercase letter
        if char.islower():
            lowercase_present = True

        # Criteria 3: Check for uppercase letter
        if char.isupper():
            uppercase_present = True

        # Criteria 4: Check for number
        if char.isdigit():
            number_present = True

        # Criteria 5: Check for special character
        if char in "!@#$%^&()-_=":
            special_character_present = True

        # Criteria 6: Check for invalid characters
        if not (char.isalnum() or char in "!@#$%^&()-_="):
            return False

    # Check if all criteria are met
    if lowercase_present and uppercase_present and number_present and special_character_present:
        return True
    else:
        return False
