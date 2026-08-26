<h1 align="center">💀 RETRO MCP KALI ☠️</h1>
<p align="center">
  <b>The Ultimate Unrestricted MCP Server for Kali Linux</b>
</p>
<p align="center">
  <a href="https://github.com/yourusername/RETRO-MCP-KALI/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  </a>
  <img src="https://img.shields.io/badge/Kali-268BEE?logo=kalilinux&logoColor=white" alt="Kali">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/version-1.0.0-red" alt="Version">
  <img src="https://img.shields.io/badge/status-stable-brightgreen" alt="Status">
</p>

---

## 🔥 What is RETRO MCP KALI?

**RETRO MCP KALI** is a **fully unrestricted** MCP (Model Context Protocol) server that exposes **all Kali Linux tools** over **Streamable HTTP**. Designed for AI‑powered penetration testing, CTF challenges, and offensive security automation – with **no safety filters, no restrictions, and full root power**.

> ⚠️ **WARNING** – **This server gives unrestricted root access to your Kali machine.**  
> There are **no safety filters** – you can run **any command**, including destructive ones.  
> **USE ONLY IN ISOLATED, CONTROLLED ENVIRONMENTS.**  
> The author is **NOT responsible** for any damage or legal consequences.

---

## 📱 Works with Rikkhahub on Android

**RETRO MCP KALI** is built to work seamlessly with **[Rikkhahub](https://play.google.com/store/apps/details?id=me.rerere.rikkahub)** – a powerful AI chat client for Android that supports MCP servers over Streamable HTTP.

<a href="https://play.google.com/store/apps/details?id=me.rerere.rikkahub">
  <img src="https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png" alt="Get it on Google Play" width="200">
</a>

### Connect Rikkhahub to RETRO MCP KALI

1. Open Rikkhahub on your Android device.
2. Go to **Settings → MCP Servers**.
3. Add a new server with:
   - **Transport Type**: Streamable HTTP
   - **Server URL**: `http://<YOUR_KALI_IP>:8000/mcp`
   - **Enable**: ON
4. Save and start chatting with your AI assistant – it now has full Kali Linux access!

---

## 🧠 Why RETRO MCP KALI?

- ✅ **Complete Tool Access** – All Kali tools exposed as MCP tools.
- 🚫 **No Restrictions** – Execute any command, install any package, run any exploit.
- ⏳ **Async Jobs** – Run long‑running scans in the background and poll for results.
- 📁 **File Operations** – Upload, download, list, and delete files directly.
- 🌐 **Streamable HTTP** – Works with Rikkhahub, Claude Desktop, 5ire, and any MCP client.
- ⚡ **One‑Command Setup** – Install and run with a single command: `retro-mcp-kali`.

---

## 🚀 Quick Start

### One‑Line Install (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/RETRO-MCP-KALI/main/setup.sh | sudo bash
