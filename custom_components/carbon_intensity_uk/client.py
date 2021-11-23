"""Client."""
from datetime import datetime, timezone
import aiohttp
import logging
import numpy as np

from .const import INTENSITY

_LOGGER = logging.getLogger(__name__)

intensity_indexes = {
    2021: [50, 140, 220, 330],
    2022: [45, 130, 210, 310],
    2023: [40, 120, 200, 290],
    2024: [35, 110, 190, 270],
    2025: [30, 100, 180, 250],
    2026: [25, 90, 170, 230],
    2027: [20, 80, 160, 210],
    2028: [15, 70, 150, 190],
    2029: [10, 60, 140, 170],
    2030: [5, 50, 130, 150],
}

class Client:
    """Carbon Intensity API Client"""

    def __init__(self, postcode):
        self.postcode = postcode
        self.headers = {"Accept": "application/json"}
        _LOGGER.debug(str(self))

    def __str__(self):
        return "{ postcode: %s, headers: %s }" % (self.postcode, self.headers)

    async def async_raw_get_data(self, from_time=None):
        if from_time is None:
            from_time = datetime.utcnow()
        request_url = (
            "https://api.carbonintensity.org.uk/regional/intensity/%s/fw48h/postcode/%s"
            % (from_time.strftime("%Y-%m-%dT%H:%MZ"), self.postcode)
        )
        _LOGGER.debug("Request: %s" % request_url)
        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as resp:
                json_response = await resp.json()
                return json_response

    async def async_get_data(self, from_time=None, target='low'):
        raw_data = await self.async_raw_get_data(from_time)
        return generate_response(raw_data, target)

def generate_response(json_response, target='low'):
    intensities = []
    period_start = []
    period_end = []
    response = {}
    data = json_response["data"]["data"]
    postcode = json_response["data"]["postcode"]
    two_day_forecast = True

    current_intensity_index = intensity_indexes[datetime.now().year]
    def get_index(intensity):
        if intensity < current_intensity_index[0]:
            return "very low"
        elif intensity < current_intensity_index[1]:
            return "low"
        elif intensity < current_intensity_index[2]:
            return "moderate"
        elif intensity < current_intensity_index[3]:
            return "high"
        else:
            return "very high"

    # sanitise input length
    if datetime.strptime(data[0]["to"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc) < datetime.utcnow().replace(tzinfo=timezone.utc):
        data.pop(0)
    if len(data) > 96:
        data = data[0:96]
    if len(data) < 48:
        return {"error": "malformed data"}
    if len(data) % 2 == 1:
        data.pop(-1)
    if len(data) < 56:
        two_day_forecast = False

    for period in data:
        period_start.append(datetime.strptime(
                period["from"], "%Y-%m-%dT%H:%MZ"
            ).replace(tzinfo=timezone.utc))
        period_end.append(datetime.strptime(
                period["to"], "%Y-%m-%dT%H:%MZ"
            ).replace(tzinfo=timezone.utc))
        intensities.append(period["intensity"]["forecast"])
  
    intensity_array = np.array(intensities)
    hourly_intensities = np.convolve(intensity_array, np.ones(2)/2 , 'valid')[::2]

    hours_start = period_start[::2]
    hours_end = period_end[1::2]

    average_intensity24h  = np.convolve(hourly_intensities[:24], np.ones(4)/4 , 'valid')
    best24h = np.argmin(average_intensity24h)

    if two_day_forecast:
        average_intensity48h  = np.convolve(hourly_intensities[24:], np.ones(4)/4 , 'valid')
        best48h = np.argmin(average_intensity48h)
    else:
        best48h = 0

    hourly_forecast = []
    for i in range(len(hours_start)):
        hourly_forecast.append({
            "from":      hours_start[i],
            "to":        hours_end[i],
            "intensity": hourly_intensities[i],
            "index":     get_index(hourly_intensities[i]),
            "optimal":   True if (hours_start[i]>=hours_start[best24h] and hours_end[i]<=hours_end[best24h+3]) or \
                                 (two_day_forecast and hours_start[i]>=hours_start[best48h+24] and hours_end[i]<=hours_end[best48h+3+24]) else False,
        })

    response = {
        "data": {
            "current_period_from": hourly_forecast[0]["from"],
            "current_period_to": hourly_forecast[0]["to"],
            "current_period_forecast": hourly_forecast[0]["intensity"],
            "current_period_index": hourly_forecast[0]["index"],
            "optimal_window_from" : hours_start[best24h],
            "optimal_window_to" : hours_end[best24h+3],
            "optimal_window_forecast" : average_intensity24h[best24h],
            "optimal_window_index" : get_index(average_intensity24h[best24h]),
            "optimal_window_48_from" : hours_start[best48h+24] if two_day_forecast else None,
            "optimal_window_48_to" : hours_end[best48h+3+24] if two_day_forecast else None,
            "optimal_window_48_forecast" : average_intensity48h[best48h] if two_day_forecast else None, # no need for +24 as we are reading from a reduced array
            "optimal_window_48_index" : get_index(average_intensity48h[best48h]) if two_day_forecast else None,
            "unit": "gCO2/kWh",
            "postcode": postcode,
            "forecast": hourly_forecast,
        }
    }
    return response
