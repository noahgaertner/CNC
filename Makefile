default: help
.PHONY: help
TARGET_WORKLOAD ?= full_wl_list#is the name of the workload list file that you want to run
NODE_COUNT ?= 128 #is the number of nodes that you want to run the experiments on
EXP_NAME ?= $(EXP_NAME) #is the name of the node that you want to run on
TEST_DIRS = $(shell find tests/$(EXP_NAME)/ -type d)
TEST_FILES = $(shell find tests/$(EXP_NAME)/ -type f -name '*')
help:
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done
gen-run-list: workload_lists/$(TARGET_WORKLOAD).txt #Generates the csv file containing the list of runs
		@echo "TARGET_WORKLOAD: $(TARGET_WORKLOAD)"
	python3 scripts/generate_csv.py $(NODE_COUNT) $(TARGET_WORKLOAD).txt $(TARGET_WORKLOAD).csv 
clean: #Cleans up the files created during the experiment without deleting the results
	rm -rf configs/$(EXP_NAME)  monitoring/$(EXP_NAME) progress/$(EXP_NAME) dispatch_logs/$(EXP_NAME).log
veryclean: clean #Cleans up the files created during the experiment and deletes the results
	rm -rf tests/$(EXP_NAME) configs/$(EXP_NAME) results/$(EXP_NAME) run_lists/*
parse: tests $(TEST_DIRS) $(TEST_FILES) #Parses the results of the experiment
	rm -rf results/$(EXP_NAME)
	mkdir results/$(EXP_NAME)
	python3.8 scripts/parse-results-cmd.py $(EXP_NAME) 
run: gen-run-list #Runs the experiments on a single node
	scripts/runscript.sh $(TARGET_WORKLOAD).csv
run-parallel: gen-run-list #Runs the experiments on all nodes
	scripts/dispatch_runs.bash $(TARGET_WORKLOAD).csv
run-parallel-clean:clean gen-run-list run-parallel #Cleans up the files created during the experiment without deleting the results, then runs on all nodes and parses on Node 0 (should finish last)
run-parallel-veryclean:veryclean gen-run-list run-parallel #Cleans up the files created during the experiment and deletes the results, then runs on all nodes and parses on Node 0
run-clean: clean gen-run-list run #Cleans up the files created during the experiment without deleting the results, then runs and parses on a single node (0)
run-veryclean: veryclean gen-run-list run #Cleans up the files created during the experiment and deletes the results, then runs and parses on a single node (0)