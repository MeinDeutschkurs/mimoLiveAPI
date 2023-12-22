from flask import Flask, jsonify
import subprocess
import configparser

# Function to load configuration from an INI file
def load_config(filename):
    config = configparser.ConfigParser()
    try:
        config.read(filename)
        return config
    except FileNotFoundError:
        print(f"Config file '{filename}' not found.")
        exit(1)

# Load configuration from the INI file
config = load_config('../config.ini')

if config:
    # Get BASE_URL from the configuration
    SERVER_PORT = float(config.get('SCRIPT', 'SERVER_PORT', fallback='8888'))

app = Flask(__name__)

@app.route('/<path:script>', strict_slashes=False)
def run_python_script(script):
    global SERVER_PORT
    # create path
    script_path = f"./modules/{script}.py"
    try:
        result = subprocess.run(["python3", script_path, "--matrix"], capture_output=True, text=True, check=True)
        output = result.stdout
        response_data = {'output': output}
    except Exception as e:
        response_data = {'error': str(e)}
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='localhost', port=SERVER_PORT)
