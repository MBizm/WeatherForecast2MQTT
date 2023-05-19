"""
    Main class that will start weather forecast loading OWM and map weather conditions on a daily basis.
    Weather forecast information will be sent to defined MQTT instance.
"""
import datetime
import logging
import os
import ipinfo

import paho.mqtt.client as paho

from pyowm import OWM
from threading import Timer
from ipinfo.exceptions import RequestQuotaExceededError

from src.core.util.Configurations import Configurations
from src.core.util.utility import getExternalIPAddress, dayinfuture


class WF2M:
    """
    Main class
    """

    """
    STATIC CLASS ATTRIBUTES
    """
    LOG_PATH      = os.path.expanduser('~') + "/.wf2m/wf2m.log"

    # WEATHER CONDITION CODE
    # each weather condition based on rain, cloud coverage and temperature is mapped into discrete number of condition states
    #  that are indicated by different colors on the LED strip
    # storm: digit 6, big endian
    CONDITION_STORM = 0x40
    # snow: digit 5, big endian
    CONDITION_SNOW = 0x20
    # temperature: digit 4-3, big endian
    CONDITION_LTMP = 0x08
    CONDITION_MTMP = 0x10
    CONDITION_HTMP = 0x18
    # rain/cloud: digit 2-0, big endian
    CONDITION_CLEAR = 0x01
    CONDITION_SLCLO = 0x02
    CONDITION_CLO   = 0x03
    CONDITION_SLRAI = 0x04
    CONDITION_RAI   = 0x05

    """
    Constructor
    Will load OWM instance to start weather forecast.
    """
    def __init__(self):
        super()

        # setup logging
        logging.basicConfig(filename=type(self).LOG_PATH, filemode='w', level=logging.ERROR)

        # load configuration with OWM and MQTT config
        self.config = Configurations()

        # initialize OWM
        self.__init_OWM(self.config)

    ########################################
    #            UTILITY METHODS           #
    ########################################

    """
        reads forecast config values from the defined property file
        this will instantiate the OpenWeatherMap instance and read country, city, ... data

        property file consists of two sections:
            - [OWMData]:APIKeyDomain, APIKeyName(optional), APIKey
            - [ApplicationData]:CityID, CityName, Country
    """

    def __init_OWM(self, config):
        # get your personal key
        apiKey = config.getOWMKey();
        if apiKey is None:
            raise RuntimeError('You need to define an Open Weather Map API key to run the forecast module!')

        # initiate OpenWeatherMap object
        self.owm = OWM(apiKey);
        reg = self.owm.city_id_registry()

        # get current location
        ipInfoKey = config.getIPInfoKey()
        if ipInfoKey is not None:
            try:
                # determine location by external IP
                ipInfo = ipinfo.getHandler(ipInfoKey)
                ipDetails = ipInfo.getDetails(getExternalIPAddress())

                self.localCity = ipDetails.city
                self.localCountry = ipDetails.country
                self.localLat = float(ipDetails.latitude)
                self.localLon = float(ipDetails.longitude)
                self.localTimeZone = ipDetails.timezone
            except (RequestQuotaExceededError, AttributeError) as e:
                logging.error("Error defining location automatically: " + e)

        # bind location to OWM
        try:
            locs = reg.locations_for(self.localCity, self.localCountry, matching='exact')
            #always select first from list
            loc = locs.pop(0)
            self.cityID = loc.id
            logging.info("OWM location defined %s", loc.name)
        except (ValueError, IndexError) as e:
            logging.error("Error defining location in OWM: " + e)
            raise RuntimeError("Error in setting up OWM instance.")

    def update_forecast(self):
        # request forecast
        forecast = self.owm.weather_manager().forecast_at_id(self.cityID, '3h')

        # set up MQTT client
        client = paho.Client("Weather Forecaster")
        # TODO config values
        client.username_pw_set(self.config.getMQTTUser(), self.config.getMQTTPwd())
        if self.config.getMQTTPort() is None:
            client.connect(self.config.getMQTTIP())
        else:
            client.connect(self.config.getMQTTIP(), self.config.getMQTTPort())

        # iterate set of forecast days
        for days in range(1, 5):
            rain = 0
            tmp_min = 1000
            tmp_max = -1000
            storm = -1000
            snow = False

            # iterate intra-day forecasts, OWM will provide forecasts in 3h segments
            for w in forecast.forecast.weathers:
                if datetime.datetime.fromtimestamp(w.reference_time()).day == dayinfuture(days).day:
                    # rain
                    if len(w.rain) > 0:
                        rain = w.rain.get('3h') + rain
                    # tmp min
                    if w.temperature('celsius').get('temp_min') < tmp_min:
                        tmp_min = w.temperature('celsius').get('temp_min')
                    # tmp max
                    if w.temperature('celsius').get('temp_max') > tmp_max:
                        tmp_max = w.temperature('celsius').get('temp_max')
                    # storm
                    if w.wind('meters_sec').get('speed') > storm:
                        storm = w.wind('meters_sec').get('speed')
                    # snow
                    if len(w.snow) > 0:
                        snow = True

            # publish values
            logging.info("Day {0}: Rain - {1}, tmp_min - {2}, tmp_max - {3}, storm - {4}. snow - {5}".format(
                            days, rain, tmp_min, tmp_max, storm, snow))
            client.publish("/weather/forecast/TodayPlus{0}/rain".format(days), rain)
            client.publish("/weather/forecast/TodayPlus{0}/tmp_min".format(days), tmp_min)
            client.publish("/weather/forecast/TodayPlus{0}/tmp_max".format(days), tmp_max)
            client.publish("/weather/forecast/TodayPlus{0}/storm".format(days), storm)
            client.publish("/weather/forecast/TodayPlus{0}/snow".format(days), snow)

        # all days are updated
        client.disconnect()

    def start_update(self):
        # initial forecast update
        self.update_forecast()

        # start regular update
        Timer(3600, self.start_update, ()).start()

########################################
#                MAIN                  #
########################################

if __name__ == '__main__':
    wf2m = WF2M()

    # initiate regular update
    wf2m.start_update()