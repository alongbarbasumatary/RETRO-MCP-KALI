
#!/usr/bin/env python3
# RETRO MCP KALI – Backend API (Ultimate, No Restrictions)

import argparse
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import traceback
import threading
import shutil
import uuid
import time
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from typing import Dict, Any, Optional

# ------------------ Logging ------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ------------------ Configuration ------------------
API_PORT = int(os.environ.get("API_PORT", 5000))
DEBUG_MODE = os.environ.get("DEBUG_MODE", "0").lower() in ("1", "true", "yes", "y")
COMMAND_TIMEOUT = 180
ASYNC_TIMEOUT = 600

# ------------------ Flask App ------------------
app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/mcp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ Command Executor ------------------
class CommandExecutor:
    def __init__(self, command, timeout: int = COMMAND_TIMEOUT):
        self.command = command
        self.timeout = timeout
        self.use_shell = isinstance(command, str)
        self.process = None
        self.stdout_data = ""
        self.stderr_data = ""
        self.stdout_thread = None
        self.stderr_thread = None
        self.return_code = None
        self.timed_out = False

    def _read_stdout(self):
        for line in iter(self.process.stdout.readline, ''):
            self.stdout_data += line

    def _read_stderr(self):
        for line in iter(self.process.stderr.readline, ''):
            self.stderr_data += line

    def execute(self) -> Dict[str, Any]:
        logger.info(f"Executing: {self.command}")
        try:
            self.process = subprocess.Popen(
                self.command,
                shell=self.use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.stdout_thread = threading.Thread(target=self._read_stdout)
            self.stderr_thread = threading.Thread(target=self._read_stderr)
            self.stdout_thread.daemon = True
            self.stderr_thread.daemon = True
            self.stdout_thread.start()
            self.stderr_thread.start()

            try:
                self.return_code = self.process.wait(timeout=self.timeout)
                self.stdout_thread.join()
                self.stderr_thread.join()
            except subprocess.TimeoutExpired:
                self.timed_out = True
                logger.warning(f"Timeout after {self.timeout}s")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                self.return_code = -1

            success = True if self.timed_out and (self.stdout_data or self.stderr_data) else (self.return_code == 0)
            return {
                "stdout": self.stdout_data,
                "stderr": self.stderr_data,
                "return_code": self.return_code,
                "success": success,
                "timed_out": self.timed_out,
                "partial_results": self.timed_out and (self.stdout_data or self.stderr_data)
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {
                "stdout": self.stdout_data,
                "stderr": f"Error: {str(e)}\n{self.stderr_data}",
                "return_code": -1,
                "success": False,
                "timed_out": False,
                "partial_results": bool(self.stdout_data or self.stderr_data)
            }

def execute_command(command) -> Dict[str, Any]:
    executor = CommandExecutor(command)
    return executor.execute()

# ------------------ Job Manager (Async) ------------------
jobs = {}
job_lock = threading.Lock()

def run_job(job_id, command, timeout=ASYNC_TIMEOUT):
    with job_lock:
        jobs[job_id]["status"] = "running"
    try:
        result = CommandExecutor(command, timeout).execute()
        with job_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["result"] = result
    except Exception as e:
        with job_lock:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["result"] = {"error": str(e), "success": False}

def start_async_job(command) -> str:
    job_id = str(uuid.uuid4())
    with job_lock:
        jobs[job_id] = {"status": "queued", "result": None, "created_at": time.time()}
    thread = threading.Thread(target=run_job, args=(job_id, command))
    thread.daemon = True
    thread.start()
    return job_id

# ------------------ Helper: build_command for async ----------
def build_command(tool: str, params: Dict) -> Optional[str]:
    if tool == "nmap":
        target = params.get("target", "")
        scan_type = params.get("scan_type", "-sV")
        ports = params.get("ports", "")
        additional = params.get("additional_args", "")
        cmd = f"nmap {scan_type}"
        if ports: cmd += f" -p {ports}"
        if additional: cmd += f" {additional}"
        cmd += f" {target}"
        return cmd
    elif tool == "gobuster":
        url = params.get("url", "")
        mode = params.get("mode", "dir")
        wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        additional = params.get("additional_args", "")
        cmd = f"gobuster {mode} -u {url} -w {wordlist}"
        if additional: cmd += f" {additional}"
        return cmd
    elif tool == "ffuf":
        url = params.get("url", "")
        wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        additional = params.get("additional_args", "")
        cmd = f"ffuf -u {url} -w {wordlist}"
        if additional: cmd += f" {additional}"
        return cmd
    elif tool == "whatweb":
        target = params.get("target", "")
        additional = params.get("additional_args", "")
        cmd = f"whatweb {target}"
        if additional: cmd += f" {additional}"
        return cmd
    elif tool == "searchsploit":
        query = params.get("query", "")
        additional = params.get("additional_args", "")
        cmd = f"searchsploit {query}"
        if additional: cmd += f" {additional}"
        return cmd
    elif tool == "crackmapexec":
        target = params.get("target", "")
        module = params.get("module", "")
        options = params.get("options", "")
        cmd = f"crackmapexec {module} {target} {options}"
        return cmd
    elif tool == "bloodhound":
        domain = params.get("domain", "")
        username = params.get("username", "")
        password = params.get("password", "")
        dc_ip = params.get("dc_ip", "")
        additional = params.get("additional_args", "")
        cmd = f"bloodhound-python -u {username} -p {password} -d {domain} -ns {dc_ip}"
        if additional: cmd += f" {additional}"
        return cmd
    elif tool == "msfvenom":
        payload = params.get("payload", "windows/meterpreter/reverse_tcp")
        lhost = params.get("lhost", "")
        lport = params.get("lport", "4444")
        format_type = params.get("format", "exe")
        output = params.get("output", "/tmp/payload.exe")
        additional = params.get("additional_args", "")
        if not lhost:
            return None
        os.makedirs(os.path.dirname(output), exist_ok=True)
        cmd = f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} -f {format_type} -o {output}"
        if additional:
            cmd += f" {additional}"
        return cmd
    elif tool == "hashcat":
        hash_file = params.get("hash_file", "")
        wordlist = params.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        hash_type = params.get("hash_type", "0")
        additional = params.get("additional_args", "")
        if not hash_file:
            return None
        cmd = f"hashcat -m {hash_type} -a 0 {hash_file} {wordlist}"
        if additional: cmd += f" {additional}"
        return cmd
    elif tool == "amass":
        target = params.get("target", "")
        mode = params.get("mode", "enum")
        additional = params.get("additional_args", "")
        if not target:
            return None
        cmd = f"amass {mode} -d {target}"
        if additional: cmd += f" {additional}"
        return cmd
    elif tool == "subfinder":
        target = params.get("target", "")
        additional = params.get("additional_args", "")
        if not target:
            return None
        cmd = f"subfinder -d {target}"
        if additional: cmd += f" {additional}"
        return cmd
    elif tool == "nuclei":
        target = params.get("target", "")
        templates = params.get("templates", "")
        additional = params.get("additional_args", "")
        if not target:
            return None
        cmd = f"nuclei -u {target}"
        if templates: cmd += f" -t {templates}"
        if additional: cmd += f" {additional}"
        return cmd
    else:
        return None

# ==================== ROUTES ====================

# ---------- Generic command ----------
@app.route("/api/command", methods=["POST"])
def generic_command():
    params = request.json
    command = params.get("command", "")
    if not command:
        return jsonify({"error": "Command required"}), 400
    result = execute_command(command)
    return jsonify(result)

# ---------- Original tool endpoints (keep as before) ----------
@app.route("/api/tools/nmap", methods=["POST"])
def nmap():
    params = request.json
    target = params.get("target", "")
    scan_type = params.get("scan_type", "-sCV")
    ports = params.get("ports", "")
    additional = params.get("additional_args", "-T4 -Pn")
    if not target:
        return jsonify({"error": "Target required"}), 400
    cmd = ["nmap"] + shlex.split(scan_type)
    if ports:
        cmd += ["-p", ports]
    if additional:
        cmd += shlex.split(additional)
    cmd.append(target)
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/gobuster", methods=["POST"])
def gobuster():
    params = request.json
    url = params.get("url", "")
    mode = params.get("mode", "dir")
    wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
    additional = params.get("additional_args", "")
    if not url:
        return jsonify({"error": "URL required"}), 400
    if mode not in ["dir", "dns", "fuzz", "vhost"]:
        return jsonify({"error": "Invalid mode"}), 400
    cmd = ["gobuster", mode, "-u", url, "-w", wordlist]
    if additional:
        cmd += shlex.split(additional)
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/dirb", methods=["POST"])
def dirb():
    params = request.json
    url = params.get("url", "")
    wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
    additional = params.get("additional_args", "")
    if not url:
        return jsonify({"error": "URL required"}), 400
    cmd = ["dirb", url, wordlist]
    if additional:
        cmd += shlex.split(additional)
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/nikto", methods=["POST"])
def nikto():
    params = request.json
    target = params.get("target", "")
    additional = params.get("additional_args", "")
    if not target:
        return jsonify({"error": "Target required"}), 400
    cmd = ["nikto", "-h", target]
    if additional:
        cmd += shlex.split(additional)
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/sqlmap", methods=["POST"])
def sqlmap():
    params = request.json
    url = params.get("url", "")
    data = params.get("data", "")
    additional = params.get("additional_args", "")
    if not url:
        return jsonify({"error": "URL required"}), 400
    cmd = ["sqlmap", "-u", url, "--batch"]
    if data:
        cmd += ["--data", data]
    if additional:
        cmd += shlex.split(additional)
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/metasploit", methods=["POST"])
def metasploit():
    params = request.json
    module = params.get("module", "")
    options = params.get("options", {})
    if not module:
        return jsonify({"error": "Module required"}), 400
    if not re.match(r'^[a-zA-Z0-9/_-]+$', module):
        return jsonify({"error": "Invalid module"}), 400
    resource_content = f"use {module}\n"
    for key, value in options.items():
        if not re.match(r'^[a-zA-Z0-9_]+$', str(key)):
            return jsonify({"error": f"Invalid option: {key}"}), 400
        resource_content += f"set {key} {value}\n"
    resource_content += "exploit\n"
    resource_file = "/tmp/mks_msf_resource.rc"
    with open(resource_file, "w") as f:
        f.write(resource_content)
    cmd = ["msfconsole", "-q", "-r", resource_file]
    result = execute_command(cmd)
    try:
        os.remove(resource_file)
    except:
        pass
    return jsonify(result)

@app.route("/api/tools/hydra", methods=["POST"])
def hydra():
    params = request.json
    target = params.get("target", "")
    service = params.get("service", "")
    username = params.get("username", "")
    username_file = params.get("username_file", "")
    password = params.get("password", "")
    password_file = params.get("password_file", "")
    additional = params.get("additional_args", "")
    if not target or not service:
        return jsonify({"error": "Target and service required"}), 400
    if not (username or username_file) or not (password or password_file):
        return jsonify({"error": "Username/Password required"}), 400
    cmd = ["hydra", "-t", "4"]
    if username:
        cmd += ["-l", username]
    elif username_file:
        cmd += ["-L", username_file]
    if password:
        cmd += ["-p", password]
    elif password_file:
        cmd += ["-P", password_file]
    cmd += [target, service]
    if additional:
        cmd += shlex.split(additional)
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/john", methods=["POST"])
def john():
    params = request.json
    hash_file = params.get("hash_file", "")
    wordlist = params.get("wordlist", "/usr/share/wordlists/rockyou.txt")
    format_type = params.get("format", "")
    additional = params.get("additional_args", "")
    if not hash_file:
        return jsonify({"error": "Hash file required"}), 400
    cmd = ["john"]
    if format_type:
        cmd.append(f"--format={format_type}")
    if wordlist:
        cmd.append(f"--wordlist={wordlist}")
    if additional:
        cmd += shlex.split(additional)
    cmd.append(hash_file)
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/wpscan", methods=["POST"])
def wpscan():
    params = request.json
    url = params.get("url", "")
    additional = params.get("additional_args", "")
    if not url:
        return jsonify({"error": "URL required"}), 400
    cmd = ["wpscan", "--url", url]
    if additional:
        cmd += shlex.split(additional)
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/enum4linux", methods=["POST"])
def enum4linux():
    params = request.json
    target = params.get("target", "")
    additional = params.get("additional_args", "-a")
    if not target:
        return jsonify({"error": "Target required"}), 400
    cmd = ["enum4linux"] + shlex.split(additional) + [target]
    result = execute_command(cmd)
    return jsonify(result)

# ---------- New sync tool endpoints ----------
@app.route("/api/tools/msfvenom", methods=["POST"])
def msfvenom():
    params = request.json
    payload = params.get("payload", "windows/meterpreter/reverse_tcp")
    lhost = params.get("lhost", "")
    lport = params.get("lport", "4444")
    format_type = params.get("format", "exe")
    output = params.get("output", "/tmp/payload.exe")
    additional = params.get("additional_args", "")
    if not lhost:
        return jsonify({"error": "lhost required"}), 400
    if shutil.which("msfvenom") is None:
        return jsonify({"error": "msfvenom not found. Install metasploit-framework."}), 500
    os.makedirs(os.path.dirname(output), exist_ok=True)
    cmd = f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} -f {format_type} -o {output}"
    if additional:
        cmd += f" {additional}"
    logger.info(f"msfvenom cmd: {cmd}")
    result = execute_command(cmd)
    if result.get("success"):
        result["output_file"] = output
    return jsonify(result)

