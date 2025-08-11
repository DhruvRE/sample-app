from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "UP"}), 200

@app.route("/user", methods=["GET"])
def get_user():
    return jsonify({
        "id": 1,
        "name": "DhruvRE",
        "role": "Developer"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
