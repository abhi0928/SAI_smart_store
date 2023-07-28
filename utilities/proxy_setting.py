import os
from dotenv import load_dotenv
load_dotenv()

def set_proxies():
    proxy = os.getenv('PROXY')
    os.environ['http_proxy'] = proxy
    os.environ['HTTP_PROXY'] = proxy
    os.environ['https_proxy'] = proxy
    os.environ['HTTPS_PROXY'] = proxy