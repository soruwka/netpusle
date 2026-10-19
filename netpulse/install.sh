#!/usr/bin/env bash
# NetPulse Installer — Kali Linux / Debian-based systems
set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo " ███╗   ██╗███████╗████████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗"
echo " ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝"
echo " ██╔██╗ ██║█████╗     ██║   ██████╔╝██║   ██║██║     ███████╗█████╗  "
echo " ██║╚██╗██║██╔══╝     ██║   ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝  "
echo " ██║ ╚████║███████╗   ██║   ██║     ╚██████╔╝███████╗███████║███████╗"
echo " ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝"
echo -e "${NC}"
echo -e "${YELLOW}          WiFi Network Intelligence Suite — Installer${NC}"
echo ""

# ── check python3 ──
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[!] python3 not found. Installing...${NC}"
    sudo apt-get update -q && sudo apt-get install -y python3 python3-pip
fi

# ── install system deps ──
echo -e "${CYAN}[*] Installing system dependencies...${NC}"
sudo apt-get install -y -q \
    wireless-tools \
    network-manager \
    iproute2 \
    nmap \
    libpcap-dev 2>/dev/null || true

# ── create virtualenv ──
echo -e "${CYAN}[*] Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# ── pip install ──
echo -e "${CYAN}[*] Installing Python packages...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo -e "${GREEN}[✓] Installation complete!${NC}"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo "  source venv/bin/activate"
echo "  sudo python3 main.py"
echo ""
echo -e "${CYAN}  (root required for packet capture & ARP scanning)${NC}"
