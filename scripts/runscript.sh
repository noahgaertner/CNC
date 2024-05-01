#!/bin/bash

# Check hostname and parse for {number}
/users/ngaertne/CNC/scripts/modified_setup.sh
hostname=$(hostname)
number=$(echo $hostname | cut -d'.' -f1 | sed 's/h//')
exp_name=$(echo $HOSTNAME | cut -d'.' -f2)
FAIL_FLAG=0
zero=0
# Path to progress file
if [[ ! -d /users/ngaertne/progress/${exp_name} ]]; then
    mkdir /users/ngaertne/CNC/progress/${exp_name}
fi
if [[ ! -d /users/ngaertne/monitoring/${exp_name} ]]; then
    mkdir /users/ngaertne/CNC/monitoring/${exp_name}
fi
if [[ ! -d /users/ngaertne/progress/${exp_name} ]]; then
    mkdir /users/ngaertne/CNC/progress/${exp_name}
fi
if [[ ! -d /proj/s24-18-742/tests/noah_test/${exp_name} ]]; then
    mkdir /proj/s24-18-742/tests/noah_test/${exp_name}
fi
if [[ ! -d /users/ngaertne/CNC/zsim/tests/${exp_name} ]]; then
    mkdir /users/ngaertne/CNC/zsim/tests/${exp_name}
fi
progress_file="/users/ngaertne/CNC/progress/${exp_name}/${number}_progress.txt"
# echo $progress_file
# Check if progress file exists, if not create it
if [ ! -f "$progress_file" ]; then
    echo "0" > "$progress_file"
fi

# Read the number from the progress file
num_prog=$(cat $progress_file)

# Path to the log file
log_file="/users/ngaertne/CNC/dispatch_logs/${exp_name}.log"

# Read the CSV filename from the script arguments
csv_file=$1
csv_file_path="/users/ngaertne/CNC/run_lists/${csv_file}"  # Ensuring the path is expanded here correctly

# Start the loop
while true; do
    # Read matching rows from the CSV
    mapfile -t matching_rows < <(awk -F, -v num="$number" '$1 == num' "$csv_file_path")

    # Check if num_prog is valid
    if [ "$num_prog" -ge "${#matching_rows[@]}" ]; then
        if [[ $FAIL_COUNT -eq $zero ]]; then
            echo "Node $number has finished executing all assigned tasks successfully" >> "$log_file"
        else
            echo "Node $number has finished executing all assigned tasks with $FAIL_COUNT errors" >> "$log_file"
        fi
        break
    fi

    # Get the specific row based on num_prog
    IFS=',' read -ra row <<< "${matching_rows[$num_prog]}"

    shared_percentage="${row[1]}"
    process_file="${row[2]}"
    workload_name=$(basename "$process_file" .csv)
    num_cores="${row[3]}"
    num_clusters="${row[4]}"

    # Generate configuration
    "/users/ngaertne/CNC/scripts/cfggen.py" "$shared_percentage" "$process_file" "$num_cores" "$num_clusters" "/users/ngaertne/CNC/zsim/tests/${exp_name}/${shared_percentage}_${workload_name}.cfg"
    cd "/proj/s24-18-742/tests/noah_test/${exp_name}"
    mkdir "${shared_percentage}_${workload_name}"
    cd "${shared_percentage}_${workload_name}"
    # Determine the tests being run based on process file content
    found=false  # Variable to track if any condition was met

    if grep -q "gapbs" "$process_file"; then
        echo "Running gapbs test"
        ln -s "/proj/s24-18-742/tests/noah_test/gapbs" .        
        rm -rf gapbs/benchmark/out/*
        found=true
    fi

    if grep -q "spec" "$process_file"; then
        echo "Running spec tests"
        found=true
    fi

    if [ "$found" = false ]; then
        echo "Running custom tests"
    fi

    # Execute zsim with the generated configuration and write output to file in real-time, not showing in console
    "/users/ngaertne/CNC/zsim/build/opt/zsim" "/users/ngaertne/CNC/zsim/tests/${exp_name}/${shared_percentage}_${workload_name}.cfg" > "/users/ngaertne/CNC/monitoring/${exp_name}/${shared_percentage}_${workload_name}.out" 2>&1

    # Read the output from the file and check for errors
    if grep -q -i "ERROR" "/users/ngaertne/CNC/monitoring/${exp_name}/${shared_percentage}_${workload_name}.out"; then
        echo "ERROR on Node $number while executing Workload $workload_name with Shared Percentage $shared_percentage%" >> "$log_file"
        FAIL_COUNT=$((FAIL_COUNT+1))
    elif grep -q -i "FATAL" "/users/ngaertne/CNC/monitoring/${exp_name}/${shared_percentage}_${workload_name}.out"; then
        echo "FATAL on Node $number while executing Workload $workload_name with Shared Percentage $shared_percentage%" >> "$log_file"
        FAIL_COUNT=$((FAIL_COUNT+1))
    elif grep -q -i "PANIC" "/users/ngaertne/CNC/monitoring/${exp_name}/${shared_percentage}_${workload_name}.out"; then
        echo "PANIC on Node $number while executing Workload $workload_name with Shared Percentage $shared_percentage%" >> "$log_file"
        FAIL_COUNT=$((FAIL_COUNT+1))
    elif grep -q -i "No Such" "/users/ngaertne/CNC/monitoring/${exp_name}/${shared_percentage}_${workload_name}.out"; then
        echo "Can't find file on Node $number while executing Workload $workload_name with Shared Percentage $shared_percentage%" >> "$log_file"
        FAIL_COUNT=$((FAIL_COUNT+1))
    elif grep -q -i "Permission Denied" "/users/ngaertne/CNC/monitoring/${exp_name}/${shared_percentage}_${workload_name}.out"; then
        echo "Permission Error on Node $number while executing Workload $workload_name with Shared Percentage $shared_percentage%" >> "$log_file"
        FAIL_COUNT=$((FAIL_COUNT+1))
    else
        echo "Node $number succesfully executed Workload $workload_name with Shared Percentage $shared_percentage%" >> "$log_file"
    fi

    # Increment num_prog and update the file
    ((num_prog++))
    echo "$num_prog" > "$progress_file"
done
if [[ $(number) -eq 0 ]]; then
    cd /users/ngaertne/CNC
    make parse EXP_NAME=${exp_name}
fi