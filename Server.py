from flask import Flask, request
import os

app = Flask(__name__)

def file_in_directory() -> list:
    file_list = os.listdir("/home/mottu/file")
    return file_list

@app.route("/")
def home():
    lista_dir = ""
    for x in file_in_directory():
        lista_dir = f"{x}\n"
    
    return lista_dir



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)