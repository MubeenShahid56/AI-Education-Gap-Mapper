import subprocess
import sys
import os

def start_server():
    print("Starting AI Education Gap Mapper App...")
    print("Open: http://127.0.0.1:5000")
    # Check if we are running in our virtual environment, if not, use the correct interpreter
    venv_python = os.path.join('.venv', 'bin', 'python')
    if os.path.exists(venv_python) and sys.executable != os.path.abspath(venv_python):
        print(f"Relaunching server within virtual environment: {venv_python}")
        try:
            # Launch the Flask app inside the virtualenv by importing and running it.
            # Running `app.py` directly only executes top-level statements (which load assets)
            # but does not call `app.app.run(...)`. Import and run the Flask app instead.
            subprocess.run([
                venv_python,
                '-c',
                "import app; app.app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)"
            ])
        except KeyboardInterrupt:
            print("\nServer stopped.")
    else:
        # If already in venv or venv not found, run directly
        import app
        app.app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    start_server()
