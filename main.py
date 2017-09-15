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


def collect_data():
    raspy = init()
    to_send = raspy.sensor_datas()
    saved = rasp_data.save_datas(to_send)
    sended = rasp_data.send_to_somei(to_send)


def main(argv):
    if '--noloop' in argv:
        collect_data()
    else:
        while True:
            collect_data()
            time.sleep( 60 )

if __name__ == '__main__':
    logger = logging.getLogger("api_beez")
    try:
        main(sys.argv[1:])
    except( KeyboardInterrupt, SystemExit ):
        MyPi.cleanup()
        sys.exit()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        logger.error( f'Unexpected error: {sys.exc_info()[0]}')
        raise
