from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Welcome to the Flask Server!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)