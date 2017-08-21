import json
import sys
import time
import logging
import logging.config
import rasp_data
from raspberry import MyPi


def launch_logger():
    with open('logging.json', 'r') as f:
        config = json.load(f)
    logging.config.dictConfig(config)


def init():
    launch_logger()
    logger = logging.getLogger("api_beez")
    logger.debug("Raspberry Pi initialization")
    return MyPi()


def main():
    raspy = init()
    waiting_seconds = 60
    while True:
        to_send = raspy.sensor_datas()
        saved = rasp_data.save_datas(to_send)
        #sended = rasp_data.send_datas(saved)
        time.sleep( waiting_seconds )
    # return 0

if __name__ == '__main__':
    logger = logging.getLogger("api_beez")
    try:
        main()
    except( KeyboardInterrupt, SystemExit ):
        MyPi.cleanup()
        sys.exit()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        logger.error( f'Unexpected error: {sys.exc_info()[0]}')
        raise
