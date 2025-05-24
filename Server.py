from flask import Flask, request, jsonify
import os

app = Flask(__name__)

def check_type(file: str):
    if "." in file:
        return "file"
    else:
        return "dir"

def file_in_directory(path: str):
    file_list = os.listdir(f"/home/mottu/{path}")
    json = []
    if file_list == None:
        return "Cartella Vuota"
    else:
        for i in range(len(file_list)):
            json.append({"file": file_list[i], "type": check_type(file_list[i])})

    return jsonify(json)

@app.route("/")
def home():
    return file_in_directory("file")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)