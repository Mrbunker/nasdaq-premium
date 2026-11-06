"""Refresh all sources, cross-check prices and derive daily/monthly comparisons."""
import argparse
import os
import subprocess
import sys
from project import DATA, ROOT

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cutoff',help='Last complete Chinese session date (YYYY-MM-DD)')
parser.add_argument('--cached',action='store_true',help='Reproduce locally cached responses without refreshing')
args = parser.parse_args()
snapshot = DATA/'history.json'
previous = snapshot.read_bytes() if snapshot.exists() else None
environment = os.environ.copy()
environment['NAQD_REFRESH'] = '0' if args.cached else '1'
try:
    fetch = [sys.executable,str(ROOT/'scripts/fetch_data.py')]
    if args.cutoff:
        fetch += ['--cutoff',args.cutoff]
    if args.cached:
        fetch.append('--cached')
    subprocess.run(fetch,env=environment,check=True)
    for filename in ['validate_data.py','compute_daily.py','compute_monthly.py','validate_snapshot.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/filename)],env=environment,check=True)
except BaseException:
    if previous is not None:
        snapshot.write_bytes(previous)
    raise
