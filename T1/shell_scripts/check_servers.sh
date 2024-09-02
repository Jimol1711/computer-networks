#!/bin/bash

echo "Checking servers..."

# Check port 1818
ss -tuln | grep :1818

# Check port 1819
ss -tuln | grep :1819

# Check port 1820
ss -tuln | grep :1820