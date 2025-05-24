from flask import Flask, request
import os

app = Flask(__name__)
print(os.listdir("file"))

@app.route("/")
def home():
    file_list = os.listdir("file")
    print(file_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)