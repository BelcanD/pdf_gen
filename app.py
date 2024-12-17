from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/<path:path>')
def catch_all(path):
    return f"Path {path} not found", 404

# Only for local development
if __name__ == '__main__':
    app.run(debug=True) 