from flask import Flask, jsonify, request, abort

app = Flask(__name__)

TOKEN = "mvot-test-token-2026"
DEVICES = {
    "dev-001": {"id": "dev-001", "name": "Router-A", "status": "online"},
    "dev-002": {"id": "dev-002", "name": "Switch-B", "status": "offline"},
}
ALARMS = {
    "alm-001": {"id": "alm-001", "device_id": "dev-002", "severity": "critical", "resolved": False},
    "alm-002": {"id": "alm-002", "device_id": "dev-001", "severity": "warning",  "resolved": False},
}
SLA = {
    "dev-001": {"device_id": "dev-001", "uptime_percent": 99.95, "threshold": 99.9, "compliant": True},
    "dev-002": {"device_id": "dev-002", "uptime_percent": 87.50, "threshold": 99.9, "compliant": False},
}

def auth():
    if request.headers.get("Authorization") != f"Bearer {TOKEN}":
        abort(401, description="Invalid or missing token")

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/devices")
def devices():
    auth()
    return jsonify(list(DEVICES.values())), 200

@app.route("/devices/<id>")
def device(id):
    auth()
    return jsonify(DEVICES.get(id) or abort(404, description="Device not found")), 200

@app.route("/alarms")
def alarms():
    auth()
    return jsonify(list(ALARMS.values())), 200

@app.route("/alarms/<id>/resolve", methods=["POST"])
def resolve(id):
    auth()
    alarm = ALARMS.get(id) or abort(404, description="Alarm not found")
    alarm["resolved"] = True
    return jsonify(alarm), 200

@app.route("/sla/<device_id>")
def sla(device_id):
    auth()
    return jsonify(SLA.get(device_id) or abort(404, description="No SLA record found")), 200

@app.errorhandler(400)
def bad_request(e): return jsonify({"error": str(e.description)}), 400
@app.errorhandler(401)
def unauthorized(e): return jsonify({"error": str(e.description)}), 401
@app.errorhandler(404)
def not_found(e): return jsonify({"error": str(e.description)}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
