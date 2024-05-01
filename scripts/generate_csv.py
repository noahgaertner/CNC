#!/usr/bin/python3
import csv
import itertools
import argparse

def generate_csv(num_nodes, process_file_name, output_csv_name):
    # Reading the process file names from a text file
    with open("/users/ngaertne/CNC/workload_lists/"+process_file_name, 'r') as file:
        process_files = [line.strip() for line in file.readlines()]

    # Define the shared_percentage values
    shared_percentages = list(set(list(range(0, 101, 25))+list(range(0,101,10))))
    

    # Create combinations of shared_percentage and process_file
    combinations = list(itertools.product(shared_percentages, process_files))
    ignore_count=0

    # Write to CSV
    with open("/users/ngaertne/CNC/run_lists/"+output_csv_name, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['node_number', 'shared_percentage', 'process_file', 'num_cores', 'num_clusters'])
        
        # Write each combination to the CSV, assigning node_number based on row index
        for index, (percentage, proc_file) in enumerate(combinations):
            if(num_nodes==1):
                node_number = 0
                writer.writerow([node_number, percentage, proc_file, 16, 4])
            else:
                if (proc_file=="/users/ngaertne/CNC/workloads/gapbs_all_cores.csv" or proc_file=="/users/ngaertne/CNC/workloads/4xgapbs.csv"):
                    node_number = 0
                    writer.writerow([node_number, percentage, proc_file, 16, 4])
                    ignore_count+=1
                else:
                    node_number = ((index-ignore_count) % (num_nodes-1))+1
                    writer.writerow([node_number, percentage, proc_file, 16, 4])

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Generate a CSV file with node configurations.")
    parser.add_argument("num_nodes", type=int, help="The number of nodes")
    parser.add_argument("process_file_name", type=str, help="Name of the file containing the workload list (in Workload_List Folder)")
    parser.add_argument("output_csv_name", type=str, help="Name of the output CSV file (in run_lists Folder)")
    
    args = parser.parse_args()

    # Generate the CSV
    generate_csv(args.num_nodes, args.process_file_name, args.output_csv_name)

if __name__ == "__main__":
    main()
