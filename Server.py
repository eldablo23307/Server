from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Welcome to the Flask Server!"
