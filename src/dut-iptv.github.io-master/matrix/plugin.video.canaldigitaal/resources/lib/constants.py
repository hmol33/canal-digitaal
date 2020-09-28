CONST_BASE_URL = 'https://livetv.canaldigitaal.nl'
CONST_DEFAULT_API = 'https://tvapi.solocoo.tv/v1'
CONST_LOGIN_URL = 'https://login.canaldigitaal.nl'

CONST_LOGIN_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_LOGIN_URL,
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Accept-Encoding': 'deflate, br',
    'Accept-Language': 'en-US,en;q: 0.9,nl;q: 0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
}

CONST_BASE_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_BASE_URL,
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': CONST_BASE_URL + '/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q: 0.9,nl;q: 0.8',
}

CONST_EPG = 'https://dut-epg.github.io/c.epg.xml.zip'
CONST_IMAGES = 'https://dut-epg.github.io/c.images.zip'
CONST_MD5 = 'https://dut-epg.github.io/c.md5.json'
CONST_MINIMALEPG = 'https://dut-epg.github.io/c.epg.xml.minimal.zip'
CONST_RADIO = 'https://dut-epg.github.io/radio.m3u8'
CONST_SETTINGS = 'https://dut-epg.github.io/c.settings.json'
CONST_VOD = 'https://dut-epg.github.io/c.vod.json'