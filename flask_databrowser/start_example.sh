#! /bin/bash


if [ $# != 1 ]
then
    echo "Usage: start_example.sh example_name"
    exit
fi

cd examples/$1
python basemain.py
cd ../../
