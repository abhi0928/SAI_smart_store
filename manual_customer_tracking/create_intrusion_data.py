from get_ts_file import merge_ts_files
import os
import pickle
from time import sleep

files_count = 0
while True:
    print("fetching...")
    if not os.path.exists('intrusion_timestamp.pickle'):
        sleep(5)
        continue

    f = pickle.load(open('intrusion_timestamp.pickle', "rb"))
    if not f:
        sleep(5)
        continue
    total_files = len(f)
    if total_files == files_count + 1:
        start, end, counter = f[files_count]
        merge_ts_files(start, end, counter)

        files_count += 1

    sleep(2)