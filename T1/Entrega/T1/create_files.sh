#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <NUMBER OF FILES> <SIZE OF EACH FILE> <DIRECTORY NAME>"
  exit 1
fi

num_files=$1
file_size=$2
dir_name="${3}_files"

# Create the directory if it does not exist
mkdir -p "$dir_name"

# Create the specified number of files with the given size and .bin extension
for i in $(seq 1 "$num_files"); do
  dd if=/dev/urandom of="${dir_name}/file$i.bin" bs="${file_size}M" count=1
done