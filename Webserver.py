import threading
from random import randint
import socket

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.bindSocket()

    def bindSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.sock.bind((self.host, self.port))
                break
            except OSError:
                self.port = randint(2000, 10000)

        self.sock.listen()
        print("Server started at {}:{}".format(self.host, self.port))

    def stop(self):
        self.closeSocket()

    def closeSocket(self):
        self.sock.close()

    def run(self):
        while True:
            conn, addr = self.sock.accept()
            self.coop(conn, addr)

    def coop(self, conn, addr):
        print('Connected client', addr)
        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    print("Client disconnected", addr)
                    break

                print("Message from {} - {}".format(addr, data))
                conn.send(data.upper().encode())
        except ConnectionAbortedError:
            print("Lost connection with", addr)
        finally:
            conn.close()

class ThreadedServer(Server):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.threads = []
        
    def run(self):
        while True:
            conn, addr = self.sock.accept()

            thr = threading.Thread(target=self.coop, args=[conn, addr])
            self.threads.append(thr)
            thr.start()

    def stop(self):
        super().stop()
        self.closeThreads()

    def closeThreads(self):
        for t in self.threads:
            t.join()

class ResponseLoader:
    def __init__(self):
        self.paths = {
            '/': 'index.html',
            '/adress': 'adress.html',
            '/product': 'product.html',
            '/style/main.css': 'main.css'
        }

    def loadResponse(self, path):
        header = 'HTTP/1.1 200 OK\n'
        contentType = ''
        try:
            file = self.paths[path]
            if file.endswith('.html'):
                contentType = 'text/html'
                file = 'webserver/' + file

            elif file.endswith('.css'):
                contentType = 'text/css'
                file = 'webserver/main.css'

            else:
                header = 'HTTP/1.1 403 Forbidden\n\n'
                file = 'webserver/403.html'

        except KeyError:
            header = 'HTTP/1.1 404 File not found\n\n'
            file = 'webserver/404.html'

        with open(file, 'r') as f:
            content = f.read()
        
        if not contentType:
            return header + content

        return header + 'Content-Type: ' + contentType + '\n\n' + content

class WebServer(ThreadedServer):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.responseLoader = ResponseLoader()

    def coop(self, conn, addr):
        try:
            print('Connected client', addr)
   
            request = conn.recv(4096).decode()
            headers = request.split()

            response = self.responseLoader.loadResponse(headers[1])
            conn.send(response.encode())
        finally:
            conn.close()
    
if __name__ == "__main__":
    try:
        webserver = WebServer("localhost", 8080)
        webserver.run()
    finally:
        webserver.stop()