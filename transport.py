import datetime
import pytz

class Transport:

    local_tz = pytz.timezone('Europe/Helsinki')

    def __init__(self, stop_name, route_code, headsign, service_day, departure_time):
        self.stop_name = stop_name
        self.route_code = route_code
        self.departure_time = departure_time
        self.service_day = service_day
        self.headsign = headsign
    
    def get_departure_time(self):
        return self.get_current_day_midnight()
    
    def get_current_day_midnight(self):
        tz_aware_datetime = datetime.datetime.fromtimestamp(self.service_day + self.departure_time)
        localizedDateTime = pytz.utc.localize(tz_aware_datetime, is_dst=None)
        return localizedDateTime.strftime('%H:%M')