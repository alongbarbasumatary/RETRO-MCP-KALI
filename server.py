#!/usr/bin/env python3
"""
RETRO MCP KALI – Ultimate MCP Server for Kali
No restrictions, full root, all tools, async, file ops.
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, Optional

import requests
from mcp.server.fastmcp import FastMCP

# ------------------ Logging ------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# ------------------ Configuration ------------------
DEFAULT_KALI_API = "http://localhost:5000"
DEFAULT_TIMEOUT = 300
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

# ------------------ Kali API Client (no filters) ------------------
class KaliToolsClient:
    def __init__(self, api_url: str, timeout: int = DEFAULT_TIMEOUT):
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        logger.info(f"Kali API client → {self.api_url}")

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.api_url}/{endpoint}"
        try:
            resp = requests.post(url, json=data, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {"error": str(e), "success": False}

    def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.api_url}/{endpoint}"
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "success": False}

    # ---------- Synchronous tools ----------
    def nmap(self, target, scan_type="-sV", ports="", additional_args=""):
        return self._post("api/tools/nmap", {"target": target, "scan_type": scan_type, "ports": ports, "additional_args": additional_args})

    def gobuster(self, url, mode="dir", wordlist="/usr/share/wordlists/dirb/common.txt", additional_args=""):
        return self._post("api/tools/gobuster", {"url": url, "mode": mode, "wordlist": wordlist, "additional_args": additional_args})

    def dirb(self, url, wordlist="/usr/share/wordlists/dirb/common.txt", additional_args=""):
        return self._post("api/tools/dirb", {"url": url, "wordlist": wordlist, "additional_args": additional_args})

    def nikto(self, target, additional_args=""):
        return self._post("api/tools/nikto", {"target": target, "additional_args": additional_args})

    def sqlmap(self, url, data="", additional_args=""):
        return self._post("api/tools/sqlmap", {"url": url, "data": data, "additional_args": additional_args})

    def metasploit(self, module, options={}):
        return self._post("api/tools/metasploit", {"module": module, "options": options})

    def hydra(self, target, service, username="", username_file="", password="", password_file="", additional_args=""):
        return self._post("api/tools/hydra", {"target": target, "service": service, "username": username, "username_file": username_file, "password": password, "password_file": password_file, "additional_args": additional_args})

    def john(self, hash_file, wordlist="/usr/share/wordlists/rockyou.txt", format_type="", additional_args=""):
        return self._post("api/tools/john", {"hash_file": hash_file, "wordlist": wordlist, "format": format_type, "additional_args": additional_args})

    def wpscan(self, url, additional_args=""):
        return self._post("api/tools/wpscan", {"url": url, "additional_args": additional_args})

    def enum4linux(self, target, additional_args="-a"):
        return self._post("api/tools/enum4linux", {"target": target, "additional_args": additional_args})

    # ---------- New sync tools ----------
    def msfvenom(self, payload, lhost, lport="4444", format="exe", output="/tmp/payload.exe", additional_args=""):
        return self._post("api/tools/msfvenom", {"payload": payload, "lhost": lhost, "lport": lport, "format": format, "output": output, "additional_args": additional_args})

    def hashcat(self, hash_file, wordlist="/usr/share/wordlists/rockyou.txt", hash_type="0", additional_args=""):
        return self._post("api/tools/hashcat", {"hash_file": hash_file, "wordlist": wordlist, "hash_type": hash_type, "additional_args": additional_args})

    def amass(self, target, mode="enum", additional_args=""):
        return self._post("api/tools/amass", {"target": target, "mode": mode, "additional_args": additional_args})

    def subfinder(self, target, additional_args=""):
        return self._post("api/tools/subfinder", {"target": target, "additional_args": additional_args})

    def nuclei(self, target, templates="", additional_args=""):
        return self._post("api/tools/nuclei", {"target": target, "templates": templates, "additional_args": additional_args})

    # ---------- File operations ----------
    def upload_file(self, local_path):
        with open(local_path, 'rb') as f:
            files = {'file': f}
            resp = requests.post(f"{self.api_url}/api/file/upload", files=files, timeout=self.timeout)
            return resp.json()

    def download_file(self, remote_path):
        resp = requests.post(f"{self.api_url}/api/file/download", json={"path": remote_path}, timeout=self.timeout)
        if resp.status_code == 200:
            return {"success": True, "content": resp.content}
        else:
            return {"error": "Download failed", "status": resp.status_code}

    def list_files(self, path="/tmp"):
        return self._post("api/file/list", {"path": path})

    def delete_file(self, path):
        return self._post("api/file/delete", {"path": path})

    # ---------- Async ----------
    def async_start(self, tool, params):
        return self._post(f"api/async/{tool}", params)

    def async_result(self, job_id):
        return self._get(f"api/job/{job_id}")

    # ---------- Raw command (no restrictions) ----------
    def execute_command(self, command):
        return self._post("api/command", {"command": command})

    def health(self):
        try:
            resp = requests.get(f"{self.api_url}/health", timeout=5)
            return resp.json() if resp.ok else {"status": "unreachable"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

# ------------------ MCP Server ------------------
def create_mcp_server(api_client: KaliToolsClient) -> FastMCP:
    mcp = FastMCP("RETRO MCP KALI", instructions="No restrictions – full power.")

    # ---------- Synchronous tools ----------
    @mcp.tool()
    def nmap_scan(target: str, scan_type: str = "-sV", ports: str = "", additional_args: str = "") -> Dict:
        return api_client.nmap(target, scan_type, ports, additional_args)

    @mcp.tool()
    def gobuster_scan(url: str, mode: str = "dir", wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict:
        return api_client.gobuster(url, mode, wordlist, additional_args)

    @mcp.tool()
    def dirb_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict:
        return api_client.dirb(url, wordlist, additional_args)

    @mcp.tool()
    def nikto_scan(target: str, additional_args: str = "") -> Dict:
        return api_client.nikto(target, additional_args)

    @mcp.tool()
    def sqlmap_scan(url: str, data: str = "", additional_args: str = "") -> Dict:
        return api_client.sqlmap(url, data, additional_args)

    @mcp.tool()
    def metasploit_run(module: str, options: Dict[str, Any] = {}) -> Dict:
        return api_client.metasploit(module, options)

    @mcp.tool()
    def hydra_attack(target: str, service: str, username: str = "", username_file: str = "", password: str = "", password_file: str = "", additional_args: str = "") -> Dict:
        return api_client.hydra(target, service, username, username_file, password, password_file, additional_args)

    @mcp.tool()
    def john_crack(hash_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt", format_type: str = "", additional_args: str = "") -> Dict:
        return api_client.john(hash_file, wordlist, format_type, additional_args)

    @mcp.tool()
    def wpscan_analyze(url: str, additional_args: str = "") -> Dict:
        return api_client.wpscan(url, additional_args)

    @mcp.tool()
    def enum4linux_scan(target: str, additional_args: str = "-a") -> Dict:
        return api_client.enum4linux(target, additional_args)

    # ---------- New sync tools ----------
    @mcp.tool()
    def msfvenom_generate(payload: str, lhost: str, lport: str = "4444", format: str = "exe", output: str = "/tmp/payload.exe", additional_args: str = "") -> Dict:
        return api_client.msfvenom(payload, lhost, lport, format, output, additional_args)

    @mcp.tool()
    def hashcat_crack(hash_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt", hash_type: str = "0", additional_args: str = "") -> Dict:
        return api_client.hashcat(hash_file, wordlist, hash_type, additional_args)

    @mcp.tool()
    def amass_enum(target: str, mode: str = "enum", additional_args: str = "") -> Dict:
        return api_client.amass(target, mode, additional_args)

    @mcp.tool()
    def subfinder_enum(target: str, additional_args: str = "") -> Dict:
        return api_client.subfinder(target, additional_args)

    @mcp.tool()
    def nuclei_scan(target: str, templates: str = "", additional_args: str = "") -> Dict:
        return api_client.nuclei(target, templates, additional_args)

    # ---------- File operations ----------
    @mcp.tool()
    def upload_file_to_kali(local_path: str) -> Dict:
        """Upload a file from the local filesystem to Kali."""
        return api_client.upload_file(local_path)

    @mcp.tool()
    def download_file_from_kali(remote_path: str) -> Dict:
        """Download a file from Kali (returns binary content)."""
        return api_client.download_file(remote_path)

    @mcp.tool()
    def list_directory(path: str = "/tmp") -> Dict:
        return api_client.list_files(path)

    @mcp.tool()
    def delete_file_on_kali(path: str) -> Dict:
        return api_client.delete_file(path)

    # ---------- Async tools (all tools have async versions) ----------
    @mcp.tool()
    def nmap_scan_async(target: str, scan_type: str = "-sV", ports: str = "", additional_args: str = "") -> Dict:
        params = {"target": target, "scan_type": scan_type, "ports": ports, "additional_args": additional_args}
        return api_client.async_start("nmap", params)

    @mcp.tool()
    def gobuster_scan_async(url: str, mode: str = "dir", wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict:
        params = {"url": url, "mode": mode, "wordlist": wordlist, "additional_args": additional_args}
        return api_client.async_start("gobuster", params)

    @mcp.tool()
    def ffuf_scan_async(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict:
        params = {"url": url, "wordlist": wordlist, "additional_args": additional_args}
        return api_client.async_start("ffuf", params)

    @mcp.tool()
    def whatweb_async(target: str, additional_args: str = "") -> Dict:
        params = {"target": target, "additional_args": additional_args}
        return api_client.async_start("whatweb", params)

    @mcp.tool()
    def searchsploit_async(query: str, additional_args: str = "") -> Dict:
        params = {"query": query, "additional_args": additional_args}
        return api_client.async_start("searchsploit", params)

    @mcp.tool()
    def crackmapexec_async(target: str, module: str, options: str = "") -> Dict:
        params = {"target": target, "module": module, "options": options}
        return api_client.async_start("crackmapexec", params)

    @mcp.tool()
    def bloodhound_async(domain: str, username: str, password: str, dc_ip: str, additional_args: str = "") -> Dict:
        params = {"domain": domain, "username": username, "password": password, "dc_ip": dc_ip, "additional_args": additional_args}
        return api_client.async_start("bloodhound", params)

    @mcp.tool()
    def msfvenom_async(payload: str, lhost: str, lport: str = "4444", format: str = "exe", output: str = "/tmp/payload.exe", additional_args: str = "") -> Dict:
        params = {"payload": payload, "lhost": lhost, "lport": lport, "format": format, "output": output, "additional_args": additional_args}
        return api_client.async_start("msfvenom", params)

    @mcp.tool()
    def hashcat_async(hash_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt", hash_type: str = "0", additional_args: str = "") -> Dict:
        params = {"hash_file": hash_file, "wordlist": wordlist, "hash_type": hash_type, "additional_args": additional_args}
        return api_client.async_start("hashcat", params)

    @mcp.tool()
    def amass_async(target: str, mode: str = "enum", additional_args: str = "") -> Dict:
        params = {"target": target, "mode": mode, "additional_args": additional_args}
        return api_client.async_start("amass", params)

    @mcp.tool()
    def subfinder_async(target: str, additional_args: str = "") -> Dict:
        params = {"target": target, "additional_args": additional_args}
        return api_client.async_start("subfinder", params)

    @mcp.tool()
    def nuclei_async(target: str, templates: str = "", additional_args: str = "") -> Dict:
        params = {"target": target, "templates": templates, "additional_args": additional_args}
        return api_client.async_start("nuclei", params)

    @mcp.tool()
    def get_job_result(job_id: str) -> Dict:
        """Poll for the result of an async job."""
        return api_client.async_result(job_id)

    # ---------- Raw command execution ----------
    @mcp.tool()
    def execute_command(command: str) -> Dict:
        """Execute ANY command on Kali (no restrictions)."""
        return api_client.execute_command(command)

    @mcp.tool()
    def server_health() -> Dict:
        return api_client.health()

    return mcp

# ------------------ Main ------------------
def main():
    parser = argparse.ArgumentParser(description="RETRO MCP KALI – Ultimate MCP Server")
    parser.add_argument("--api", default=DEFAULT_KALI_API, help="Kali API server URL")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Bind port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    client = KaliToolsClient(args.api)
    health = client.health()
    if "error" in health:
        logger.warning(f"Kali API unreachable: {health.get('error')}")
    else:
        logger.info(f"Kali API healthy: {health.get('status')}")

    mcp = create_mcp_server(client)

    os.environ["MCP_HOST"] = args.host
    os.environ["MCP_PORT"] = str(args.port)
    if hasattr(mcp, "settings"):
        mcp.settings.host = args.host
        mcp.settings.port = args.port

    logger.info(f"Starting RETRO MCP KALI on http://{args.host}:{args.port}/mcp")
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
