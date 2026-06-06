#!/bin/bash
# Auto-generated network configuration script by DWS Assistant
# Cluster: dwsuat

# --- dwsuat0001 ---
ssh dwsuat0001 'nmcli con mod bond1 ipv4.addresses 10.134.21.190/24'
ssh dwsuat0001 'nmcli con mod bond4 ipv4.addresses 10.134.21.190/24'

# --- dwsuat0002 ---
ssh dwsuat0002 'nmcli con mod bond1 ipv4.addresses 10.134.21.191/24'
ssh dwsuat0002 'nmcli con mod bond4 ipv4.addresses 10.134.21.191/24'

# --- dwsuat0003 ---
ssh dwsuat0003 'nmcli con mod bond1 ipv4.addresses 10.134.21.192/24'
ssh dwsuat0003 'nmcli con mod bond4 ipv4.addresses 10.134.21.192/24'

