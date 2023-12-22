#!/bin/bash

echo "Please wait.... (approx 10 sec)"
python repo_health.py
read -n 1 -p "Press 'r' to rerun the script, or any other key to exit: " input
if [ "$input" == "r" ]; then
    exec "$0" "$@"
fi