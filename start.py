#!/usr/bin/env python3
import os
import subprocess
import sys
import platform

def run_command(command, cwd=None):
    if platform.system() == "Windows":
        return subprocess.Popen(command, cwd=cwd, shell=True)
    else:
        return subprocess.Popen(command, cwd=cwd, shell=False)

def start_project():
    # Detect environment
    if platform.system() == "Windows":
        venv_python = os.path.join("venv", "Scripts", "python.exe")
        venv_pip = os.path.join("venv", "Scripts", "pip.exe")
    else:
        venv_python = os.path.join("venv", "bin", "python")
        venv_pip = os.path.join("venv", "bin", "pip")

    # Ensure venv exists
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        subprocess.run([venv_pip, "install", "-r", "requirements.txt"], check=True)

    # Ensure frontend dependencies
    if not os.path.exists(os.path.join("frontend", "node_modules")):
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd="frontend", shell=(platform.system() == "Windows"), check=True)

    # Start services
    print("Starting backend...")
    backend = run_command([venv_python, "-m", "uvicorn", "backend.main:app", "--reload"])
    
    print("Starting frontend...")
    frontend = run_command(["npm", "run", "dev"], cwd="frontend")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend.terminate()
        frontend.terminate()

if __name__ == "__main__":
    start_project()
