from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    file_list = subprocess.check_output("ls ./file", shell=True, text=True)
    print(file_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)