#!/usr/bin/env bash
# NetPulse Installer — Termux (Android)
# No sudo here — Termux runs as a user process.
# For packet capture / ARP scan you need a rooted device.
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
echo -e "${YELLOW}       WiFi Network Intelligence Suite — Termux Installer${NC}"
echo ""

# ── verify we're in Termux ──
if [ -z "$TERMUX_VERSION" ] && [ ! -d "/data/data/com.termux" ]; then
    echo -e "${YELLOW}[!] This script is for Termux. Kali users: use ../netpulse/install.sh${NC}"
fi

# ── update pkg index ──
echo -e "${CYAN}[*] Updating package index...${NC}"
pkg update -y -q

# ── system packages ──
echo -e "${CYAN}[*] Installing system packages...${NC}"
pkg install -y -q \
    python \
    nmap \
    iproute2 \
    libpcap \
    termux-api

# ── pip (no venv — Termux Python is already isolated) ──
echo -e "${CYAN}[*] Upgrading pip...${NC}"
pip install --upgrade pip -q

echo -e "${CYAN}[*] Installing Python packages...${NC}"
pip install -r requirements.txt -q

echo ""
echo -e "${GREEN}[✓] Done!${NC}"
echo ""
echo -e "${YELLOW}Feature availability on Termux:${NC}"
echo -e "  ${GREEN}✓${NC}  Dashboard, Bandwidth, Logs"
echo -e "  ${GREEN}✓${NC}  WiFi info  (via termux-wifi-connectioninfo)"
echo -e "  ${GREEN}✓${NC}  Nearby AP scan  (via termux-wifi-scaninfo)"
echo -e "  ${YELLOW}~${NC}  Packet capture  (rooted device only)"
echo -e "  ${YELLOW}~${NC}  DNS monitor     (rooted device only)"
echo -e "  ${YELLOW}~${NC}  ARP scanner     (rooted device only)"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo "  python main.py"
echo ""
echo -e "${CYAN}  Rooted? Run:  su -c 'python main.py'  for full features.${NC}"

