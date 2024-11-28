from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def update_pwnboard(ip):
    try:
        data = {'ip': ip, 'type': "festivus"}
        req = requests.post("https://pwnboard.win/pwn/boxaccess", json=data, timeout=3)
    except:
        pass

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.json
        ip = data['ip']
        print(f"Received heartbeat from {ip}")
        update_pwnboard(ip)
        return jsonify({'status': 'success'})
    except:
        pass

def main():
    app.run(debug=True,host='0.0.0.0',port=80)

if __name__ == '__main__':
    main()