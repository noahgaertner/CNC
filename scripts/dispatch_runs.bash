#! /usr/bin/env bash

SCREEN_NAME="zsim_sweep"
RUN_NAME=${1?Run List Name Missed!}
HOSTNAME=$(hostname)
HOSTNAME=${HOSTNAME%.narwhal*}
POSTFIX=${HOSTNAME#*.}

ALL_HOSTS=$(emulab-listall --separator ' ')
echo "All hosts: ${ALL_HOSTS}"
for h in ${ALL_HOSTS}
do
    (set -x; ssh ${h}.${POSTFIX} "screen -S ${SCREEN_NAME} -dm bash -c '/users/ngaertne/CNC/scripts/runscript.sh $RUN_NAME'")
done
