import os
import sys
import subprocess
import shutil
from datetime import datetime
import h5py
import numpy as np
# import tkinter as tk
# from scipy.stats import gmean
# test

runDir = '/users/ngaertne/CNC/zsim'
testDir = '/proj/s24-18-742/tests/noah_test' # this is where all the zsim files are created
cfgsDir = '/users/ngaertne/CNC/zsim/tests'

################################
########## HELPER FNS ##########
################################

def assertFileExists(filePath):
    if not os.path.isfile(filePath):
        print("File:", filePath, "does not exist.")
        return False

def assertDirExists(dirPath):
    if not os.path.isdir(dirPath):
        print("File:", dirPath, "does not exist.")
        return False
    
def get_directories_in_folder(folder_path):
    directories = []
    for entry in os.listdir(folder_path):
        #if ("initial" in entry):
        if ("initial" in entry):
            entry_path = os.path.join(folder_path, entry)
            if os.path.isdir(entry_path):
                directories.append(entry)
    return directories


# Get the values
def getStatValue(statPointer, index, parameter, beginIndex=0):
    return np.array(statPointer[index][parameter][-1]) - np.array(statPointer[index][parameter][beginIndex])

# From here: https://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string
def find_nth(str_in, sub_str, n):
    start = str_in.find(sub_str)
    while start >= 0 and n > 1:
        start = str_in.find(sub_str, start+len(sub_str))
        n -= 1
    return start

def getValFromLineN(filename, n):
    f = open(filename, "r")
    for i, line in enumerate(f):
        if (i == n):
            return int(''.join(line.split(":")[1].split("#")[0]))
    return None


##########################
########## MAIN ##########
##########################

# Each entry should follow syntax below
# initial-runs_shared%_workloadname
tests = get_directories_in_folder(testDir)
print(tests)

bench_sort = True

# Sort the tests
if bench_sort:
    test_dict = {}
    test_dict_sorted = {}
    for test in tests:
        idx_1 = find_nth(test, "_", 1)
        idx_2 = find_nth(test, "_", 2)
        percentage = test[idx_1+1:idx_2]
        # print(percentage)
        key = test[idx_2+1:] + '_' + percentage
        test_dict[key] = test
        

    # print(test_dict)

    keys = list(test_dict.keys())
    keys.sort()
    test_dict_sorted = {j: test_dict[j] for j in keys}

    tests = []
    names = []
    percentages = []
    for key in test_dict_sorted:
        tests.append(test_dict_sorted[key])
        names.append(key)
        idx = key.rfind("_")
        percentages.append(key[idx+1:])


os.chdir(testDir)
fcyc = open("results_cyc_copy.csv", "w")
# famat = open("results_miss.csv", "w")

