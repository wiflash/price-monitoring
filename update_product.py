import requests, time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


while True:
    s = requests.Session()
    retries = Retry(total=float("inf"), backoff_factor=1)
    s.mount("http://", HTTPAdapter(max_retries=retries))
    response = s.put("http://0.0.0.0:5000/update_price")
    print(response.json())
    time.sleep(1)
