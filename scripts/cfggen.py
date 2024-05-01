#!/usr/bin/python3
import argparse
import csv
import sys
def get_cache_sizes(csv_file, shared_percentage):
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if float(row['Shared Percentage']) == shared_percentage:
                return int(row['Legal Shared Cache Size (Bytes)']), int(row['Legal Private Cache Size (Bytes)'])

def generate_zsim_config(shared_percentage, process_file, num_cores, num_clusters, output_file):
    """
    Generate a zSim configuration file based on the specified shared L2 cache percentage, number of cores,
    number of clusters, and save it to the specified output file.

    Args:
        shared_percentage (int): Percentage of L2 cache that is shared.
        process_file (str): Path to the CSV file containing the processes with their masks.
        num_cores (int): Total number of cores.
        num_clusters (int): Total number of clusters.
        output_file (str): Path to the output file where the configuration will be saved.
    """
    if num_cores % num_clusters != 0:
        raise ValueError("Number of cores must be evenly divisible by the number of clusters.")
    if shared_percentage >100 or shared_percentage<0:
        raise ValueError("Shared percentage must be between 0 and 100")

    cores_per_cluster = num_cores // num_clusters
    total_l2_per_cluster = 1024 * 1024  # 1 MiB

    shared_cache_size, private_cache_size = get_cache_sizes('/users/ngaertne/CNC/scripts/cache_configurations.csv', shared_percentage)

    print(f"Opening CSV file at: {process_file}")  # Debug: show file path
    try:
        with open(process_file, 'r') as f:
            csv_reader = csv.DictReader(f)
            processes = []
            for row in csv_reader:
                try:
                    processes.append((row['process'], row['mask']))
                except KeyError as e:
                    print(f"KeyError: {e} in row: {row}")  # Show which key is missing
                    sys.exit(1)  # Exit on error for now
    except FileNotFoundError:
        print(f"File not found: {process_file}")
        sys.exit(1)

    cores_config, caches_config, process_config = "", "", ""
    for cluster_id in range(num_clusters):
        core_ids = [cluster_id * cores_per_cluster + i for i in range(cores_per_cluster)]
        cores_config += "\n".join(f"""
        c{core_id} = {{
            type = "OOO";
            dcache = "l1d{core_id}";
            icache = "l1i{core_id}";
            cores = 1;
        }};""" for core_id in core_ids)
        if(shared_percentage >0 and shared_percentage < 100):
            caches_config += "\n".join(f"""
            l1d{core_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 8;
                }};
                caches = 1;
                latency = 4;
                size = 32768;  // 32 KiB
            }};
            l1i{core_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 4;
                }};
                caches = 1;
                latency = 3;
                size = 32768;  // 32 KiB
            }};
            l2p{core_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 8;
                }};
                caches = 1;
                latency = 7;
                children = "l1i{core_id}|l1d{core_id}";
                size = {private_cache_size};
            }};""" for core_id in core_ids)

            caches_config += f"""
            l2sc{cluster_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 8;
                }};
                caches = 1;
                latency = 0;
                children = "{'|'.join([f'l2p{cid}' for cid in core_ids])}";
                size = {shared_cache_size};
            }};"""

            l3_children = '|'.join([f'l2sc{i}' for i in range(num_clusters)])
            l3_cache_config = f"""
            l3 = {{
            array = {{
                hash = "H3";
                type = "Z";
                ways = 4;
                candidates = 52;
            }};
            banks = 6;
            caches = 1;
            latency = 27;
            children = "{l3_children}";
            size = 12582912;  // 12 MiB
            }};"""
        elif (shared_percentage==100):
            caches_config += "\n".join(f"""
            l1d{core_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 8;
                }};
                caches = 1;
                latency = 4;
                size = 32768;  // 32 KiB
            }};
            l1i{core_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 4;
                }};
                caches = 1;
                latency = 3;
                size = 32768;  // 32 KiB
            }};
            """ for core_id in core_ids)
            caches_config += f"""
            l2c{cluster_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 8;
                }};
                caches = 1;
                latency = 0;
                children = "{'|'.join([f'l1i{cid}' for cid in core_ids] + [f'l1d{cid}' for cid in core_ids])}";
                size = {shared_cache_size};
            }};"""
            l3_children = '|'.join([f'l2c{i}' for i in range(num_clusters)])
            l3_cache_config = f"""
            l3 = {{
            array = {{
                hash = "H3";
                type = "Z";
                ways = 4;
                candidates = 52;
            }};
            banks = 6;
            caches = 1;
            latency = 27;
            children = "{l3_children}";
            size = 12582912;  // 12 MiB
            }};"""
        else:
            caches_config += "\n".join(f"""
            l1d{core_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 8;
                }};
                caches = 1;
                latency = 4;
                size = 32768;  // 32 KiB
            }};
            l1i{core_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 4;
                }};
                caches = 1;
                latency = 3;
                size = 32768;  // 32 KiB
            }};
            l2c{core_id} = {{
                array = {{
                    type = "SetAssoc";
                    ways = 8;
                }};
                caches = 1;
                latency = 7;
                children = "l1i{core_id}|l1d{core_id}";
                size = {private_cache_size};
            }};""" for core_id in core_ids)
            l3_children = '|'.join([f'l2c{i}' for i in range(num_cores)])
            l3_cache_config = f"""
            l3 = {{
            array = {{
                hash = "H3";
                type = "Z";
                ways = 4;
                candidates = 52;
            }};
            banks = 6;
            caches = 1;
            latency = 27;
            children = "{l3_children}";
            size = 12582912;  // 12 MiB
            }};"""

    frequency_config = "frequency = 2400;  // in MHz"
    mem_config = """
    mem = {
      controllers = 12;
      type = "DDR";
      controllerLatency = 40;  // in cycles
    };"""

    sim_config = """
    sim = {
      maxTotalInstrs= 100000000000L;
      phaseLength = 10000;  // in cycles
      schedQuantum = 50;  // switch threads frequently
    };"""

    process_config = "\n".join(f'process{index} = {{\n    command = "{cmd.strip()}";\n    mask="{mask}";\n}};' for index, (cmd, mask) in enumerate(processes))

    config = f"""
sys = {{
    cores = {{{cores_config}
    }};

    caches = {{{caches_config}
    {l3_cache_config}
    }};
    {frequency_config}
    {mem_config}
}}

{sim_config}

{process_config}
"""
    # Save the configuration to a file
    with open(output_file, 'w') as file:
        file.write(config)
    print(f"Configuration saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate a zSim configuration file.")
    parser.add_argument("shared_percentage", type=int, help="Percentage of L2 cache that is shared")
    parser.add_argument("process_file", type=str, help="Path to the CSV file containing the processes and their masks")
    parser.add_argument("num_cores", type=int, help="Total number of cores")
    parser.add_argument("num_clusters", type=int, help="Total number of clusters")
    parser.add_argument("output_file", type=str, help="Path to the output file to save the configuration")
    
    args = parser.parse_args()

    try:
        generate_zsim_config(args.shared_percentage, args.process_file, args.num_cores, args.num_clusters, args.output_file)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
