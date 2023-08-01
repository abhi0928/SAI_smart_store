from typing import List
import os
import argparse
from transactions import get_transaction_id, update_transaction_validation_status
from subprocess import Popen


def smart_store_monitor(store_name : str, aisles : List, streams : List = None, 
                        regions_file : str = 'archway_aisle_map.pkl', rtsp : bool = False):
    tran_id = get_transaction_id()
    print("transaction id : ", tran_id)
    command = []

    if not rtsp:
        if len(aisles) != len(streams):
            return "aisles and streams length must be same"
    
        for aisle, stream in zip(aisles, streams):
        
            command.append(f"python monitor_cust.py --store {store_name} --aisle {aisle} --stream '{stream}' --tranid {tran_id}")

    else:
        for aisle in aisles:
            command.append(f"python monitor_cust.py --store {store_name} --aisle {aisle} --tranid {tran_id} --rtsp {rtsp}")
    
    command.insert(0, "python test_checkout.py")

    procs = [ Popen(i, shell = True) for i in command ]
    for p in procs:
        p.wait()
    update_transaction_validation_status(tran_id = tran_id)



if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description = "SAI smart store project demo")

    # parser.add_argument("-sn", "--store", required = True, help = 'name of the store')
    # parser.add_argument("-a", "--aisle", required = True, help = 'aisle which needs to monitor')
    # parser.add_argument("-r", "--regions", default = 'archway_aisle_map.pkl', help = 'pickle file contain regions')
    # parser.add_argument("-s", "--stream", default = None, help = 'path of stream')
    # parser.add_argument("-rt", "--rtsp", help = "url of rtsp stream")

    # args = vars(parser.parse_args())

    smart_store_monitor(store_name = 'store1', aisles = [126, 120, 128], rtsp = True)

