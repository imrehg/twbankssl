#!/usr/bin/env python3

import argparse
import configparser
from datetime import datetime, timedelta
import csv
import lzma
import os
import pytz
import json
import subprocess
import sys
from time import sleep
from urllib.parse import urlparse

# Command line arguments
parser = argparse.ArgumentParser(description='Batch SSL grade query.')
parser.add_argument('-c', '--config', help='Congfiguration file for %(prog)s', default='script.conf')
parser.add_argument('-q', '--quiet', help='Run quiet', action='store_true', default=False)
args = parser.parse_args()

# Configuration
config = configparser.SafeConfigParser({'timezone': 'utc', 'datadir': 'data'})
config.read(args.config)

QUIET = args.quiet
DATADIR = config.get('Common', 'datadir');

# Command line arguments for the ssllabs scan
# For more info, check `./ssllabs-scan -help`
sslcmd = [config.get('Scrape', 'ssllabsbin'),
          "-quiet=true",
          "-usecache=true",
          "-maxage=2",
         ]

# Set output directory
today = datetime.now(pytz.timezone(config.get('Common', 'timezone'))).date()
outdir = os.path.join(DATADIR, str(today))

def getServerAssessment(serverName=None):
    """ Task to done a single server assessment and save the results

    Keyword arguments:
    servername -- what server to query (FQDN)
    """
    if serverName is None:
        return

    if not QUIET:
        print("Doing %s" %(serverName))
    thiscmd = sslcmd + [serverName]
    results = None

    try:
        results = subprocess.check_output(thiscmd, stderr=subprocess.STDOUT,)
    except subprocess.CalledProcessError as e:
        if e.returncode == 2:  # just the output of "-help"
            pass
        else:
            print(e.output)
            return

    if results:
        resultsjson = json.loads(results)
        if len(resultsjson) > 0 and resultsjson[0]['status'] == 'READY':
            filename = os.path.join(outdir, serverName + ".json.xz")
            with lzma.open(filename, 'wb') as outfile:
                outfile.write(str.encode(json.dumps(resultsjson)))
        else:
            if not QUIET:
                reason = "Not enough data" if len(resultsjson) == 0 else "Not READY"
                print("Sleep and retry %s in 3mins: %s" %(serverName, reason))
            sleep(3*60)
            getServerAssessment(serverName)
    if not QUIET:
        print("Done: "+serverName)

def loadServerList(inputFile='servers.csv', httpsonly=True):
    """ Load list of servers to check from configuration.

    Keyword arguments:
    inputFile -- a csv file with "Example site,https://www.example.com" line format
    """
    servers = []
    with open('servers.csv', 'r') as csvfile:
        serverreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in serverreader:
            name, url = row
            if url:
                host = urlparse(url)
                if not httpsonly or host.scheme == 'https':
                    servers += [host.netloc]
    return servers

if __name__ == '__main__':
    from multiprocessing import Pool

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Load server names
    servers = loadServerList()

    # Run the assessment in parallel
    p = Pool(3)
    p.map_async(getServerAssessment, servers).get(9999999)
    p.close()
    p.join()
