"""
    The configurations class is a singleton for retrieving and setting all configuration values.
"""
import configparser
import logging
import os

from os import path


class Configurations(object):
    """
    STATIC CLASS ATTRIBUTES
    """
    DEFAULT_CONFIG      = os.path.expanduser('~') + "/.wf2m/config.properties"

    """
    OBJECT ATTRIBUTES
    """
    __instance = None
    __config_parser = None

    """
        static class constructor for singleton
    """

    def __new__(cls, *args, **kwargs):
        if Configurations.__instance is None:
            Configurations.__instance = object.__new__(cls)
        return Configurations.__instance

    """
        constructor for singleton

        :param    config_file: the location of the properties file, relative to runtime execution path
        :type     config_file: str
    """
    def __init__(self, config_file=None):
        # read config for led strips
        self.__config_parser = configparser.ConfigParser()

        # check if custom configuration file defined
        if config_file is None:
            config_file = type(self).DEFAULT_CONFIG

        # check if config file exists
        if not(path.exists(config_file)):
            logging.error("Configuration file does not exist: %s", config_file)
            raise FileNotFoundError("Config file does not exist " + config_file)

        logging.info("Loading configuration from file: %s", config_file)
        self.__config_parser.read(config_file)


    ########################################
    #      GETTER/SETTER Methods           #
    ########################################

    #
    #    service provider configuration
    #
    def getIPInfoKey(self):
        return self.getConfigProperty('Forecast-IPInfoData', 'APIKey')

    def getOWMKey(self):
        return self.getConfigProperty('Forecast-OWMData', 'APIKey')

    #
    #    location information
    #
    def getCityID(self):
        cid = self.getConfigProperty('Forecast-ApplicationData', 'CityID')
        if cid is not None:
            cid = int(cid)
        return cid

    def getCityName(self):
        return self.getConfigProperty('Forecast-ApplicationData', 'CityName')

    def getCityCountry(self):
        return self.getConfigProperty('Forecast-ApplicationData', 'Country')

    def getLongitude(self):
        lon = self.getConfigProperty('Forecast-ApplicationData', 'Longitude')
        if lon is not None:
            lon = float(lon)
        return lon

    def getLatitude(self):
        lat = self.getConfigProperty('Forecast-ApplicationData', 'Latitude')
        if lat is not None:
            lat = float(lat)
        return lat

    #
    #    MQTT information
    #
    def getMQTTIP(self):
        return self.getConfigProperty('MQTT-ServerData', 'IPAddress')

    def getMQTTPort(self):
        return self.getConfigProperty('MQTT-ServerData', 'Port')

    def getMQTTUser(self):
        return self.getConfigProperty('MQTT-ServerData', 'Username')

    def getMQTTPwd(self):
        return self.getConfigProperty('MQTT-ServerData', 'Password')

    ########################################
    #         UTILITY Methods              #
    ########################################

    """
        returns a property from specified config file (dynamic values)
        shall be only used in exceptional cases - use dedicated getter/setter classes instead

        :param    section: section in config file
        :type     section: str
        :param    attribute: required attribute
        :type     attribute: str
        :returns: property value
    """

    def getConfigProperty(self, section, attribute):
        try:
            ret = self.__config_parser.get(section, attribute)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return None
        return ret

    def hasSection(self, section):
        return self.__config_parser.has_section(section)