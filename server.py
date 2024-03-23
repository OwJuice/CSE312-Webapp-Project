import socketserver
from util.request import Request
from util.router import Router
from util.requestHandler import *


#Router with added routes:
router = Router()
router.add_route("GET", "/$", server_root)
router.add_route("GET", "/public/functions.js$", server_js)
router.add_route("GET", "/public/webrtc.js$", server_webrtc_js)
router.add_route("GET", "/public/style.css$", server_css)
router.add_route("GET", "/public/favicon.ico$", server_favicon)
router.add_route("POST", "/chat-messages$", server_post_chat_msgs)
router.add_route("GET", "/chat-messages$", server_get_chat_msgs)
router.add_route("GET", "/chat-messages/", server_get_chat_msg)
router.add_route("DELETE", "/chat-messages/", server_delete_chat_msg)
router.add_route("PUT", "/chat-messages/", server_update_chat_msg)
router.add_route("GET", "/public/image/", server_image)

router.add_route("post", "/register$", server_register)
router.add_route("post", "/login$", server_login)

class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        received_data = self.request.recv(2048)
        print(self.client_address)
        print("--- received data ---")
        print(received_data)
        print("--- end of data ---\n\n")
        request = Request(received_data)

        # NOTE: sendall method sends information back to the client

        req_body = request.body
        req_method = request.method
        req_path = request.path
        req_http = request.http_version
        req_headers = request.headers
        req_cookies = request.cookies

        response = router.route_request(request)
        self.request.sendall(response)

def main():
    host = "0.0.0.0"
    port = 8080

    socketserver.TCPServer.allow_reuse_address = True

    server = socketserver.TCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))

    server.serve_forever()


if __name__ == "__main__":
    main()
