from flask import Flask, request
import os

app = Flask(__name__)

def file_in_directory(path: str) -> list:
    file_list = os.listdir(f"/home/mottu/{path}")
    if file_list == None:
        return ["Cartella Vuota"]
    else:
        return file_list

@app.route("/")
def home():
    return file_in_directory("file")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)