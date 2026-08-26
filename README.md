# RETRO MCP KALI

**RETRO MCP KALI** is an **unrestricted** MCP (Model Context Protocol) server for Kali Linux.  
It exposes all major Kali tools (nmap, gobuster, metasploit, msfvenom, hashcat, etc.) over **Streamable HTTP**, making them accessible to any MCP client like **Rikkhahub**, Claude Desktop, or custom AI agents.

> ⚠️ **WARNING**: This server gives **full root access** to your Kali machine.  
> There are **no safety filters** – you can run any command, including destructive ones.  
> **USE ONLY IN ISOLATED, CONTROLLED ENVIRONMENTS.**

---

## 🔥 Features

- **All Kali tools** – nmap, gobuster, dirb, nikto, sqlmap, metasploit, hydra, john, wpscan, enum4linux.
- **Advanced tools** – ffuf, whatweb, searchsploit, crackmapexec, bloodhound.
- **New tools** – msfvenom, hashcat, amass, subfinder, nuclei.
- **Async jobs** – long-running tasks return a job ID; poll for results.
- **File operations** – upload, download, list, delete files.
- **Unrestricted `execute_command`** – run any shell command.
- **Streamable HTTP** – fully compatible with Rikkhahub.
- **No safety filters** – full power, no restrictions.

---

## 🚀 Quick Start

### 1. Install dependencies & tools

```bash
sudo apt update
sudo apt install -y nmap gobuster dirb nikto sqlmap metasploit-framework hydra john wpscan enum4linux ffuf whatweb exploitdb crackmapexec amass subfinder nuclei hashcat
pip install -r requirements.txt
