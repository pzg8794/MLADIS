import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)


def build_agent_reply(user_message: str) -> str:
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not openai_api_key:
        return "Agent is online, but no OPENAI_API_KEY is set yet."

    return f"Echo: {user_message} (booking agent stub)"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/agent", methods=["POST"])
def agent():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    return jsonify({"reply": build_agent_reply(user_message)})


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
