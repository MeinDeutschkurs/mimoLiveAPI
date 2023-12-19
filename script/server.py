from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/<path:script>', strict_slashes=False)
def run_python_script(script):
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
    app.run(host='localhost', port=8888)
