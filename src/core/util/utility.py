import re
import requests

from datetime import datetime, timedelta, timezone

"""
    resolves the external IP address of local machine
    we rely on an external service to reflect the IP

    https://stackoverflow.com/questions/2311510/getting-a-machines-external-ip-address-with-python
"""


def getExternalIPAddress():
    site = requests.get("http://checkip.dyndns.org/")
    grab = re.findall('([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', site.text)
    return grab[0]



########################################
#          OWM UTILITY METHODS         #
########################################

"""
Defines the day for OWM request
:param  days: defines the offset from today, e.g. 1 = tomorrow, 2 = day after tomorrow, max: 4
:type   days: int
"""
def dayinfuture(days):
    # limit range for free edition
    if days < 1:
        days = 1
    if days > 4:
        days = 4
    # calculating data based on timestamps.tomorrow definition
    now = datetime.now(timezone.utc)
    tomorrow_date = now.date() + timedelta(days)
    return datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day,
                    now.hour, now.minute, 0, 0, timezone.utc)