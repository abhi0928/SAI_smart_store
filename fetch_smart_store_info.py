# from sshtunnel import SSHTunnelForwarder
import pymysql
import json



# server = SSHTunnelForwarder(
#     'XXX.XXX.XXX.XXX',
#     ssh_username='root',
#     ssh_password='my_server_password',
#     remote_bind_address=('127.0.0.1', 3306)
# )
# server.start()

class SAISmartStoreDB:

    def __init__(self, store_name : str, config_file : str) -> None:
        self.store_name = store_name
        try:
            self.config = json.load(open(config_file, 'r'))
        except Exception as e:
            print(str(e))
        self.conn = self.connect_db()

    def connect_db(self):
        cnx = pymysql.connect(
            host = self.config['dbhost'],
            user = self.config['user'],
            port = self.config['port'],
            password = self.config['password'],
            database = self.config['database']
        )
        print("successfully connect with DB")
        return cnx
    
    def fetch_item_info(self, aisle_name : str, block_name : str):
        block = 'block' + block_name[0]
        section = 'section' + block_name
        item = 'item' + block_name

        cursor = self.conn.cursor()
        query = f"""SELECT i.price, i.name as price FROM stores s JOIN aisles a ON s.id = a.store_id JOIN blocks b ON a.id = b.aisle_id
        JOIN sections sc ON b.id = sc.block_id
        JOIN items i ON sc.id = i.section_id
        WHERE i.name = '{item}'
        AND sc.name = '{section}'
        AND b.name = '{block}'
        AND a.name = '{aisle_name}'
        AND s.name = '{self.store_name}';
        """

        cursor.execute(query)

        out = cursor.fetchall()

        item_price = out[0][0]
        item_name = out[0][1]
        return f"Price : {item_price}\nName : {item_name}"


if __name__ == "__main__":


    # this is a demo run, how you use this class to fetch item info
    sai_ss = SAISmartStoreDB(store_name = 'store1', config_file = 'config.json')
    print(sai_ss.fetch_item_info(aisle_name = 'aisle_128', block_name = 'A3'))