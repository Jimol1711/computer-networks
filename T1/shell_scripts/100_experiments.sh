#!/bin/bash

echo "Running local echo 2 100 small" >> ../times_100small_files.txt
date >> times_100small_files.txt
./local_echo2_100small.sh >> times_100small_files.txt
echo -e "\n\n" >> times_100small_files.txt
./clean_trash.sh

echo "Running local echo 4 100 small" >> times_100small_files.txt
date >> times_100small_files.txt
./local_echo4_100small.sh >> times_100small_files.txt
echo -e "\n\n" >> times_100small_files.txt
./clean_trash.sh

echo "Running local echo 5 100 small" >> times_100small_files.txt
date >> times_100small_files.txt
./local_echo5_100small.sh >> times_100small_files.txt
echo -e "\n\n" >> times_100small_files.txt
./clean_trash.sh
