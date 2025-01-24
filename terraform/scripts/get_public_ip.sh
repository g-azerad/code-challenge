#!/bin/bash
set -e

# Get public IP from current computer
public_ip="$(dig +short myip.opendns.com @resolver1.opendns.com)"

# Output data in the required format
jq -n --arg public_ip "$public_ip" '{"public_ip": $public_ip}'
