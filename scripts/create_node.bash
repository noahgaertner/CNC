#! /usr/bin/env bash

EXPERIMENT_NAME=${1?Experiment name missed!}
NUM_NODES=${2:-1}
PROJECT_NAME="s24-18-742"
OS_IMAGE_NAME="ubuntu-18-zsim"

/share/testbed/bin/wf-makebed -n ${NUM_NODES} -e ${EXPERIMENT_NAME} -p ${PROJECT_NAME} -i ${OS_IMAGE_NAME} -s /share/testbed/bin/linux-autofs-ldap

for i in $(seq 0 $(( NUM_NODES - 1 )))
do
    ssh h${i}.${EXPERIMENT_NAME}.${PROJECT_NAME} 'screen -S stress_screen -dm stress -c 1'
done

exit
