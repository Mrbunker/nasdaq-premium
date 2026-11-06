"""Project paths, HTTP cache, CSV output and complete-session cutoff."""
import csv
import datetime as dt
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RAW = ROOT / '.cache' / 'raw'
CHINA = dt.timezone(dt.timedelta(hours=8))


def latest_complete_day(now=None):
    now = now or dt.datetime.now(CHINA)
    day = now.date()
    if now.time() < dt.time(15, 30):
        day -= dt.timedelta(days=1)
    while day.weekday() >= 5:
        day -= dt.timedelta(days=1)
    return day


def download(url, destination, referer=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.environ.get('NAQD_REFRESH') != '1' and destination.exists() and destination.stat().st_size > 100:
        return destination.read_text(encoding='utf-8-sig')
    command = ['curl','-L','--fail','--retry','2','--retry-all-errors','--retry-delay','2','--connect-timeout','10','--max-time','40','-sS',url]
    if referer:
        command += ['-H','Referer: '+referer]
    response = subprocess.run(command, capture_output=True, check=True)
    text = response.stdout.decode('utf-8-sig')
    temporary = destination.with_suffix(destination.suffix+'.tmp')
    temporary.write_text(text, encoding='utf-8')
    temporary.replace(destination)
    return text


def write_csv(path, records, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
