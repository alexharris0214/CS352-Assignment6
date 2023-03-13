import socket
import signal
import sys
import random

# Read a command line argument for the port where the server
# must run.
port = 8080
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)

### Contents of pages we will serve.
# Login form
login_form = """
   <form action = "http://localhost:%d" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
""" % port
# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form
# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form
# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form
# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = """
   <h1>Welcome!</h1>
   <form action="http://localhost:%d" method = "post">
   <input type = "hidden" name = "password" value = "new" />
   <input type = "submit" value = "Click here to Change Password" />
   </form>
   <form action="http://localhost:%d" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
""" % (port, port)

new_password_page = """
   <form action="http://localhost:%d" method = "post">
   New Password: <input type = "text" name = "NewPassword" /> <br/>
   <input type = "submit" value = "Submit" />
</form>
""" % port

#### Helper functions
# Printing.
def print_value(tag, value):
    print "Here is the", tag
    print "\"\"\""
    print value
    print "\"\"\""
    print

# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)
# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)

def populateDbPasswords(inputFile):
    pwdDb = {}
    for line in inputFile:
        tokens = line.split(' ')
        urn = tokens[0]
        pwd = tokens[1].strip('\n')
        pwdDb[urn] = pwd
    return pwdDb
        
def populateDbSecrets(inputFile):
    secDb = {}
    for line in inputFile:
        tokens = line.split(' ')
        urn = tokens[0]
        secret = tokens[1].strip('\n')
        secDb[urn] = secret
    return secDb

def parseBody(body):
    begin = 0
    end = 0
    urn = ""
    for i, char in enumerate(body):
        if(char == '='):
            begin = i + 1
        if(char == '&'):
            urn = body[begin: i]
    pwd = body[begin:]
    return urn , pwd

def findCookies(headers):
    split_headers = headers.split('\n')
    stored_cookie = ""
    for head in split_headers:
        # print("Count: ", head[0:6])
        if head[0:6] == "Cookie":
            stored_cookie = head[14:].strip('\n')
    return stored_cookie
            
            

# TODO: put your application logic here!
# Read login credentials for all the users
# Read secret data of all the users
filePasswords = open('passwords.txt', 'r')
fileSecrets = open('secrets.txt', 'r')

pwdDb = populateDbPasswords(filePasswords)
secDb = populateDbSecrets(fileSecrets)
cookiesDb = {}
counter = 0

### Loop to accept incoming HTTP connections and respond.
while True:
    client, addr = sock.accept()
    req = client.recv(1024)
    print("COUNTER: ", counter)
    counter+=1
    # Let's pick the headers and entity body apart
    header_body = req.split('\r\n\r\n')
    headers = header_body[0]
    body = '' if len(header_body) == 1 else header_body[1]
    print_value('headers', headers)
    print_value('entity body', body)
    headers_to_send = ''
    html_content_to_send = login_page
    # TODO: Put your application logic here!
    # Parse headers and body and perform various actions
    # Checks for cookie header

    # First should check for new password or logout
    # Then if cookie is present or invalid 
    # Then user pass sucess / failure if else
    # Basic case

    cookieID = findCookies(headers)

    if(headers[0] == "P" and body[0][0] == "p"):
        
        # Requested new password page
        print('Requested reset pasword page')
        html_content_to_send = new_password_page
    elif(headers[0] == "P" and body[0][0] == "a"):
        # Check if this is the base case? if so then combine if headers = P with body[0][0] = p and have elif with new password case
        print("\n\n\n LOGOUT CASE TEST 12:::\n\n\n")
        headers_to_send = 'Set-Cookie: token=' + str(cookieID) + '; expires=Thu, 01 Jan 1970 00:00:00 GMT\r\n'
        print(headers_to_send)
        html_content_to_send = login_page
    elif headers[0] == "P" and body[:12].strip('\n') == "NewPassword=":
        # New password request was posted
        new_password = body[12:]
        username_here = cookiesDb.get(cookieID)
        pwdDb[username_here] = new_password
        html_content_to_send = success_page
        print("\n\n\n HIT Change password CASE TEST 10:::\n\n\n")
        print(pwdDb)
    else:
        if cookieID:
            if (cookieID in cookiesDb):
                # Valid cookie
                usr = cookiesDb[cookieID]
                html_content_to_send = success_page + secDb[usr]
                print("\n\n\n HIT Valid cookie CASE TEST 6:::\n\n\n")
                # Check for case 7 how can you enter a bad username or password and have a valid cookie without it auto login, does it mean cookie is only checked when login button is hit?
                # Same for case 6 and 8
            else:
                # Invalid cookie case
                html_content_to_send = bad_creds_page
                print("\n\n\n HIT Bad credentials CASE TEST 9:::\n\n\n")
        else:
            # No cookie id
            urn, pwd = parseBody(body)
            # Check for case 5, with missing username and has password and check if it gives bad credentials
            if(urn != "" or pwd != ""):
                if(urn in pwdDb):
                    if(pwd == pwdDb[urn]):
                        # On successful login
                        html_content_to_send = success_page + secDb[urn]
                        cookieID = random.getrandbits(64)
                        cookiesDb[str(cookieID)] = urn
                        headers_to_send = 'Set-Cookie: token=' + str(cookieID) + '\r\n'
                        print("\n\n\n HIT Successful Login CASE TEST 2:::\n\n\n")
                        html_content_to_send = success_page + secDb[urn]
                    else:
                        # Existing username with bad password
                        html_content_to_send = bad_creds_page
                        print("\n\n\n HIT Bad password Login CASE TEST 4:::\n\n\n")
                else:
                    # Non-existent username
                    html_content_to_send = bad_creds_page
                    print("\n\n\n HIT Non-existent Login CASE TEST 3:::\n\n\n")
            else:
                # Base case
                print("\n\n\n HIT BASE CASE TEST 1:::\n\n\n")
                html_content_to_send = login_page

            
    # But other possibilities exist, including
    # html_content_to_send = success_page + <secret>
    # html_content_to_send = bad_creds_page
    # html_content_to_send = logout_page
    
    # (2) `headers_to_send` => add any additional headers
    # you'd like to send the client?
    # Right now, we don't send any extra headers.

    # Construct and send the final response
    response  = 'HTTP/1.1 200 OK\r\n'
    response += headers_to_send
    response += 'Content-Type: text/html\r\n\r\n'
    response += html_content_to_send
    print_value('response', response)    
    client.send(response)
    client.close()
    
    print "Served one request/connection!"
    print

# We will never actually get here.
# Close the listening socket
sock.close()
