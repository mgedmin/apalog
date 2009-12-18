#!/usr/bin/env python
# please keep python 2.4 compatibility
import sys
import re
import datetime


class Entry(object):
    __slots__ = ['date', 'hour', 'minute']
    def __init__(self, date=None, hour=None, minute=None):
        self.date = date
        self.hour = hour
        self.minute = minute


def parse_log(filename):
    """Parse Apache common log format, return Entry objects."""
    rx = re.compile(r"^\S+ \S+ \S+"
                    r" \[\s*(\d+)/(\w+)/(\d+):(\d+):(\d+):\d+ [-+]\d+\]")
    months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
              'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
    for line in open(filename):
        # 1.2.3.4 - - [18/Dec/2009:16:17:18 +0100] "GET /url HTTP/1.1" 200 1000 "http://referrer" "UserAgent" "-"
        m = rx.match(line)
        if m:
            day, month, year, hour, minute = m.groups()
            year = int(year)
            month = months[month.lower()]
            day = int(day)
            hour = int(hour)
            minute = int(minute)
            try:
                date = datetime.date(year, month, day)
            except ValueError, e:
                raise ValueError('%s/%s/%s: %s' % (day, month, year, e))
            yield Entry(date, hour, minute)


def filter_by_date(entries, date):
    """Return only those log entries that fall on a given date."""
    for entry in entries:
        if entry.date == date:
            yield entry

def pigeonhole(entries, requests=None):
    """Put log entries into time slots, return a dict (h, m) -> count."""
    if not requests:
        requests = {}
    for entry in entries:
        h, m = entry.hour, entry.minute
        requests[h, m] = requests.get((h, m), 0) + 1
    return requests


def timegrid(requests):
    """Draw a grid given a mapping of (hour, minute) -> number_of_requests"""
    w = sys.stdout.write
    for h in range(24):
        w("%02d:00 [" % h)
        for m in range(60):
            if requests.get((h, m)):
                w("#")
            else:
                w(" ")
        w("]\n")


def main():
    try:
        filename = sys.argv[1]
    except IndexError:
        sys.exit("usage: %s filename" % sys.argv[0])
    date = datetime.date.today()
    entries = parse_log(filename)
    day_entries = filter_by_date(entries, date)
    requests = pigeonhole(day_entries)
    print "Requests handled today:"
    timegrid(requests)


if __name__ == "__main__":
    main()
