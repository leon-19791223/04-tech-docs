#!/bin/bash
# Auto-generated partition script by DWS Assistant
# WARNING: This will erase all data on target disks!
# Cluster: dwsuat — Generated: 2026-06-06 11:30:50

set -e

echo '=== Partitioning /dev/sdb ==='
parted -s /dev/sdb mklabel gpt
parted -s /dev/sdb mkpart primary 0% 100%
mkfs.xfs -f -n ftype=1 -L data1 /dev/sdb1

echo '=== Partitioning /dev/sdc ==='
parted -s /dev/sdc mklabel gpt
parted -s /dev/sdc mkpart primary 0% 100%
mkfs.xfs -f -n ftype=1 -L data2 /dev/sdc1

echo '=== Partitioning /dev/sdd ==='
parted -s /dev/sdd mklabel gpt
parted -s /dev/sdd mkpart primary 0% 100%
mkfs.xfs -f -n ftype=1 -L data3 /dev/sdd1

echo '=== Partitioning /dev/sde ==='
parted -s /dev/sde mklabel gpt
parted -s /dev/sde mkpart primary 0% 100%
mkfs.xfs -f -n ftype=1 -L data4 /dev/sde1

echo '=== Partitioning /dev/sdf ==='
parted -s /dev/sdf mklabel gpt
parted -s /dev/sdf mkpart primary 0% 100%
mkfs.xfs -f -n ftype=1 -L data5 /dev/sdf1

echo '=== Partitioning /dev/sdg ==='
parted -s /dev/sdg mklabel gpt
parted -s /dev/sdg mkpart primary 0% 100%
mkfs.xfs -f -n ftype=1 -L data6 /dev/sdg1

