from datetime import datetime, timedelta
import re
import sys
import matplotlib.pyplot as plt
import numpy as np

# grep "Stream time" logs.log | head -100000 | sed -e 's/\ \-.*took /|/g' | sed -e 's/ms//g' > fps_trimed.log

log_file_path = sys.argv[1]

aggregate_on = "1s"    # single digit seconds or minutes
aggregate_fn = "count" # not being used... TODO

aggregate_on = re.search("^([1-9])(m|s)$", aggregate_on)
if aggregate_on is None:
    print("aggregate_on is invalid.")
    exit(1)
aggregate_on = {'value': int(aggregate_on.group(1)), 'unit': aggregate_on.group(2)}
if aggregate_fn not in ['count']:
    print("aggregate_fn is invalid.")
    exit(1)

with open(log_file_path) as log_file:
    group_by_count_dict = {}
    group_by_sum_dict = {}
    prev_datetime = None
    for line in log_file.readlines():
        log_line = line.split('|')
        logs_datetime = datetime.strptime(log_line[0], "%Y-%m-%d %H:%M:%S,%f")
        log_msg = int(log_line[1].strip())

        logs_datetime += timedelta(microseconds=-logs_datetime.microsecond)
        if aggregate_on['unit'] == 'm':
            logs_datetime += timedelta(seconds=-logs_datetime.second) 

        if prev_datetime is None or (
                aggregate_on["unit"] == 's' and 
                (logs_datetime - prev_datetime).total_seconds() >= aggregate_on["value"]) or (
                    aggregate_on["unit"] == 'm' and 
                    (logs_datetime - prev_datetime).total_seconds()/60 >= aggregate_on["value"]
                ):
            prev_datetime = logs_datetime
            group_by_count_dict[prev_datetime] = 0
            group_by_sum_dict[prev_datetime] = 0
            
        
        group_by_count_dict[prev_datetime] += 1
        group_by_sum_dict[prev_datetime] += log_msg
        
    #print(group_by_dict.items())
    x, y = group_by_sum_dict.keys(), np.array(list(group_by_count_dict.values()))
    print(len(y),y)
    N = 120
    y = np.convolve(np.pad(y,((int(N/2),int(N/2)-1)),'edge'), np.ones(N)/N, mode='valid')
    print(len(y),y)
    plt.figure("FPS")
    plt.plot(x,y)
    plt.xlabel("Date and Time")
    plt.ylabel("FPS")
    # plt.gcf().autofmt_xdate()
    plt.show()
