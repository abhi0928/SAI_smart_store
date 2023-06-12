import pymysql
import os
import ast
import yaml


class CustomerInfoDB(object):

    def __init__(self, db_name : str = None, sql_config : str = None):
        self.db = db_name
        assert self.config = yaml.safe_load(open(sql_config, 'r')), "Unable to fetch sql_config info"
        self.conn = self.connect_db()
        


    def connect_db(self):
        """make a connection with sql
        """
        cred = self.config['sql_cred']
        cnx = pymysql.connect(
            host = cred['host'],
            user = cred['user'],
            password = cred['password'],
        )
        
        return cnx

    def create_db(self, db_name : str, check : bool = False):
        """create a new database in sql
        Args :
            db_name (str) : name of the database
        """
        cursor = self.conn.cursor()

        cursor.execute(f"CREATE DATABASE {db_name};")

        if check:
            cursor.execute("SHOW DATABASES;")\
            for db in cursor:
                print(db)

    def build_arch_in_db(self):
        cursor = self.conn.cursor()

        # create customer info table
        cursor.execute("""CREATE TABLE CustInfo (
                                    uid INT IDENTITY,    # primary key, foreign key 
                                    name VARCHAR(15) NOT NULL, 
                                    address VARCHAR(50) NOT NULL
                                    );""")

        # create customer store activity info table
        cursor.execute("""CREATE TABLE CustStoreAct (
                                    uid INT IDENTITY,
                                    date_of_activity DATETIME,
                                    entrance_time DATETIME,
                                    exit_time DATETIME
                                    );""")

        
        
