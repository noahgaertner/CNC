# README

## How to Run

Use make - 

Environment Variables:

TARGET_WORKLOAD = the relative path of the workload you want to run from the workload_lists folder

NODE_COUNT = number of nodes in the experiment

EXP_NAME = name of the experiment


Targets:

help:Shows help menu

clean:Cleans up the files created during the experiment without deleting the results

gen-run-list:Generates the csv file containing the list of runs

parse:Parses the results of the experiment

run-clean:Cleans up the files created during the experiment without deleting the results, then runs and parses on a single node (0)

run:Runs the experiments on a single node

run-parallel-clean:Cleans up the files created during the experiment without deleting the results, then runs on all nodes and parses on Node 0 (should finish last)

run-parallel:Runs the experiments on all nodes

run-parallel-veryclean:Cleans up the files created during the experiment and deletes the results, then runs on all nodes and parses on Node 0

run-veryclean:Cleans up the files created during the experiment and deletes the results, then runs and parses on a single node (0)

veryclean:Cleans up the files created during the experiment and deletes the results
