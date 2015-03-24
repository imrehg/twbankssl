#!/usr/bin/env python2

from datetime import date, timedelta
import csv
import gzip
import os
import simplejson as json
import subprocess
from urlparse import urlparse

# Command line arguments for the ssllabs scan
# For more info, check `./ssllabs-scan -help`
sslcmd = ["./ssllabs-scan", "-quiet=true", "-usecache=true", "-maxage=2"]

# Set output directory
today = date.today()
outdir = str(today)

def getServerAssessment(serverName=None):
    """ Task to done a single server assessment and save the results

    Keyword arguments:
    servername -- what server to query (FQDN)
    """
    if serverName is None:
        return

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
        if resultsjson[0]['status'] != 'READY':
            return
        filename = os.path.join(outdir, serverName + ".json.gz")
        f = gzip.open(filename, 'wb')
        f.write(json.dumps(resultsjson))
        f.close()
    print("Done: "+serverName)

def loadServerList(inputFile='servers.csv'):
    """ Load list of servers to check from configuration.

    Keyword arguments:
    inputFile -- a csv file with "Example site,https://www.example.com" line format
    """
    servers = []
    with open('servers.csv', 'rb') as csvfile:
        serverreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in serverreader:
            name, url = row
            if url:
                host = urlparse(url)
                if host.scheme == 'https':
                    servers += [host.netloc]
    return servers


if __name__ == '__main__':
    from multiprocessing import Pool

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Load server names
    servers = loadServerList()

    # Run the assessment in parallel
    p = Pool(8)
    p.map(getServerAssessment, servers)
    p.close()
    p.join()
