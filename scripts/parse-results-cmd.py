import os
import subprocess
import shutil
import argparse
from datetime import datetime
import h5py
import numpy as np

################################
########## HELPER FNS ##########
################################

def assertFileExists(filePath):
    if not os.path.isfile(filePath):
        print("File:", filePath, "does not exist.")
        return False

def assertDirExists(dirPath):
    if not os.path.isdir(dirPath):
        print("Directory:", dirPath, "does not exist.")
        return False

def get_directories_in_folder(folder_path):
    directories = []
    for entry in os.listdir(folder_path):
        entry_path = os.path.join(folder_path, entry)
        if os.path.isdir(entry_path):
            directories.append(entry)
    return directories

# Get the values
def getStatValue(statPointer, index, parameter, beginIndex=0):
    return np.array(statPointer[index][parameter][-1]) - np.array(statPointer[index][parameter][beginIndex])

def find_nth(str_in, sub_str, n):
    start = str_in.find(sub_str)
    while start >= 0 and n > 1:
        start = str_in.find(sub_str, start+len(sub_str))
        n -= 1
    return start

def getValFromLineN(filename, n):
    with open(filename, "r") as f:
        for i, line in enumerate(f):
            if i == n:
                return int(''.join(line.split(":")[1].split("#")[0]))
    return None

