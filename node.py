import json
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
    "type": "hello",
    "version": "0.8.0",
    "agent": "Kerma−Core Client 0.8"
})

app.run()