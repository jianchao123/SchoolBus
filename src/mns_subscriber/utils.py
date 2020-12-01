import json
import logging
import requests


def get_logger(log_path):
    handler = logging.FileHandler(log_path)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def gcj_02_to_gorde_gpd(longitude, latitude):
    s = longitude + "," + latitude
    url = "https://restapi.amap.com/v3/assistant/coordinate/convert?" \
          "key=5c96c771bb5621b2bc0f80130e56b083&locations={}" \
          "&coordsys=gps".format(s)
    res = requests.get(url)
    d = json.loads(res.content.decode("utf-8"))
    if "locations" not in d:
        return 0, 0
    arr = d['locations'].split(",")
    return arr[0], arr[1]
