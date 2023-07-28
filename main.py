import os
import yaml
import logging
from logging.handlers import TimedRotatingFileHandler
from WIWO import WIWO
from utilities.proxy_setting import set_proxies


def setup_logging(log_path, log_level):
    log_filename = os.path.join(log_path,"logs.log")
    rotating_handler = TimedRotatingFileHandler(log_filename, when='d', interval=1, backupCount=3)
    logging.basicConfig(
            format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s' ,
            level=log_level,
            handlers=[rotating_handler])

if __name__ == '__main__':

    # set_proxies()
    with open("config.yml") as f:
        config = yaml.safe_load(f)
    
    
    log_path = os.path.join(config['log_path'])
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    setup_logging(log_path, config['log_level'])


    wiwo_service = WIWO(config)

    wiwo_service.start()
    
    logging.info("Exiting...")