@app.route("/api/tools/hashcat", methods=["POST"])
def hashcat():
    params = request.json
    hash_file = params.get("hash_file", "")
    wordlist = params.get("wordlist", "/usr/share/wordlists/rockyou.txt")
    hash_type = params.get("hash_type", "0")
    additional = params.get("additional_args", "")
    if not hash_file:
        return jsonify({"error": "hash_file required"}), 400
    cmd = f"hashcat -m {hash_type} -a 0 {hash_file} {wordlist}"
    if additional:
        cmd += f" {additional}"
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/amass", methods=["POST"])
def amass():
    params = request.json
    target = params.get("target", "")
    mode = params.get("mode", "enum")
    additional = params.get("additional_args", "")
    if not target:
        return jsonify({"error": "target required"}), 400
    cmd = f"amass {mode} -d {target}"
    if additional:
        cmd += f" {additional}"
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/subfinder", methods=["POST"])
def subfinder():
    params = request.json
    target = params.get("target", "")
    additional = params.get("additional_args", "")
    if not target:
        return jsonify({"error": "target required"}), 400
    cmd = f"subfinder -d {target}"
    if additional:
        cmd += f" {additional}"
    result = execute_command(cmd)
    return jsonify(result)

@app.route("/api/tools/nuclei", methods=["POST"])
def nuclei():
    params = request.json
    target = params.get("target", "")
    templates = params.get("templates", "")
    additional = params.get("additional_args", "")
    if not target:
        return jsonify({"error": "target required"}), 400
    cmd = f"nuclei -u {target}"
    if templates:
        cmd += f" -t {templates}"
    if additional:
        cmd += f" {additional}"
    result = execute_command(cmd)
    return jsonify(result)

# ---------- File operations ----------
@app.route("/api/file/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No filename"}), 400
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return jsonify({"filename": filename, "path": path, "success": True})

@app.route("/api/file/download", methods=["POST"])
def download_file():
    data = request.json
    path = data.get("path")
    if not path or not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True)

@app.route("/api/file/list", methods=["POST"])
def list_files():
    data = request.json
    path = data.get("path", "/tmp")
    if not os.path.isdir(path):
        return jsonify({"error": "Directory not found"}), 404
    files = os.listdir(path)
    return jsonify({"path": path, "files": files})

@app.route("/api/file/delete", methods=["POST"])
def delete_file():
    data = request.json
    path = data.get("path")
    if not path or not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    os.remove(path)
    return jsonify({"success": True, "deleted": path})

                        
