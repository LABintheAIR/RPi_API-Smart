import json
import logging
import time
import math
import RPi.GPIO as GPIO

import Adafruit_DHT
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from w1thermsensor import W1ThermSensor
from hx711 import HX711


logger = logging.getLogger("api_beez")
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 0))

class MyPi(object):
    # 'magic method' propre à toutes les classes (ca commence et finit par '__').
    # En l'occurence init prend des parametres et permet de les relier à l'instance via self
    def __init__(self):
        self.config = json.load(open("config_settings.json", "r"))
        self.sensors = self.sensor_matches(self.config['raspberry']['sensors'])

    # Décorateur qui permet de faire des méthodes classe et non d'instance
    @classmethod
    def sensor_matches(cls, sensor_config):
        matches = {
                "DS18B20": { "mesure": "temperature", "class": DS18B20Sensor },
                "DHT22": { "mesure": "humidite", "class": DHT22Sensor },
                "HX711": { "mesure": "poids", "class": HX711Sensor },
                "SEN0159" : { "mesure" : "CO2", "class" : SEN0159Sensor }
        }

        sensors = {}
        for sensor in sensor_config:
            match = matches[sensor["model"]]
            if sensors.get( match['mesure'] ) == None:
                sensors[ match['mesure'] ] = []

            sensors[ match['mesure'] ].append(match['class']( **sensor["params"] ) )

        # La ligne en dessous permet de faire la meme chose que la boucle au dessus: -> List Comprehension
        # sensors = [matches[sensor] for sensor in sensor_config]
        return sensors

    def get_sensors(self):
        return self.sensors

    def sensor_datas(self):
        datas = {}
        for mesure, sensors in self.sensors.items():
            datas[ mesure ] = {}
            for sensor in sensors:
                datas[mesure][sensor.name] =sensor.get_data()

        return datas
        #return [{sensor.name: sensor.get_data()} for sensor in self.sensors]

    # Permet de "nettoyer" les GPIOs utilisés. Doit être appelée avant la fermeture du programme
    @staticmethod
    def cleanup():
        GPIO.cleanup()


class Sensor(object):
    def __init__(self, name, *args, **kwargs):
        self.name = name

    def get_data(self):
        pass


class TempSensor(Sensor):
    def __init__(self, name, *args, **kwargs):
        logger.debug(f'Temp Sensor "{name}" just initialized')
        # print(f"Temp Sensor {model} just initialized")
        super().__init__(name, *args, **kwargs)

    def get_data(self):
        return 0


class DS18B20Sensor(Sensor):
    def __init__(self, name, serial, *args, **kwargs):
        logger.debug(f'DS18B20 Sensor "{name}" ({serial}) just initialized')
        self.sensor = W1ThermSensor( W1ThermSensor.THERM_SENSOR_DS18B20, serial )
        super().__init__(name, *args, **kwargs)

    def get_data(self):
        return self.sensor.get_temperature()


class DHT22Sensor(Sensor):
    def __init__(self, name, gpio, *args, **kwargs):
        logger.debug(f'DHT22 Sensor "{name}" just initialized')
        self.dht = Adafruit_DHT.DHT22
        self.gpio = gpio
        super().__init__(name, *args, **kwargs)

    def get_data(self):
        return Adafruit_DHT.read(self.dht, self.gpio)[0]

class HX711Sensor(Sensor):
    def __init__(self, name, gpio_clk, gpio_dat, scale_value, offset_value, *args, **kwargs):
        logger.debug(f'HX711 Sensor "{name}" just initialized')
        self.hx = HX711( gpio_dat, gpio_clk, 128 )
        self.hx.set_scale(scale_value)
        self.hx.set_offset(offset_value)
        super().__init__(name, *args, **kwargs)

    def get_data(self):
        return self.hx.get_units( 10 )


class SEN0159Sensor(Sensor):
    def __init__(self, name, channel, *args, **kwargs):
        logger.debug(f'SEN0159 Sensor "{name}" just initialized')
        self.channel = channel
        super().__init__(name, *args, **kwargs)

    def get_data(self):
        v = mcp.read_adc( self.channel )
        if v == 0:
            return 0
        v = v * 5 / 1024
        v /= 8.5
        v = -42.857 * math.log10( v ) + 436.429
        return math.ceil( v )
