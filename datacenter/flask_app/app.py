from flask import Flask
import random

app = Flask(__name__)

@app.route('/')
def home():
    # Simulate some work
    x = [random.random() for _ in range(10000)]
    return "<h1>Datacenter Site B: Linux Server is Active</h1>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)