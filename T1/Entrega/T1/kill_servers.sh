#!/bin/bash

# Ports to be checked
ports=(1818 1819 1820)

# Iterate over each port
for port in "${ports[@]}"
do
  echo "Checking port $port..."

  # Find the PID associated with the port
  pid=$(lsof -ti :$port)

  # Check if there is a process running on the port
  if [ -n "$pid" ]; then
    echo "Killing process $pid running on port $port..."
    kill -9 $pid
    echo "Process $pid killed."
  else
    echo "No process running on port $port."
  fi
done

echo "All specified servers on ports ${ports[@]} have been checked."
