#!/bin/bash
set -e
ufw allow from 192.168.1.0/24 to any port 8123 proto tcp
ufw allow from 192.168.1.0/24 to any port 6052 proto tcp
ufw allow from 192.168.1.0/24 to any port 5353 proto udp
ufw allow from 192.168.1.0/24 to any port 1400 proto tcp   # Sonos pushes state to Home Assistant
ufw status numbered
