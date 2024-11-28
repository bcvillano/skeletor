import requests
import socket
import time
import threading
import json

class Client:

    def __init__(self,ip, port):
        self.ip = ip
        self.port = port
        self.local_ip = socket.gethostbyname(socket.gethostname())
        

    def heartbeat(self):
        while True:
            try:
                data = {'ip': self.local_ip,}
                req = requests.post(f"http://{self.ip}:{self.port}/heartbeat", json=data, timeout=3)
            except:
                pass
            time.sleep(120)

    def run(self):
        heartbeat_thread = threading.Thread(target=self.heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        while True:
            time.sleep(120)
        
            

def main():
    client = Client("localhost", 80)
    client.run()

if __name__ == '__main__':
    main()