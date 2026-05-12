import subprocess
import sys

def run(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_capture=True, text=True)
        print(f"--- {cmd} ---")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
    except Exception as e:
        print(f"Failed To Run {cmd}: {e}")

run("docker ps -a")
