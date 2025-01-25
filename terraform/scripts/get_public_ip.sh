#!/bin/bash
set -e

# Get public IP from current computer
public_ip="$(curl -4 ifconfig.me)"

# Output data in the required format
jq -n --arg public_ip "$public_ip" '{"public_ip": $public_ip}'
