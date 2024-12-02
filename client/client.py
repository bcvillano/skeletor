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
        try:
            data = {'agent_id': self.local_ip}
            req = requests.post(f"http://{self.ip}:{self.port}/register", json=data, timeout=3)
        except:
            print("Failed to register agent (" + self.local_ip + ")")
        while True:
            req = requests.get(f"http://{self.ip}:{self.port}/targets")
            print(req.text)
            targets = req.text.split("\n")
            if self.local_ip in targets:
                print("Agent is in the target list")
                try:
                    req = requests.get(f"http://{self.ip}:{self.port}/tasks")
                    print(req.json())
                    task = req.json().get('action')
                    print(task)
                except Exception as e:
                    print(e)
            time.sleep(120)
        
            

def main():
    client = Client("localhost", 80)
    client.run()

if __name__ == '__main__':
    main()