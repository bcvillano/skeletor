import requests,json

def main():
    data = {"ip": "1.1.1.1",'username': "admin",'password': "admin"}
    requests.post("http://localhost:80/upload-password", json=data)
    _ = input("Press enter to send update")
    data = {"ip": "1.1.1.1",'username': "admin",'password': "admin2"}
    requests.post("http://localhost:80/upload-password", json=data)
    


main()