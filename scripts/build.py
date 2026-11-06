"""Build a standalone offline page without a JS bundler or Python dependencies."""
import argparse
import json
from pathlib import Path
import shutil
from project import ROOT


def build(output):
    bundle = json.loads((ROOT/'data/history.json').read_text())
    if bundle.get('errors') or len(bundle['funds']) != 16:
        raise ValueError('Expected a verified 16-fund snapshot')
    html = (ROOT/'web/dashboard_template.html').read_text()
    replacements = {
        '__DATA_JSON__': json.dumps(bundle,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'),
        '__APP_JS__': (ROOT/'web/app.js').read_text(),
        '__DAILY_CHART_JS__': (ROOT/'web/daily_charts.js').read_text(),
        '__VIEWPORT_JS__': (ROOT/'web/chart_viewport.js').read_text(),
        '__ECHARTS_JS__': (ROOT/'vendor/echarts.min.js').read_text(),
        '__CHART_OPTIONS_JS__': (ROOT/'web/chart_options.js').read_text(),
        '__UI_CSS__': (ROOT/'web/ui.css').read_text(),
        '__PICO_CSS__': (ROOT/'vendor/pico.conditional.min.css').read_text(),
        '__TOM_SELECT_CSS__': (ROOT/'vendor/tom-select.css').read_text(),
        '__TOM_SELECT_JS__': (ROOT/'vendor/tom-select.base.min.js').read_text(),
    }
    for placeholder, value in replacements.items():
        html = html.replace(placeholder,value)
    if any(placeholder in html for placeholder in replacements):
        raise ValueError('An HTML template placeholder was not replaced')
    output.mkdir(parents=True,exist_ok=True)
    (output/'index.html').write_text(html,encoding='utf-8')
    (output/'data').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'data/history.json',output/'data/history.json')
    if (ROOT/'charts').exists():
        shutil.copytree(ROOT/'charts',output/'charts',dirs_exist_ok=True)
    return output/'index.html'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    print('Built',build(parser.parse_args().output.resolve()))
