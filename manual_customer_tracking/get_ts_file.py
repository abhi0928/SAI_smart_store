import os
import glob
import subprocess
from datetime import datetime, timedelta
import time
import re

date = datetime.now().date().strftime("%Y-%m-%d")
# date= "2023-07-05"

stream_base_path_global = "E:\\Sai_Group\\ScreenSelectionTheft_keyboard\\Videos\\{}\\store_id_no\\".format(date)
saving_base_path_global = "E:\\Sai_Group\\ScreenSelectionTheft_keyboard\\Videos\\save_{}\\store_id_no\\".format(date)


def convert_ts_to_mp4(infile):
	outfile = infile.replace(".ts", ".mp4")
	cmd = f'ffmpeg -i "{infile}" -c:v libx264 -c:a copy -b 150k -preset ultrafast "{outfile}"' #cmd = f'ffmpeg -i "{infile}" -acodec copy -vcodec copy "{outfile}"'
	os.system(cmd); os.remove(infile)
	return outfile

def get_latest_file(counter_no):
    stream_base_path = stream_base_path_global.replace("store_id_no", str(counter_no))
    l = glob.glob(stream_base_path + "*.ts")
    l1 = [int(re.findall('\d+',i.rsplit('\\', 1)[-1])[0]) for i in l]
    latest_file=max(l1)
    return latest_file
    

def merge_ts_files(start, end, counter_no):
    print("merging files...")
    stream_base_path = stream_base_path_global.replace("store_id_no", str(counter_no))
    saving_base_path = saving_base_path_global.replace("store_id_no", str(counter_no))
    if not os.path.exists(saving_base_path):
        os.makedirs(saving_base_path)
    ts_files = list(range(start, end+1, 1))
    
    file_name_saved_with = saving_base_path + str(datetime.now()).replace(":", "_").replace(" ", "_").replace("-", "_").replace(".", "_")+"_"+str(counter_no)+".ts"
    with open("input.txt", "w") as f:
        for line in ts_files:
            f.write(f"file '{stream_base_path}stream{str(line)}.ts'"+"\n")
            #f.write(f"file 'stream{str(line)}.ts'"+"\n")
    merge_cmd = f'ffmpeg -f concat -safe 0 -i input.txt -c copy {file_name_saved_with}'
    #merge_cmd = f'ffmpeg -i concat:"{all_files_for_mp4[0]}"^|"{all_files_for_mp4[1]}"^|"{all_files_for_mp4[2]}"^|"{all_files_for_mp4[3]}"^|"{all_files_for_mp4[4]}"^|"{all_files_for_mp4[5]}"^|"{all_files_for_mp4[6]}"^|"{all_files_for_mp4[7]}"^|"{all_files_for_mp4[8]}"^|"{all_files_for_mp4[9]}" -vcodec copy -acodec copy -f vob "{infile}"'
    os.system(merge_cmd)
    convert_ts_to_mp4(infile = file_name_saved_with)
    print(file_name_saved_with)
    


# if __name__ == "__main__":
#     get_latest_file(counter_no=116)
#     merge_ts_files(start=911, end=920, counter_no=116)
    