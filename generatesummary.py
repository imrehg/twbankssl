#!/usr/bin/env python2
"""
Generates JSON output from the SSL Labs test data scrape

Run it something like this: `./generatesummary.py > ssltest.json`
"""
from datetime import datetime, timedelta
import csv
import gzip
import os
import simplejson as json
from urlparse import urlparse

def loadServerList(inputFile='servers.csv', httpsOnly=True):
    """ Load list of servers to check from configuration.

    Keyword arguments:
    inputFile -- a csv file with "Example site,https://www.example.com" line format
    """
    sites = []
    with open('servers.csv', 'rb') as csvfile:
        serverreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in serverreader:
            name, link = row
            if link:
                host = urlparse(link)
                if not httpsOnly or host.scheme == 'https':
                    sites += [{'url': host.netloc, 'name': name, 'link': link}]
    return sites

if __name__ == '__main__':
    import argparse
    import ConfigParser
    import pytz

    # Command line arguments
    parser = argparse.ArgumentParser(description='Batch SSL grade query.')
    parser.add_argument('-c', '--config', help='Congfiguration file for %(prog)s', default='script.conf')
    args = parser.parse_args()

    # Configuration
    config = ConfigParser.SafeConfigParser({'timezone': 'utc'})
    config.read(args.config)

    today = datetime.now(pytz.timezone(config.get('Common', 'timezone'))).date()
    indir = str(today)
    output = {"update": str(today)};
    results = []
    sites = loadServerList(httpsOnly=False)
    for s in sites:
        serverName = s['url']
        filename = os.path.join(indir, serverName + ".json.gz")

        thisResult = { 'name': s['name'] }

        if not os.path.exists(filename):
            thisResult['lowGrade'] = 'X'
            thisResult['link'] = s['link']
            thisResult['url'] = serverName
            thisResult['endpoints'] = []
            results += [thisResult]
            continue

        f = gzip.open(filename, 'rb')
        scanresult = json.loads(f.read())
        f.close()
        endpoints = scanresult[0]['endpoints']

        thisResult['link'] = s['link']
        thisResult['url'] = serverName
        ends = []
        for e in endpoints:
            try:
                grade = e['grade']
            except KeyError:
                grade = 'X'
                
            try:
                warnings = e['hasWarnings']
            except KeyError:
                warnings = None

            try:
                rc4 = e['details']['supportsRc4']
            except KeyError:
                rc4 = None

            try:
                poodle = e['details']['poodleTls'] > 1
            except KeyError:
                poodle = None

            try:
                beast = e['details']['vulnBeast']
            except KeyError:
                beast = None

            ends += [{'grade': grade, 
                      'ipAddress': e['ipAddress'], 
                      'hasWarnings': warnings,
                      'statusMessage': e['statusMessage'],
                      'rc4': rc4,
                      'poodle': poodle,
                      'beast': beast,
                  }]
            if ('grade' not in thisResult) or (grade < thisResult['lowGrade']):
                if grade != 'X':
                    thisResult['lowGrade'] = grade
        if 'lowGrade' not in thisResult:
            thisResult['lowGrade'] = 'X'
        thisResult['endpoints'] = ends
        results += [thisResult]
    output['results'] = results
    print json.dumps(output)
