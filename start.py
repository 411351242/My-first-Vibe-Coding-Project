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
    venv_dir = None
    for d in [".venv", "venv"]:
        if os.path.exists(d):
            venv_dir = d
            break
            
    if venv_dir:
        if platform.system() == "Windows":
            venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
            venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            venv_python = os.path.join(venv_dir, "bin", "python")
            venv_pip = os.path.join(venv_dir, "bin", "pip")
    else:
        # Default to .venv if none exist
        print("No virtual environment found. Defaulting to creating .venv...")
        venv_dir = ".venv"
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        if platform.system() == "Windows":
            venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
            venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            venv_python = os.path.join(venv_dir, "bin", "python")
            venv_pip = os.path.join(venv_dir, "bin", "pip")
        subprocess.run([venv_pip, "install", "-r", "requirements.txt"], check=True)

    # Ensure frontend dependencies
    if not os.path.exists(os.path.join("frontend", "node_modules")):
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd="frontend", shell=(platform.system() == "Windows"), check=True)

    # Start services
    print("Starting backend (127.0.0.1:8000)...")
    backend = run_command([venv_python, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"])
    
    print("Starting frontend (Vite)...")
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
