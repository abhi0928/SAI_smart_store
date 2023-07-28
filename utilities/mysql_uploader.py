#SQL
import os
import datetime

import mysql.connector
from dotenv import load_dotenv
load_dotenv()


config = {
    'host': os.getenv('SQL_HOST'),
    'user': os.getenv('SQL_USER'),
    'pass': os.getenv('SQL_PASS'),
    'db_name': os.getenv('SQL_DB')
}
class MySQLUploader:
    def __init__(self):
        self.cnx = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['pass'],
            database=config['db_name'])


    def upload_video_name(self, store_id, cam_id, vid_date, vid_time):
        cursor = self.cnx.cursor()
        todays_date = datetime.datetime.now().date().strftime("%Y_%m_%d")
        vid_name = f"{store_id}_{cam_id}_{todays_date}_{vid_time.replace(':','_')}.mp4"
        insert_query = f"INSERT INTO wiwo_interaction_videos_meta (store_id, cam_id, vid_date, vid_time, vid_name) VALUES ({store_id}, {cam_id}, '{vid_date}', '{vid_time}', '{vid_name}') "
        cursor.execute(insert_query)
        self.cnx.commit()
        cursor.close()

    def __del__(self):
        self.cnx.close()
