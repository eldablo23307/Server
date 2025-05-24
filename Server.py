from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/")
def home():
    file_list = os.system("ls home/mottu/file")
    print(x for x in file_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)