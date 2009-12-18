#!/usr/bin/env python
"""
Parses an apache log file (in common log format) and prints an activity grid:
for every hour and minute were there any requests processed today?

Requires Python 2.4 or later.
"""
import sys
import re
import datetime
import optparse
import itertools


class Entry(object):
    __slots__ = ['ip', 'date', 'hour', 'minute']
    def __init__(self, ip=None, date=None, hour=None, minute=None):
        self.ip = ip
        self.date = date
        self.hour = hour
        self.minute = minute


def parse_logs(filenames):
    """Parse several Apache log files, return Entry objects."""
    return itertools.chain(*map(parse_log, filenames))


def parse_log(filename):
    """Parse Apache common log format, return Entry objects."""
    rx = re.compile(r"^(\S+) \S+ \S+"
                    r" \[\s*(\d+)/(\w+)/(\d+):(\d+):(\d+):\d+ [-+]\d+\]")
    months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
              'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
    for line in open(filename):
        # 1.2.3.4 - - [18/Dec/2009:16:17:18 +0100] "GET /url HTTP/1.1" 200 1000 "http://referrer" "UserAgent" "-"
        m = rx.match(line)
        if m:
            ip, day, month, year, hour, minute = m.groups()
            year = int(year)
            month = months[month.lower()]
            day = int(day)
            hour = int(hour)
            minute = int(minute)
            try:
                date = datetime.date(year, month, day)
            except ValueError, e:
                raise ValueError('%s/%s/%s: %s' % (day, month, year, e))
            yield Entry(ip, date, hour, minute)


def filter_by_date(entries, date):
    """Return only those log entries that fall on a given date."""
    for entry in entries:
        if entry.date == date:
            yield entry


def filter_out_ip(entries, ip):
    """Return only those log entries that don't match the given IP."""
    for entry in entries:
        if entry.ip != ip:
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
    w("      [")
    for m in range(60):
        if m % 10 == 0:
            w(str(m // 10))
        elif m % 10 == 1:
            w("0")
        else:
            w(" ")
    w("]\n")
    for h in range(24):
        w("%02d:00 [" % h)
        for m in range(60):
            if requests.get((h, m)):
                w("#")
            elif m % 10 == 0 and m > 0:
                w(":")
            else:
                w(" ")
        w("]\n")


def main():
    parser = optparse.OptionParser("usage: %prog [options] filename ...",
                                   description=__doc__.lstrip())
    parser.add_option("-x", metavar='IP', dest="exclude", action="append",
                      help="ignore requests from this IP")
    opts, files = parser.parse_args()
    if not files:
        parser.error("please specify an apache access log file to parse")
    date = datetime.date.today()
    entries = parse_logs(files)
    day_entries = filter_by_date(entries, date)
    if opts.exclude is not None:
        for ip in opts.exclude:
            day_entries = filter_out_ip(day_entries, ip)
    requests = pigeonhole(day_entries)
    print "Requests handled today:"
    timegrid(requests)


if __name__ == "__main__":
    main()
