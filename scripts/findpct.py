import math
import csv

def find_closest_legal_powers(size):
    results = []
    specific_percentages = set(range(10, 101, 10)).union(set(range(25, 101, 25)))

    for i in range(0, 101):
        shared_cache_bytes = int(size * i / 100)
        private_cache_bytes = int((size - shared_cache_bytes) / 4)
        shared_set_number = shared_cache_bytes / 64 / 8
        private_set_number = private_cache_bytes / 64 / 8
        shared_log = math.log(shared_set_number, 2) if shared_set_number > 0 else 0
        private_log = math.log(private_set_number, 2) if private_set_number >0 else 0
        shared_closeness = abs(shared_log - round(shared_log))
        private_closeness = abs(private_log - round(private_log))
        rmsd = math.sqrt(shared_closeness**2 + private_closeness**2)

        legal_shared_cache_sets = int(2 ** round(shared_log)) * 64 * 8
        legal_private_cache_sets = int(2 ** round(private_log)) * 64 * 8

        actual_shared_percentage = (legal_shared_cache_sets / (legal_shared_cache_sets+legal_private_cache_sets*4)) * 100
        actual_private_percentage = 100 - actual_shared_percentage

        results.append((i, rmsd, shared_set_number, private_set_number,
                        legal_shared_cache_sets, legal_private_cache_sets,
                        actual_shared_percentage, actual_private_percentage,
                        legal_shared_cache_sets // (64 * 8), legal_private_cache_sets // (64 * 8)))

    # Sorting results by Shared Percentage (ascending)
    results.sort(key=lambda x: x[0])

    # Write results to a CSV file
    with open('cache_configurations.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Shared Percentage', 'RMSD', 'Actual Shared Sets', 'Actual Private Sets',
                         'Legal Shared Cache Size (Bytes)', 'Legal Private Cache Size (Bytes)',
                         'Actual Shared Percentage', 'Actual Private Percentage',
                         'Legal Shared Cache Sets', 'Legal Private Cache Sets'])

        for result in results:
            writer.writerow(result)

def main():
    find_closest_legal_powers(1024 * 1024)

if __name__ == "__main__":
    main()