names_idx = 0
for test in tests:
    # print(f"Parsing {test}")
    os.chdir(testDir + "/" +  test) # change directory to the run directory
    # print(testDir)
    # Parse h5
    stat_file = "zsim.h5"
    # assertFileExists(statFile)
    try:
        stats = h5py.File(stat_file, 'r')
        stats = stats['stats']['root']
        total_cycles = []
        try:
            for i in range(16): # 16 == NUM_CORES
                total_cycles.append(max(getStatValue(stats, f"c{i}", "cycles")))
                # print(getStatValue(stats, f"c{i}", "cycles"))
        except IndexError:
            print(f"FAILED to parse {test} (index error, probably size is 0)")
        
        # print(total_cycles)
        # print(str(total_cycles))
        # print(names[names_idx])
        fcyc.write(test + "," + names[names_idx] + "," + percentages[names_idx] + "," + str(max(total_cycles)) + "\n")
    except FileNotFoundError:
        print(f"FAILED to parse {test} (zsim.h5 doesn't exist)")

    # Parse zsim.out
    stat_file = "zsim.out"

    # TODO: get number of memory transactions below L1

    # try:
    #     zout = open(stat_file, "r")

    #     l1lat = 4
    #     l2plat = 7
    #     l2slat = 0
    #     l3lat = 27
    #     memlat = 40

    #     l1ihits = []
    #     l1dhits = []
    #     l1imiss = []
    #     l1dmiss = []

    #     l2phits = []
    #     l2pmiss = []
    #     l2shits = []
    #     l2smiss = []

    #     l3hits = []
    #     l3miss = []

    #     l1icount = 0
    #     l1dcount = 0
    #     l2pcount = 0
    #     l2scount = 0
    #     l3count = 0

    #     # TODO: 0 and 100 L2 is called l2c

    #     # extract all the numbers
    #     for i, line in enumerate(zout):
    #         miss_sum = 0
    #         hit_sum = 0
    #         if f"l1i{l1icount}-0" in line:
    #             hit_sum += getValFromLineN(stat_file, i + 1)
    #             hit_sum += getValFromLineN(stat_file, i + 2)
    #             hit_sum += getValFromLineN(stat_file, i + 3)
    #             hit_sum += getValFromLineN(stat_file, i + 4)
    #             l1ihits.append(hit_sum)

    #             miss_sum += getValFromLineN(stat_file, i + 5)
    #             miss_sum += getValFromLineN(stat_file, i + 6)
    #             miss_sum += getValFromLineN(stat_file, i + 7)
    #             l1imiss.append(miss_sum)

    #             l1icount += 1
    #         elif f"l1d{l1dcount}-0" in line:
    #             hit_sum += getValFromLineN(stat_file, i + 1)
    #             hit_sum += getValFromLineN(stat_file, i + 2)
    #             hit_sum += getValFromLineN(stat_file, i + 3)
    #             hit_sum += getValFromLineN(stat_file, i + 4)
    #             l1dhits.append(hit_sum)

    #             miss_sum += getValFromLineN(stat_file, i + 5)
    #             miss_sum += getValFromLineN(stat_file, i + 6)
    #             miss_sum += getValFromLineN(stat_file, i + 7)
    #             l1dmiss.append(miss_sum)

    #             l1dcount += 1
    #         elif f"l2p{l2pcount}-0" in line:
    #             hit_sum += getValFromLineN(stat_file, i + 1)
    #             hit_sum += getValFromLineN(stat_file, i + 2)
    #             l2phits.append(hit_sum)

    #             miss_sum += getValFromLineN(stat_file, i + 3)
    #             miss_sum += getValFromLineN(stat_file, i + 4)
    #             miss_sum += getValFromLineN(stat_file, i + 5)
    #             l2pmiss.append(miss_sum)

    #             l2pcount += 1
    #         elif f"l2sc{l2scount}-0" in line:
    #             hit_sum += getValFromLineN(stat_file, i + 1)
    #             hit_sum += getValFromLineN(stat_file, i + 2)
    #             l2shits.append(hit_sum)

    #             miss_sum += getValFromLineN(stat_file, i + 3)
    #             miss_sum += getValFromLineN(stat_file, i + 4)
    #             miss_sum += getValFromLineN(stat_file, i + 5)
    #             l2smiss.append(miss_sum)

    #             l2scount += 1
    #         # special case: 0 and 100 L2 is called l2c
    #         elif f"l2c{l2scount}-0" in line:
    #             hit_sum += getValFromLineN(stat_file, i + 1)
    #             hit_sum += getValFromLineN(stat_file, i + 2)
    #             l2shits.append(hit_sum)

    #             miss_sum += getValFromLineN(stat_file, i + 3)
    #             miss_sum += getValFromLineN(stat_file, i + 4)
    #             miss_sum += getValFromLineN(stat_file, i + 5)
    #             l2smiss.append(miss_sum)

    #             l2phits.append(0)
    #             l2pmiss.append(0)

    #         elif f"l3-0b{l3count}" in line:
    #             hit_sum += getValFromLineN(stat_file, i + 1)
    #             hit_sum += getValFromLineN(stat_file, i + 2)
    #             l3hits.append(hit_sum)

    #             miss_sum += getValFromLineN(stat_file, i + 3)
    #             miss_sum += getValFromLineN(stat_file, i + 4)
    #             miss_sum += getValFromLineN(stat_file, i + 5)
    #             l3miss.append(miss_sum)

    #             l3count += 1
            
        # print(l1ihits)
        # print(l1imiss)
        # print(l1dhits)
        # print(l1dmiss)
        # print(l2pmiss)
        # print(l2phits)
        # print(l2smiss)
        # print(l2shits)
        # print(l3hits)
        # print(l3miss)

        # Use numbers to compute amat
    #     sum_hits = 0
    #     sum_miss = 0
    #     for i in range(len(l1ihits)):
    #         sum_hits = sum_hits + l1ihits[i] + l1dhits[i]
    #         sum_miss = sum_miss + l1imiss[i] + l1dmiss[i]
    #     try:
    #         l1hr = sum_hits/(sum_hits + sum_miss)
    #     except ZeroDivisionError:
    #         print("ERROR: div by 0 for L1")
    #         print(f"Hits: {sum_hits}")
    #         print(f"Miss: {sum_miss}")
    #         l1hr = 0

    #     sum_phits = 0
    #     sum_pmiss = 0
    #     sum_shits = 0
    #     sum_smiss = 0
    #     for i in range(len(l2phits)):
    #         sum_phits += l2phits[i]
    #         sum_pmiss += l2pmiss[i]
    #     for i in range(len(l2shits)):
    #         sum_shits += l2shits[i]
    #         sum_smiss += l2smiss[i]
    #     try:
    #         l2phr = (sum_phits)/(sum_phits + sum_pmiss)
    #         l2shr = (sum_shits)/(sum_shits + sum_smiss)
    #     except ZeroDivisionError:
    #         print("ERROR: div by 0 for L2")
    #         print(f"phits: {sum_phits}")
    #         print(f"pmiss: {sum_pmiss}")
    #         print(f"shits: {sum_shits}")
    #         print(f"smiss: {sum_smiss}")
    #         l2phr = 0
    #         l2shr = 0

    #     sum_3hits = 0
    #     sum_3miss = 0
    #     for i in range(len(l3hits)):
    #         sum_3hits += l3hits[i]
    #         sum_3miss += l3miss[i]
    #     try:
    #         l3hr = (sum_3hits) / (sum_3hits + sum_3miss)
    #     except ZeroDivisionError:
    #         print("ERROR: div by 0 for L3")
    #         print(f"hits: {sum_3hits}")
    #         print(f"miss: {sum_3miss}")
    #         l3hr = 0

    #     print(f"l1hr: {l1hr}")
    #     print(f"l2phr: {l2phr}")
    #     print(f"l2shr: {l2shr}")
    #     print(f"l3hr: {l3hr}")


    #     amat = l1hr * l1lat + (1-l1hr)*(l1lat + l2phr*l2plat + (1-l2phr)*(l2plat + l2shr*l2slat + (1-l2shr)*(l2slat + l3hr*l3lat + (1-l3hr)*(l3lat + memlat))))

    #     # famat.write(test + "," + names[names_idx] + "," + str(amat) + "\n")

    # except FileNotFoundError:
    #     print(f"FAILED to parse {test} (zsim.out doesn't exist)")

    print(f"Parsed {test}\n")
    names_idx += 1

fcyc.close()
# famat.close()