def main(node_name):
    baseDir = "/users/ngaertne/CNC/"
    # runDir = os.path.join(baseDir, "zsim")
    testDir = os.path.join(baseDir, "tests", node_name)
    # cfgsDir = os.path.join(runDir, "tests", node_name)
    resultDir= os.path.join(baseDir, "results", node_name)

    tests = get_directories_in_folder(testDir)
    print(tests)

    os.chdir(testDir)
    zsimh5 = open(os.path.join(resultDir, f"results_zsim_h_{node_name}.csv"), "w")
    fzsimout = open(os.path.join(resultDir, f"results_zsim_out_{node_name}.csv"), "w")

    names_idx = 0

    # write headers to csv files
    zsimh5.write("Test Name" + "," + "Benchmark" + ","  + "Percentage" + "," + "Max Cycle Count" + "\n")
    fzsimout.write("Test Name" + "," + "Benchmark" + "," + "Percentage" + "," + "AMAT" + "," + "Max Cycle Count" + "," + 
                    "L3 Accesses" + "," + "L2 Private Hit Rate" + "," + "L2 Shared Hit Rate" + "," + 
                    "L2 MPKI" + ",L2S MPKI"+",L2P MPKI"+ "\n")
    percentages = []
    for test in tests:
        idx = test.find("_")
        benchmark = test[idx+1:]
        percentage = test[:idx]

        os.chdir(os.path.join(testDir, test))

        # Parse h5
        stat_file = "zsim.h5"
        try:
            stats = h5py.File(stat_file, 'r')
            stats = stats['stats']['root']
            total_cycles = []
            total_instrs = []
            try:
                for i in range(16):
                    total_cycles.append(max(getStatValue(stats, f"c{i}", "cycles"))) # Is this correct?
                    total_instrs.append(max(getStatValue(stats, f"c{i}", "instrs")))
            except IndexError:
                print(f"FAILED to parse {test} (index error, probably size is 0)")
            if (len(total_cycles) == 0):
                zsimh5.write(test + "," + benchmark + "," + percentage + "," + "no_data" + "\n")
            else:
                zsimh5.write(test + "," + benchmark + "," + percentage + "," + str(max(total_cycles)) + "\n")
        except FileNotFoundError:
            print(f"FAILED to parse {test} (zsim.h5 doesn't exist)")

        # Parse zsim.out
        stat_file = "zsim.out"

        try:
            zout = open(stat_file, "r")

            l1lat = 4
            l2plat = 7
            l2slat = 3
            l3lat = 27
            memlat = 40

            l1ihits = []
            l1dhits = []
            l1imiss = []
            l1dmiss = []

            l2phits = []
            l2pmiss = []
            l2shits = []
            l2smiss = []

            l3hits = []
            l3miss = []

            cyc_counts = []

            l1icount = 0
            l1dcount = 0
            l2pcount = 0
            l2scount = 0
            l3count = 0
            core_count = 0

            cluster_0_inst_count = 0            
            cluster_1_inst_count = 0
            cluster_2_inst_count = 0
            cluster_3_inst_count = 0

            for i, line in enumerate(zout):
                miss_sum = 0
                hit_sum = 0
                cyc_count = 0
                if f"l1i{l1icount}-0" in line:
                    hit_sum += getValFromLineN(stat_file, i + 1)
                    hit_sum += getValFromLineN(stat_file, i + 2)
                    hit_sum += getValFromLineN(stat_file, i + 3)
                    hit_sum += getValFromLineN(stat_file, i + 4)
                    l1ihits.append(hit_sum)

                    miss_sum += getValFromLineN(stat_file, i + 5)
                    miss_sum += getValFromLineN(stat_file, i + 6)
                    miss_sum += getValFromLineN(stat_file, i + 7)
                    l1imiss.append(miss_sum)

                    l1icount += 1

                elif f"l1d{l1dcount}-0" in line:
                    hit_sum += getValFromLineN(stat_file, i + 1)
                    hit_sum += getValFromLineN(stat_file, i + 2)
                    hit_sum += getValFromLineN(stat_file, i + 3)
                    hit_sum += getValFromLineN(stat_file, i + 4)
                    l1dhits.append(hit_sum)

                    miss_sum += getValFromLineN(stat_file, i + 5)
                    miss_sum += getValFromLineN(stat_file, i + 6)
                    miss_sum += getValFromLineN(stat_file, i + 7)
                    l1dmiss.append(miss_sum)

                    l1dcount += 1
                
                elif f"l3-0b{l3count}" in line:
                    hit_sum += getValFromLineN(stat_file, i + 1)
                    hit_sum += getValFromLineN(stat_file, i + 2)
                    l3hits.append(hit_sum)

                    miss_sum += getValFromLineN(stat_file, i + 3)
                    miss_sum += getValFromLineN(stat_file, i + 4)
                    miss_sum += getValFromLineN(stat_file, i + 5)
                    l3miss.append(miss_sum)

                    l3count += 1

                elif f"c{core_count}-0" in line:
                    cyc_count += getValFromLineN(stat_file, i + 1)
                    cyc_count += getValFromLineN(stat_file, i + 2)
                    cyc_counts.append(cyc_count)

                    # Get instructions per cluster
                    if (core_count < 4):
                        cluster_0_inst_count += getValFromLineN(stat_file, i + 3)
                    elif (core_count < 8):
                        cluster_1_inst_count += getValFromLineN(stat_file, i + 3)
                    elif (core_count < 12): 
                        cluster_2_inst_count += getValFromLineN(stat_file, i + 3)
                    else:   
                        cluster_3_inst_count += getValFromLineN(stat_file, i + 3)
                    
                    core_count += 1

                # case on percentage in order to parse caches properly
                if percentage == "0":
                    if f"l2c{l2pcount}-0" in line:
                        hit_sum += getValFromLineN(stat_file, i + 1)
                        hit_sum += getValFromLineN(stat_file, i + 2)
                        l2phits.append(hit_sum)

                        miss_sum += getValFromLineN(stat_file, i + 3)
                        miss_sum += getValFromLineN(stat_file, i + 4)
                        miss_sum += getValFromLineN(stat_file, i + 5)
                        l2pmiss.append(miss_sum)

                        l2pcount += 1

                elif percentage == "100":
                    if f"l2c{l2scount}-0" in line:
                        hit_sum += getValFromLineN(stat_file, i + 1)
                        hit_sum += getValFromLineN(stat_file, i + 2)
                        l2shits.append(hit_sum)

                        miss_sum += getValFromLineN(stat_file, i + 3)
                        miss_sum += getValFromLineN(stat_file, i + 4)
                        miss_sum += getValFromLineN(stat_file, i + 5)
                        l2smiss.append(miss_sum)

                        l2scount += 1

                else:
                    if f"l2p{l2pcount}-0" in line:
                        hit_sum += getValFromLineN(stat_file, i + 1)
                        hit_sum += getValFromLineN(stat_file, i + 2)
                        l2phits.append(hit_sum)

                        miss_sum += getValFromLineN(stat_file, i + 3)
                        miss_sum += getValFromLineN(stat_file, i + 4)
                        miss_sum += getValFromLineN(stat_file, i + 5)
                        l2pmiss.append(miss_sum)

                        l2pcount += 1

                    elif f"l2sc{l2scount}-0" in line:
                        hit_sum += getValFromLineN(stat_file, i + 1)
                        hit_sum += getValFromLineN(stat_file, i + 2)
                        l2shits.append(hit_sum)

                        miss_sum += getValFromLineN(stat_file, i + 3)
                        miss_sum += getValFromLineN(stat_file, i + 4)
                        miss_sum += getValFromLineN(stat_file, i + 5)
                        l2smiss.append(miss_sum)

                        l2scount += 1

            # end of the file
            print("i: ", i)
            if (i < 10):
                fzsimout.write(test + "," + benchmark + "," + percentage + "," + "no_data" + "," + "no_data" + 
                               "," + "no_data" + "," + "no_data" + "," + "no_data" + "," + "no_data" + 
                               "," + "no_data" + "," + "no_data" + "\n")
                print(f"{test} has no data\n")
            else:
                sum_1hits = sum(l1ihits) + sum(l1dhits)
                sum_1miss = sum(l1imiss) + sum(l1dmiss)
                l1hr = sum_1hits / (sum_1hits + sum_1miss) if sum_1hits + sum_1miss != 0 else 0

                sum_phits = sum(l2phits)
                sum_pmiss = sum(l2pmiss)
                sum_shits = sum(l2shits)
                sum_smiss = sum(l2smiss)
                l2phr = sum_phits / (sum_phits + sum_pmiss) if sum_phits + sum_pmiss != 0 else 0
                l2shr = sum_shits / (sum_shits + sum_smiss) if sum_shits + sum_smiss != 0 else 0

                sum_3hits = sum(l3hits)
                sum_3miss = sum(l3miss)
                l3hr = sum_3hits / (sum_3hits + sum_3miss) if sum_3hits + sum_3miss != 0 else 0

                # average memory access time
                amat = l1hr * l1lat + (1 - l1hr) * (
                            l1lat + l2phr * l2plat + (1 - l2phr) * (
                                l2plat + l2shr * l2slat + (1 - l2shr) * (
                                    l2slat + l3hr * l3lat + (1 - l3hr) * (
                                        l3lat + memlat))))

                l3_accesses = sum_3hits + sum_3miss

                # calculate L1 MPKI
                total_instr = cluster_0_inst_count + cluster_1_inst_count + cluster_2_inst_count + cluster_3_inst_count
            
                L1_MPKI = sum_1miss / (total_instr / 1000)
                L2_MPKI = (sum_pmiss + sum_smiss) / (total_instr / 1000)
                L2S_MPKI = (sum_smiss)/(total_instr/1000)
                L2P_MPKI = (sum_pmiss)/(total_instr/1000)
                L3_MPKI = sum_3miss / (total_instr / 1000)

                # calculate IPC
                
                fzsimout.write(test + "," + benchmark + "," + percentage + "," + str(amat) + "," + str(
                    max(cyc_counts) if len(cyc_counts) > 0 else 0) + "," + str(l3_accesses) + "," + str(l2phr) + "," + str(l2shr) + "," + str(L2_MPKI) + "," + str(L2S_MPKI)+","+str(L2P_MPKI)+"\n")
                
                print(f"Parsed {test}\n")

        except FileNotFoundError:
            print(f"FAILED to parse {test} (zsim.out doesn't exist)")

        
        names_idx += 1

    zsimh5.close()
    fzsimout.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("node_name", help="Name of the node to process")
    args = parser.parse_args()
    main(args.node_name)
