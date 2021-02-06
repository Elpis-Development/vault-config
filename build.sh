#!/bin/bash

docker build -t elpis/vault-init:1.0.0 .

read -r -n 1 -p "Press any key to proceed..."