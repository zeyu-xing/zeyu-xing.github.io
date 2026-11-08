"""Render the local Jekyll build with the runner's Chrome; never publish it."""
import base64
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import urllib.request

output = Path(os.environ.get('LAYOUT_PREVIEW_DIR', '/tmp/academic-preview'))
output.mkdir(parents=True, exist_ok=True)

# The font is a QA dependency only; the public site uses system fonts.
font_dir = Path.home() / '.local/share/fonts'
font_dir.mkdir(parents=True, exist_ok=True)
font = font_dir / 'NotoSansCJKsc-Regular.otf'
if not font.exists():
    font.write_bytes(urllib.request.urlopen(
        'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf',
        timeout=60).read())
subprocess.run(['fc-cache', '-f', str(font_dir)], check=True, stdout=subprocess.DEVNULL)

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

server = http.server.ThreadingHTTPServer(
    ('127.0.0.1', 8765), functools.partial(QuietHandler, directory='_site'))
threading.Thread(target=server.serve_forever, daemon=True).start()
driver = subprocess.Popen(
    [shutil.which('chromedriver') or '/usr/local/share/chromedriver-linux64/chromedriver', '--port=9515'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def request(method, path, data=None):
    payload = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request('http://127.0.0.1:9515' + path, data=payload,
                                 method=method, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.load(response)
    value = result.get('value', result)
    if isinstance(value, dict) and value.get('error'):
        raise RuntimeError(value)
    return value

session = None
results = []
try:
    for _ in range(100):
        try:
            request('GET', '/status')
            break
        except OSError:
            time.sleep(0.1)
    session = request('POST', '/session', {'capabilities': {'alwaysMatch': {
        'browserName': 'chrome',
        'goog:chromeOptions': {'args': ['--headless=new', '--no-sandbox',
                                       '--disable-dev-shm-usage', '--hide-scrollbars']}
    }}})['sessionId']
    prefix = '/session/' + session

    def command(path, data=None, method='POST'):
        return request(method, prefix + path, data)

    def cdp(name, params):
        return command('/goog/cdp/execute', {'cmd': name, 'params': params})

    def evaluate(script):
        return command('/execute/sync', {'script': script, 'args': []})

    for device, width, height in [('desktop', 1280, 900), ('mobile', 390, 844)]:
        cdp('Emulation.setDeviceMetricsOverride', {
            'width': width, 'height': height, 'deviceScaleFactor': 1,
            'mobile': device == 'mobile'})
        for name, path in [('home', '/'), ('research', '/research/')]:
            command('/url', {'url': 'http://127.0.0.1:8765' + path})
            command('/execute/async', {
                'script': 'const done=arguments[arguments.length-1]; document.fonts.ready.then(()=>done(true));',
                'args': []})
            metrics = evaluate('return {width:innerWidth, scrollWidth:document.documentElement.scrollWidth, nav:[...document.querySelectorAll("nav a")].map(a=>a.textContent.trim()), sidebar:!!document.querySelector(".sidebar")};')
            assert metrics['width'] == width, metrics
            assert metrics['scrollWidth'] <= width, metrics
            assert metrics['nav'] == ['Home', 'Research'], metrics
            assert not metrics['sidebar'], metrics
            results.append({'page': name, 'device': device, **metrics})
            page_height = evaluate('return Math.max(document.documentElement.scrollHeight, innerHeight);')
            png = cdp('Page.captureScreenshot', {
                'format': 'png', 'captureBeyondViewport': True,
                'clip': {'x': 0, 'y': 0, 'width': width, 'height': page_height, 'scale': 1}
            })['data']
            (output / f'{name}-{device}.png').write_bytes(base64.b64decode(png))
            if device == 'desktop':
                pdf = cdp('Page.printToPDF', {'printBackground': True, 'preferCSSPageSize': True,
                                             'displayHeaderFooter': False})
                (output / f'{name}.pdf').write_bytes(base64.b64decode(pdf['data']))
            if name == 'home':
                assert not evaluate('return document.documentElement.outerHTML.includes(atob(document.querySelector(".copy-email").dataset.user)+"@"+atob(document.querySelector(".copy-email").dataset.domain));')
                cdp('Browser.grantPermissions', {'origin': 'http://127.0.0.1:8765',
                                                'permissions': ['clipboardReadWrite', 'clipboardSanitizedWrite']})
                command('/element', {'using': 'css selector', 'value': '.copy-email'})
                evaluate('document.querySelector(".copy-email").click(); return true;')
                for _ in range(30):
                    if evaluate('return document.querySelector(".email-status").textContent;') == 'Email copied.':
                        break
                    time.sleep(0.1)
                assert evaluate('return document.querySelector(".email-status").textContent;') == 'Email copied.'
    (output / 'checks.json').write_text(json.dumps(results, indent=2))
    print(json.dumps({'layout_checks': results, 'email_copy': 'passed'}))
finally:
    if session:
        request('DELETE', '/session/' + session)
    driver.terminate()
    server.shutdown()
