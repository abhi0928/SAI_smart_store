import pickle
from typing import List
from subprocess import Popen
from argparse import ArgumentParser


def manual_cust_tracker(streams : List = None):
    command = []

    for stream in streams:
        command.append(f"python track_entrance_exit.py --cam {stream}")
    
    command.insert(0, "python create_intrusion_data.py")

    procs = [ Popen(i, shell = True) for i in command ]
    for p in procs:
        p.wait()

if __name__ == "__main__":
    with open("intrusion_timestamp.pickle", "wb") as intTS:
        pickle.dump({}, intTS)
    parser = ArgumentParser(description = "SAI manual customer tracker")

    parser.add_argument("-s", "--streams", required = True, nargs = '+', help = 'camera number for each rtsp stream')

    args = vars(parser.parse_args())

    all_streams = args["streams"]
    manual_cust_tracker(all_streams)