import re

from django.utils import simplejson
from datetime import datetime, date

__jsdateregexp__ = re.compile(r'"\*\*(new Date\([0-9,]+\))"')
class __JSONDateEncoder__(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return '%i-%i-%iT%i-%i-%iZ' % (obj.year,
                                                      obj.month-1,
                                                      obj.day,
                                                      obj.hour,
                                                      obj.minute,
                                                      obj.second)
        if isinstance(obj, date):
            return '%i,%i,%i' % (obj.year,
                                             obj.month-1,
                                             obj.day)
        return simplejson.JSONEncoder.default(self, obj)

def dumps(obj):
    """ A (simple)json wrapper that can wrap up python datetime and date
    objects into Javascript date objects.
    @param obj: the python object (possibly containing dates or datetimes) for
        (simple)json to serialize into JSON

    @returns: JSON version of the passed object
    """
    return __jsdateregexp__.sub(r'\1', simplejson.dumps(obj, cls=__JSONDateEncoder__))
