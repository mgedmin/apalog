#!/usr/bin/env python3
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

    def __init__(self, ip=None, date=None, hour=None, minute=None, user_agent=None):
        self.ip = ip
        self.date = date
        self.hour = hour
        self.minute = minute
        self.user_agent = user_agent


def parse_logs(filenames):
    """Parse several Apache log files, return Entry objects."""
    return itertools.chain(*map(parse_log, filenames))


def parse_date(datestr):
    """Parse a date (YYYY-MM-DD or DD/Mmm/YYYY) into a datetime.date."""
    if '-' in datestr:
        y, m, d = datestr.split('-')
    else:
        d, m, y = datestr.split('/')
        m = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
             'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
             'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}.get(m.lower(), m)
    return datetime.date(int(y), int(m), int(d))


def parse_log(filename):
    """Parse Apache common log format, return Entry objects."""
    rx = re.compile(r"^(\S+) \S+ \S+"
                    r" \[\s*(\d+/\w+/\d+):(\d+):(\d+):\d+ [-+]\d+\]"
                    r' "[^"]*" \d+ \d+ "[^"]*" "([^"]*)"')
    for line in open(filename):
        # typical apache access log format:
        # 1.2.3.4 - - [18/Dec/2009:16:17:18 +0100] "GET /url HTTP/1.1" 200 1000
        #   "http://referrer" "UserAgent" "-"
        # my preferred custom log format:
        # 1.2.3.4 - - [18/Dec/2009:16:17:18 +0100] "GET /url HTTP/1.1" 200 1000
        #   "http://referrer" "UserAgent" 0s 4894us example.com:443
        m = rx.match(line)
        if m:
            ip, date, hour, minute, user_agent = m.groups()
            date = parse_date(date)
            hour = int(hour)
            minute = int(minute)
            yield Entry(ip, date, hour, minute, user_agent)


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


def filter_out_user_agent(entries, user_agent):
    """Return only those log entries that don't match the given user agent.

    Does substring matching.
    """
    for entry in entries:
        if user_agent not in entry.user_agent:
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
    parser = optparse.OptionParser(
        "usage: %prog [options] filename ...",
        description=__doc__.lstrip().split("\n\n")[0])
    parser.add_option("-a", "--all", action="store_true",
                      help="combine all dates into one grid")
    parser.add_option("-d", metavar='DATE', dest="date",
                      help="print grid for given date instead of today")
    parser.add_option("-x", metavar='IP', dest="exclude", action="append",
                      help="ignore requests from this IP")
    parser.add_option("-U", metavar='USER-AGENT', dest="exclude_agent", action="append",
                      help="ignore requests from this user agent")
    opts, files = parser.parse_args()
    if not files:
        parser.error("please specify an apache access log file to parse")
    if opts.all:
        date = None
    elif opts.date:
        date = parse_date(opts.date)
    else:
        date = datetime.date.today()
    entries = parse_logs(files)
    if date is not None:
        entries = filter_by_date(entries, date)
    if opts.exclude is not None:
        for ip in opts.exclude:
            entries = filter_out_ip(entries, ip)
    if opts.exclude_agent is not None:
        for agent in opts.exclude_agent:
            entries = filter_out_user_agent(entries, agent)
    requests = pigeonhole(entries)
    if date is not None:
        print("Requests handled on %s:" % date)
    else:
        print("Requests handled on all days:")
    timegrid(requests)


if __name__ == "__main__":
    main()
