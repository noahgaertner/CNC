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
    runDir = os.path.join(baseDir, "zsim")
    testDir = os.path.join(baseDir, "tests", node_name)
    cfgsDir = os.path.join(runDir, "tests", node_name)
    resultDir= os.path.join(baseDir, "results", node_name)

    tests = get_directories_in_folder(testDir)
    print(tests)

    bench_sort = True

    if bench_sort:
        test_dict = {}
        test_dict_sorted = {}

        for test in tests:
            idx = find_nth(test, "_", 2) + 1
            key = test[idx:] + test[idx-4:idx]
            test_dict[key] = test

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
    fcyc = open(os.path.join(resultDir, "results_cyc.csv"), "w")
    famat = open(os.path.join(resultDir, "results_miss.csv"), "w")

    names_idx = 0
    for test in tests:
        os.chdir(os.path.join(testDir, test))

        # Parse h5
        stat_file = "zsim.h5"
        try:
            stats = h5py.File(stat_file, 'r')
            stats = stats['stats']['root']
            total_cycles = []
            try:
                for i in range(16):
                    total_cycles.append(max(getStatValue(stats, f"c{i}", "cycles")))
            except IndexError:
                print(f"FAILED to parse {test} (index error, probably size is 0)")

            fcyc.write(test + "," + names[names_idx] + "," + percentages[names_idx] + "," + str(max(total_cycles)) + "\n")
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
                elif f"l2p{l2pcount}-0" in line:
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

                    core_count += 1

            sum_hits = sum(l1ihits) + sum(l1dhits)
            sum_miss = sum(l1imiss) + sum(l1dmiss)
            l1hr = sum_hits / (sum_hits + sum_miss) if sum_hits + sum_miss != 0 else 0

            sum_phits = sum(l2phits)
            sum_pmiss = sum(l2pmiss)
            sum_shits = sum(l2shits)
            sum_smiss = sum(l2smiss)
            l2phr = sum_phits / (sum_phits + sum_pmiss) if sum_phits + sum_pmiss != 0 else 0
            l2shr = sum_shits / (sum_shits + sum_smiss) if sum_shits + sum_smiss != 0 else 0

            sum_3hits = sum(l3hits)
            sum_3miss = sum(l3miss)
            l3hr = sum_3hits / (sum_3hits + sum_3miss) if sum_3hits + sum_3miss != 0 else 0

            amat = l1hr * l1lat + (1 - l1hr) * (
                        l1lat + l2phr * l2plat + (1 - l2phr) * (
                            l2plat + l2shr * l2slat + (1 - l2shr) * (
                                l2slat + l3hr * l3lat + (1 - l3hr) * (
                                    l3lat + memlat))))

            famat.write(test + "," + names[names_idx] + "," + str(amat) + "," + str(
                max(cyc_counts) if len(cyc_counts) > 0 else 0) + "\n")

        except FileNotFoundError:
            print(f"FAILED to parse {test} (zsim.out doesn't exist)")

        print(f"Parsed {test}\n")
        names_idx += 1

    fcyc.close()
    famat.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("node_name", help="Name of the node to process")
    args = parser.parse_args()
    main(args.node_name)
