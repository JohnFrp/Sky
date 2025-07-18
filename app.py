from flask import Flask, render_template, request, jsonify
import requests
import time
import hashlib
import random
import string
from urllib.parse import quote

app = Flask(__name__)

# Preset configurations
PRESETS = {
    "ID 1": {
        "base_url": "https://d3p651cdryuqc0.cloudfront.net/skyvpn/ad/v2/taskReward",
        "device_id": "iOS.5bb98b6d029d9509dcd30cf6380bc2e6.skyvpn",
        "token": "6ffd3a6f754fcf79dfb1462f8df4cffc",
        "user_id": "356244593592981"
    },
    "ID 2": {
        "base_url": "https://d2fh4wjtzvhqti.cloudfront.net/skyvpn/ad/v2/taskReward",
        "device_id": "iOS.5bb98b6d029d9509dcd30cf6380bc2e6.skyvpn",
        "token": "0929cc4eba05836d3b3e870f995c4145",
        "user_id": "356244593594211"
    },
    "ID 3": {
        "base_url": "https://d3fvzw9jui768t.cloudfront.net/skyvpn/ad/v2/taskReward",
        "device_id": "iOS.5bb98b6d029d9509dcd30cf6380bc2e6.skyvpn",
        "token": "6c3ef0ed96eb68933ca81d15b77deca3",
        "user_id": "356244593594470"
    },
    "ID 4": {
        "base_url": "https://d2fh4wjtzvhqti.cloudfront.net/skyvpn/ad/v2/taskReward",
        "device_id": "iOS.89509bda35b1ebe357f9c3bf8c7e8b76.skyvpn",
        "token": "773a675cbf0687c495f8015a7e0e421",
        "user_id": "356244593631300"
    }
}

class SkyVPNAutoReward:
    def __init__(self, base_url, device_id, token, user_id):
        self.base_url = base_url
        self.device_id = device_id
        self.token = token
        self.user_id = user_id
        self.app_version = "2.0.10"
        self.country = "MM"
        self.time_zone = "GMT+6:30"
        self.working_task_types = [1, 3]
        self.reward_amount = 1000

    def generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def generate_signature(self, timestamp):
        sign_str = f"{timestamp}{self.device_id}{self.token}"
        return hashlib.md5(sign_str.encode()).hexdigest().upper()

    def get_current_timestamp(self):
        return int(time.time() * 1000)

    def claim_reward(self, task_type):
        timestamp = self.get_current_timestamp()
        
        params = {
            "appVersion": self.app_version,
            "country": self.country,
            "deviceId": self.device_id,
            "dingtoneId": "",
            "r_i_s": self.generate_random_string(),
            "sign": self.generate_signature(timestamp),
            "taskType": str(task_type),
            "timeZone": quote(self.time_zone),
            "timestamp": str(timestamp),
            "token": self.token,
            "userId": self.user_id
        }

        headers = {
            "accept": "*/*",
            "api_version": "1",
            "user-agent": "SkyVPN/2.0.10 (iPhone; iOS 17.0.3; Scale/3.00)",
            "accept-language": "en;q=1",
            "accept-encoding": "gzip, deflate, br"
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("result") == "1":
                    balance = data["data"]["userBalance"]["balance"]
                    return True, balance, f"Success! Task Type: {task_type} | Balance: {balance}"
                else:
                    return False, None, f"Failed (Type {task_type}): {data.get('reason', 'Unknown error')}"
            else:
                return False, None, f"HTTP Error {response.status_code}"

        except requests.exceptions.RequestException as e:
            return False, None, f"Connection error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html', presets=PRESETS)

@app.route('/run', methods=['POST'])
def run_rewards():
    data = request.json
    
    base_url = data.get('base_url')
    device_id = data.get('device_id')
    token = data.get('token')
    user_id = data.get('user_id')
    cycles = int(data.get('cycles', 1))
    delay = float(data.get('delay', 2.0))
    
    rewarder = SkyVPNAutoReward(base_url, device_id, token, user_id)
    rewarder.reward_amount = int(data.get('reward_amount', 1000))
    
    results = []
    total_claimed = 0
    
    for cycle in range(1, cycles + 1):
        cycle_results = []
        for task_type in rewarder.working_task_types:
            success, balance, message = rewarder.claim_reward(task_type)
            cycle_results.append({
                'task_type': task_type,
                'success': success,
                'message': message,
                'balance': balance
            })
            if success:
                total_claimed += rewarder.reward_amount
            time.sleep(1)
        
        results.append({
            'cycle': cycle,
            'results': cycle_results
        })
        
        if cycle < cycles:
            time.sleep(delay)
    
    return jsonify({
        'success': True,
        'results': results,
        'total_claimed': total_claimed
    })

if __name__ == '__main__':
    app.run(debug=True)