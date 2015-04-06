#!/usr/bin/env python2
"""
Generates JSON output from the SSL Labs test data scrape

Run it something like this: `./generatesummary.py > ssltest.json`
"""
from datetime import datetime, timedelta, time
import csv
import gzip
import os
import simplejson as json
from urlparse import urlparse
from feedgen.feed import FeedGenerator

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

def parsedate(site, indir):
    """ Calculat scores for a site and a specific date

    Keyword arguments:
    site -- site data dict
    indir -- data directory
    """
    serverName = site['url']
    filename = os.path.join(indir, serverName + ".json.gz")
    thisResult = { 'name': site['name'] }

    if not os.path.exists(filename):
        thisResult['lowGrade'] = 'X'
        thisResult['link'] = site['link']
        thisResult['url'] = serverName
        thisResult['endpoints'] = []
        return thisResult

    f = gzip.open(filename, 'rb')
    scanresult = json.loads(f.read())
    f.close()
    endpoints = scanresult[0]['endpoints']

    thisResult['link'] = site['link']
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
            forwardSecrecy = e['details']['forwardSecrecy'] >= 2   # bit 1 is set, modern browsers
        except:
            forwardSecrecy = False

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
                  'forwardSecrecy': forwardSecrecy,
              }]
        if ('grade' not in thisResult) or (grade < thisResult['lowGrade']):
            if grade != 'X':
                thisResult['lowGrade'] = grade
    if 'lowGrade' not in thisResult:
        thisResult['lowGrade'] = 'X'
    thisResult['endpoints'] = ends
    return thisResult

if __name__ == '__main__':
    import argparse
    import ConfigParser
    import pytz

    # Command line arguments
    parser = argparse.ArgumentParser(description='Batch SSL grade query.')
    parser.add_argument('-c', '--config', help='Congfiguration file for %(prog)s', default='script.conf')
    parser.add_argument('-r', '--rss', help='Generate rss feed and write it to a file at RSS', default='')
    args = parser.parse_args()

    # Configuration
    config = ConfigParser.SafeConfigParser({'timezone': 'utc',
                                            'wayback': 60,
                                            'datadir': 'data',
                                            'rsstitle': 'SSL test',
                                            'rssdescription': 'SSL test',
                                            'rsslink': '',
                                        })
    config.read(args.config)
    DATADIR = config.get('Common', 'datadir')
    RSS = len(args.rss) > 0
    TZ = config.get('Common', 'timezone')

    if RSS:
        rssfile = args.rss
        rsstitle = config.get('RSS', 'rsstitle')
        fg = FeedGenerator()
        fg.title(rsstitle)
        fg.description(config.get('RSS', 'rssdescription'))
        fg.link(href=config.get('RSS', 'rsslink'), rel='self')
        rssfeed  = fg.rss_str(pretty=True)
        fg.rss_file(rssfile)

    timezone = pytz.timezone(TZ)
    today = datetime.now(timezone).date()
    indir = os.path.join(DATADIR, str(today));
    output = {"update": str(today)};
    results = []
    grades = {}
    sites = loadServerList(httpsOnly=False)
    for idx, s in enumerate(sites):
        thisResult = parsedate(s, indir)
        results += [thisResult]
        grades[idx] = [thisResult['lowGrade']]
    wayback = config.getint('Analyze', 'wayback');
    for w in range(1, wayback):
        oldday = today - timedelta(days = w)
        olddayafter = today - timedelta(days = (w - 1))
        indir = os.path.join(DATADIR, str(oldday));
        changes = []
        for idx, s in enumerate(sites):
            oldResult = parsedate(s, indir)
            grades[idx].insert(0, oldResult['lowGrade'])
            if grades[idx][0] != grades[idx][1]:
                changes += [{'index': idx, 'oldgrade': grades[idx][0], 'newgrade': grades[idx][1]}]
        if RSS and len(changes) > 0:
            fe = fg.add_entry()
            fe.title('Changes on %s' %(olddayafter))
            content = ''
            for c in changes:
                item = results[c['index']]
                org = results[c['index']]['name']
                content += '<a href="%s">%s</a> went from grade %s to %s.<br>' %(sites[c['index']]['link'], item['name'], c['oldgrade'], c['newgrade'])
            fe.content(content = content)
            pubDate = timezone.localize(datetime.combine(olddayafter, datetime.min.time()))
            fe.pubdate(pubDate = pubDate)

    for idx, s in enumerate(sites):
        results[idx]['wayback'] = grades[idx]
    output['results'] = results
    print json.dumps(output)

    if RSS:
        rssfeed  = fg.rss_str(pretty=True)
        fg.rss_file(rssfile)
