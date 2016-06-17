from datetime import datetime, tzinfo, timedelta

class Offset(tzinfo):
    def utcoffset(self, dt):
        utc = datetime.utcnow()
        offset = datetime.now() - utc
        offset_hours = offset.seconds // 3600
        return timedelta(hours=offset_hours)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self,dt):
        return "Moscow"

class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=0)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self,dt):
        return "London"

def get_duration(time_str):
    '''
    This function calculates duration with taking
    into account a time zone offset.

    :param time_str: example: 2016-06-12T19:28:41Z
    :return: time_delta
    '''

    raw_date = time_str.split('T')
    date = [int(i) for i in raw_date[0].split('-')]
    time = [int(i) for i in raw_date[1][:-1].split(':')]

    time_start = datetime(year=date[0], month=date[1], day=date[2], hour=time[0], minute=time[1], second=time[2], tzinfo=UTC())
    time_delta = datetime.now(tz=Offset()) - time_start
    return '{0}:{1}:{2}'.format(time_delta.seconds//3600, (time_delta.seconds//60)%60, time_delta.seconds % 60)
