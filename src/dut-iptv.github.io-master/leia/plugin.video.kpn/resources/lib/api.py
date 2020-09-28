import os, time, xbmc

from resources.lib.base import gui, settings
from resources.lib.base.constants import ADDON_ID, ADDON_PROFILE
from resources.lib.base.exceptions import Error
from resources.lib.base.log import log
from resources.lib.base.session import Session
from resources.lib.base.util import check_key, clean_filename, combine_playlist, find_highest_bandwidth, get_credentials, is_file_older_than_x_minutes, load_file, set_credentials, write_file
from resources.lib.constants import CONST_BASE_HEADERS, CONST_IMAGE_URL
from resources.lib.language import _

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

try:
    unicode
except NameError:
    unicode = str

class APIError(Error):
    pass

class API(object):
    def new_session(self, force=False, retry=True, channels=False):
        self.check_vars()

        if self._debug_mode:
            log.debug('Executing: api.new_session')
            log.debug('Vars: force={force}, retry={retry}, channels={channels}'.format(force=force, retry=retry, channels=channels))
            log.debug('Cookies: {cookies}'.format(cookies=self._cookies))

        username = self._username
        password = self._password

        if len(self._cookies) > 0 and len(username) > 0 and not force and not channels and self._session_age > int(time.time() - 7200) and self._last_login_success:
            self.logged_in = True

            try:
                self._session
            except:
                self._session = Session(cookies_key='_cookies')

                if self._debug_mode:
                    log.debug('Creating new Requests Session')
                    log.debug('Request Session Headers')
                    log.debug(self._session.headers)
                    log.debug('api.logged_in: {logged_in}'.format(logged_in=self.logged_in))

            return True

        self.logged_in = False

        if self._debug_mode:
            log.debug('api.logged_in: {logged_in}'.format(logged_in=self.logged_in))

        if not len(username) > 0:
            if self._debug_mode:
                log.debug('Username length = 0')
                log.debug('Execution Done: api.new_session')

            settings.setBool(key="_last_login_success", value=self.logged_in)
            self._last_login_success = self.logged_in

            return False

        if not len(password) > 0:
            email_or_pin = settings.getBool(key='email_instead_of_customer')

            if not force:
                if self._debug_mode:
                    log.debug('Password length = 0 and force is false')
                    log.debug('Execution Done: api.new_session')

                settings.setBool(key="_last_login_success", value=self.logged_in)
                self._last_login_success = self.logged_in

                return False

            if email_or_pin:
                password = gui.input(message=_.ASK_PASSWORD2, hide_input=True).strip()
            else:
                password = gui.numeric(message=_.ASK_PASSWORD).strip()

            if not len(password) > 0:
                if self._debug_mode:
                    log.debug('Password length = 0')
                    log.debug('Execution Done: api.new_session')

                if email_or_pin:
                    gui.ok(message=_.EMPTY_PASS2, heading=_.LOGIN_ERROR_TITLE)
                else:
                    gui.ok(message=_.EMPTY_PASS, heading=_.LOGIN_ERROR_TITLE)

                settings.setBool(key="_last_login_success", value=self.logged_in)
                self._last_login_success = self.logged_in

                return False

        self.login(username=username, password=password, channels=channels, retry=retry)

        if self._debug_mode:
            log.debug('Execution Done: api.new_session')
            log.debug('api.logged_in: {logged_in}'.format(logged_in=self.logged_in))

        settings.setBool(key="_last_login_success", value=self.logged_in)
        self._last_login_success = self.logged_in

        if self.logged_in:
            return True

        return False

    def check_vars(self):
        try:
            self._debug_mode
        except:
            self._debug_mode = settings.getBool(key='enable_debug')

        if self._debug_mode:
            log.debug('Executing: api.check_vars')

        try:
            self._cookies
        except:
            self._cookies = settings.get(key='_cookies')

        try:
            self._session_age
        except:
            self._session_age = settings.getInt(key='_session_age')

        try:
            self._last_login_success
        except:
            self._last_login_success = settings.getBool(key='_last_login_success')

        try:
            self._channels_age
        except:
            self._channels_age = settings.getInt(key='_channels_age')

        try:
            self._enable_cache
        except:
            self._enable_cache = settings.getBool(key='enable_cache')

        try:
            self._api_url
        except:
            self._api_url = settings.get(key='_api_url')

        try:
            self._devicekey
        except:
            self._devicekey = settings.get(key='_devicekey')

        try:
            self._username
        except:
            try:
                creds
            except:
                creds = get_credentials()

            self._username = creds['username']

        try:
            self._abortRequested
        except:
            self._abortRequested = False

        try:
            self._password
        except:
            try:
                creds
            except:
                creds = get_credentials()

            self._password = creds['password']

        if self._debug_mode:
            log.debug('Execution Done: api.check_vars')

    def login(self, username, password, channels=False, retry=True):
        if self._debug_mode:
            log.debug('Executing: api.login')
            log.debug('Vars: username={username}, password={password}, channels={channels}, retry={retry}'.format(username=username, password=password, channels=channels, retry=retry))

        settings.remove(key='_cookies')
        self._cookies = ''
        self._session = Session(cookies_key='_cookies')
        session_url = '{api_url}/USER/SESSIONS/'.format(api_url=self._api_url)

        if self._debug_mode:
            log.debug('Clear Setting _cookies')
            log.debug('Creating new Requests Session')
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        email_or_pin = settings.getBool(key='email_instead_of_customer')

        if email_or_pin:
            session_post_data = {
                "credentialsExtAuth": {
                    'credentials': {
                        'loginType': 'UsernamePassword',
                        'username': username,
                        'password': password,
                        'appId': 'KPN',
                    },
                    'remember': 'Y',
                    'deviceInfo': {
                        'deviceId': self._devicekey,
                        'deviceIdType': 'DEVICEID',
                        'deviceType' : 'PCTV',
                        'deviceVendor' : settings.get(key='_browser_name'),
                        'deviceModel' : settings.get(key='_browser_version'),
                        'deviceFirmVersion' : settings.get(key='_os_name'),
                        'appVersion' : settings.get(key='_os_version')
                    }
                },
            }
        else:
            session_post_data = {
                "credentialsStdAuth": {
                    'username': username,
                    'password': password,
                    'remember': 'Y',
                    'deviceRegistrationData': {
                        'deviceId': settings.get(key='_devicekey'),
                        'accountDeviceIdType': 'DEVICEID',
                        'deviceType' : 'PCTV',
                        'vendor' : settings.get(key='_browser_name'),
                        'model' : settings.get(key='_browser_version'),
                        'deviceFirmVersion' : settings.get(key='_os_name'),
                        'appVersion' : settings.get(key='_os_version')
                    }
                },
            }

        data = self.download(url=session_url, type='post', code=[200], data=session_post_data, json_data=True, data_return=True, return_json=True, retry=retry, check_data=False)

        if not data or not check_key(data, 'resultCode') or data['resultCode'] == 'KO':
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.login')

            if email_or_pin:
                gui.ok(message=_.LOGIN_ERROR2, heading=_.LOGIN_ERROR_TITLE)
            else:
                gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)

            self.clear_session()
            return False

        self._session_age = time.time()
        settings.setInt(key='_session_age', value=self._session_age)

        if self._debug_mode:
            log.debug('Settings _channels_age: {channels_age}'.format(channels_age=self._channels_age))
            log.debug('Time - 86400 seconds: {time}'.format(time=int(time.time() - 86400)))

        if channels or self._channels_age < int(time.time() - 86400):
            self.get_channels_for_user()
            self.vod_subscription()

        self._username = username
        self._password = password

        if settings.getBool(key='save_password', default=False):
            set_credentials(username=username, password=password)
        else:
            set_credentials(username=username, password='')

        self.logged_in = True

        if self._debug_mode:
            log.debug('Execution Done: api.login')

        return True

    def clear_session(self):
        if self._debug_mode:
            log.debug('Executing: api.clear_session')

        settings.remove(key='_cookies')
        self._cookies = ''

        try:
            self._session.clear_cookies()

            if self._debug_mode:
                log.debug('Execution Done: api.get_channels_for_user')

            return True
        except:
            if self._debug_mode:
                log.debug('Failure clearing session cookies')
                log.debug('Execution Done: api.get_channels_for_user')

            return False

    def get_channels_for_user(self):
        if self._debug_mode:
            log.debug('Executing: api.get_channels_for_user')

        channels_url = '{api_url}/TRAY/LIVECHANNELS?orderBy=orderId&sortOrder=asc&from=0&to=999&dfilter_channels=subscription'.format(api_url=self._api_url)
        data = self.download(url=channels_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True)

        if not data or not check_key(data['resultObj'], 'containers'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.get_channels_for_user')

            return False

        write_file(file="channels.json", data=data['resultObj']['containers'], isJSON=True)

        self.create_playlist()

        if self._debug_mode:
            log.debug('Execution Done: api.get_channels_for_user')

        return True

    def create_playlist(self):
        if self._debug_mode:
            log.debug('Executing: api.create_playlist')

        prefs = load_file(file="channel_prefs.json", isJSON=True)
        channels = load_file(file="channels.json", isJSON=True)

        playlist_all = u'#EXTM3U\n'
        playlist = u'#EXTM3U\n'

        for row in channels:
            channeldata = self.get_channel_data(row=row)
            id = unicode(channeldata['channel_id'])

            if len(id) > 0:
                path = 'plugin://{addonid}/?_=play_video&channel={channel}&id={asset}&type=channel&_l=.pvr'.format(addonid=ADDON_ID, channel=channeldata['channel_id'], asset=channeldata['asset_id'])
                playlist_all += u'#EXTINF:-1 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" group-title="TV" radio="false",{name}\n{path}\n'.format(id=channeldata['channel_id'], channel=channeldata['channel_number'], name=channeldata['label'], logo=channeldata['station_image_large'], path=path)

                if not prefs or not check_key(prefs, id) or prefs[id]['epg'] == 'true':
                    playlist += u'#EXTINF:-1 tvg-id="{id}" tvg-chno="{channel}" tvg-name="{name}" tvg-logo="{logo}" group-title="TV" radio="false",{name}\n{path}\n'.format(id=channeldata['channel_id'], channel=channeldata['channel_number'], name=channeldata['label'], logo=channeldata['station_image_large'], path=path)

        self._channels_age = time.time()
        settings.setInt(key='_channels_age', value=self._channels_age)

        if self._debug_mode:
            log.debug('Setting _channels_age to: {channels_age}'.format(channels_age=self._channels_age))
            log.debug('Writing tv.m3u8: {playlist}'.format(playlist=playlist))

        write_file(file="tv.m3u8", data=playlist, isJSON=False)
        write_file(file="tv_all.m3u8", data=playlist_all, isJSON=False)
        combine_playlist()

        if self._debug_mode:
            log.debug('Execution Done: api.create_playlist')

    def test_channels(self, tested=False, channel=None):
        if self._debug_mode:
            log.debug('Executing: api.test_channels')
            log.debug('Vars: tested={tested}, channel={channel}'.format(tested=tested, channel=channel))

        if channel:
            channel = unicode(channel)

        try:
            if not self._last_login_success or not settings.getBool(key='run_tests'):
                return 5

            settings.setBool(key='_test_running', value=True)
            channels = load_file(file="channels.json", isJSON=True)
            results = load_file(file="channel_test.json", isJSON=True)

            count = 0
            first = True
            last_tested_found = False
            test_run = False
            user_agent = settings.get(key='_user_agent')

            if not results:
                results = {}

            for row in channels:
                if count == 5 or (count == 1 and tested):
                    if test_run:
                        self.update_prefs()

                    settings.setBool(key='_test_running', value=False)
                    return count

                channeldata = self.get_channel_data(row=row)
                id = unicode(channeldata['channel_id'])

                if len(id) > 0:
                    if channel:
                        if not id == channel:
                            continue
                    elif tested and check_key(results, 'last_tested'):
                        if unicode(results['last_tested']) == id:
                            last_tested_found = True
                            continue
                        elif last_tested_found:
                            pass
                        else:
                            continue

                    if check_key(results, id) and not tested and not first:
                        continue

                    livebandwidth = 0
                    replaybandwidth = 0
                    live = 'false'
                    replay = 'false'
                    epg = 'false'
                    guide = 'false'

                    if settings.getInt(key='_last_playing') > int(time.time() - 300):
                        if test_run:
                            self.update_prefs()

                        settings.setBool(key='_test_running', value=False)
                        return 5

                    playdata = self.play_url(type='channel', channel=id, id=channeldata['asset_id'], test=True)

                    if first and not self._last_login_success:
                        if test_run:
                            self.update_prefs()

                        settings.setBool(key='_test_running', value=False)
                        return 5

                    if len(playdata['path']) > 0:
                        CDMHEADERS = CONST_BASE_HEADERS
                        CDMHEADERS['User-Agent'] = user_agent
                        playdata['path'] = playdata['path'].split("&", 1)[0]
                        self._session2 = Session(headers=CDMHEADERS)
                        resp = self._session2.get(playdata['path'])

                        if resp.status_code == 200:
                            livebandwidth = find_highest_bandwidth(xml=resp.text)
                            live = 'true'

                    if check_key(results, id) and first and not tested:
                        first = False

                        if live == 'true':
                            continue
                        else:
                            if test_run:
                                self.update_prefs()

                            settings.setBool(key='_test_running', value=False)
                            return 5

                    first = False
                    counter = 0

                    while not self._abortRequested and not xbmc.Monitor().abortRequested() and counter < 5:
                        if self._abortRequested or xbmc.Monitor().waitForAbort(1):
                            self._abortRequested = True
                            break

                        counter += 1

                        if settings.getInt(key='_last_playing') > int(time.time() - 300):
                            if test_run:
                                self.update_prefs()

                            settings.setBool(key='_test_running', value=False)
                            return 5

                    if self._abortRequested or xbmc.Monitor().abortRequested():
                        return 5

                    program_url = '{api_url}/TRAY/AVA/TRENDING/YESTERDAY?maxResults=1&filter_channelIds={channel}'.format(api_url=self._api_url, channel=channeldata['channel_id'])
                    data = self.download(url=program_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=False, check_data=True)

                    if data and check_key(data['resultObj'], 'containers') and check_key(data['resultObj']['containers'][0], 'id'):
                        if settings.getInt(key='_last_playing') > int(time.time() - 300):
                            if test_run:
                                self.update_prefs()

                            settings.setBool(key='_test_running', value=False)
                            return 5

                        playdata = self.play_url(type='program', channel=id, id=data['resultObj']['containers'][0]['id'], test=True)

                        if len(playdata['path']) > 0:
                            CDMHEADERS = CONST_BASE_HEADERS
                            CDMHEADERS['User-Agent'] = user_agent
                            playdata['path'] = playdata['path'].split("&min_bitrate", 1)[0]
                            self._session2 = Session(headers=CDMHEADERS)
                            resp = self._session2.get(playdata['path'])

                            if resp.status_code == 200:
                                replaybandwidth = find_highest_bandwidth(xml=resp.text)
                                replay = 'true'

                    if os.path.isfile(ADDON_PROFILE + id + '_replay.json'):
                        guide = 'true'

                        if live == 'true':
                            epg = 'true'

                    results[id] = {
                        'id': id,
                        'live': live,
                        'replay': replay,
                        'livebandwidth': livebandwidth,
                        'replaybandwidth': replaybandwidth,
                        'epg': epg,
                        'guide': guide,
                    }

                    results['last_tested'] = id

                    if not self._abortRequested:
                        write_file(file="channel_test.json", data=results, isJSON=True)

                    test_run = True
                    counter = 0

                    while not self._abortRequested and not xbmc.Monitor().abortRequested() and counter < 15:
                        if self._abortRequested or xbmc.Monitor().waitForAbort(1):
                            self._abortRequested = True
                            break

                        counter += 1

                        if settings.getInt(key='_last_playing') > int(time.time() - 300):
                            if test_run:
                                self.update_prefs()

                            settings.setBool(key='_test_running', value=False)
                            return 5

                    if self._abortRequested or xbmc.Monitor().abortRequested():
                        return 5

                    count += 1
        except:
            if test_run:
                self.update_prefs()

            count = 5

        settings.setBool(key='_test_running', value=False)

        if self._debug_mode:
            log.debug('Execution Done: api.test_channels')

        return count

    def update_prefs(self):
        if self._debug_mode:
            log.debug('Executing: api.update_prefs')

        prefs = load_file(file="channel_prefs.json", isJSON=True)
        results = load_file(file="channel_test.json", isJSON=True)
        channels = load_file(file="channels.json", isJSON=True)

        if not results:
            results = {}

        if not prefs:
            prefs = {}

        if not channels:
            channels = {}

        for row in channels:
            channeldata = self.get_channel_data(row=row)
            id = unicode(channeldata['channel_id'])

            if len(unicode(id)) == 0:
                continue

            keys = ['live', 'replay', 'epg']

            for key in keys:
                if not check_key(prefs, id) or not check_key(prefs[id], key):
                    if not check_key(results, id):
                        if not check_key(prefs, id):
                            prefs[id] = {
                                key: 'true',
                                key + '_choice': 'auto'
                            }
                        else:
                            prefs[id][key] = 'true'
                            prefs[id][key + '_choice'] = 'auto'
                    else:
                        result_value = results[id][key]

                        if not check_key(prefs, id):
                            prefs[id] = {
                                key: result_value,
                                key + '_choice': 'auto'
                            }
                        else:
                            prefs[id][key] = result_value
                            prefs[id][key + '_choice'] = 'auto'
                elif prefs[id][key + '_choice'] == 'auto' and check_key(results, id):
                    prefs[id][key] = results[id][key]

        write_file(file="channel_prefs.json", data=prefs, isJSON=True)

        if self._debug_mode:
            log.debug('Execution Done: api.update_prefs')

    def get_channel_data(self, row):
        if self._debug_mode:
            log.debug('Executing: api.get_channel_data')
            log.debug('Vars: row={row}'.format(row=row))

        asset_id = ''

        channeldata = {
            'channel_id': '',
            'channel_number': '',
            'description': '',
            'label': '',
            'station_image_large': '',
        }

        if not check_key(row, 'metadata') or not check_key(row['metadata'], 'channelId') or not check_key(row['metadata'], 'externalId') or not check_key(row['metadata'], 'orderId') or not check_key(row['metadata'], 'channelName'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.get_channel_data')

            return channeldata

        if check_key(row, 'assets'):
            for asset in row['assets']:
                if check_key(asset, 'videoType') and check_key(asset, 'assetId') and asset['videoType'] == 'SD_DASH_PR':
                    asset_id = asset['assetId']
                    break

        path = ADDON_PROFILE + "images" + os.sep + unicode(row['metadata']['channelId']) + ".png"

        if os.path.isfile(path):
            image = path
        else:
            image = '{images_url}/logo/{external_id}/256.png'.format(images_url=CONST_IMAGE_URL, external_id=row['metadata']['externalId'])

        channeldata = {
            'channel_id': row['metadata']['channelId'],
            'channel_number': int(row['metadata']['orderId']),
            'description': '',
            'label': row['metadata']['channelName'],
            'station_image_large': image,
            'asset_id': asset_id
        }

        if self._debug_mode:
            log.debug('Returned data: {channeldata}'.format(channeldata=channeldata))
            log.debug('Execution Done: api.get_channel_data')

        return channeldata

    def play_url(self, type, channel=None, id=None, test=False, from_beginning=False):
        if self._debug_mode:
            log.debug('Executing: api.play_url')
            log.debug('Vars: type={type}, channel={channel}, id={id}, test={test}'.format(type=type, channel=channel, id=id, test=test))

        playdata = {'path': '', 'license': '', 'token': ''}

        license = ''
        asset_id = ''
        militime = int(time.time() * 1000)
        typestr = 'PROGRAM'
        info = []
        program_id = None

        if not test:
            while not self._abortRequested and not xbmc.Monitor().abortRequested() and settings.getBool(key='_test_running'):
                settings.setInt(key='_last_playing', value=time.time())

                if self._abortRequested or xbmc.Monitor().waitForAbort(1):
                    self._abortRequested = True
                    break

            if self._abortRequested or xbmc.Monitor().abortRequested():
                return playdata

        if type == 'channel':
            if not test:
                info_url = '{api_url}/TRAY/SEARCH/LIVE?maxResults=1&filter_airingTime=now&filter_channelIds={channel}&orderBy=airingStartTime&sortOrder=desc'.format(api_url=self._api_url, channel=channel)
                data = self.download(url=info_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True)

                if not data or not check_key(data['resultObj'], 'containers'):
                    if self._debug_mode:
                        log.debug('Failure to retrieve expected data')
                        log.debug('Execution Done: api.play_url')

                    return playdata

                for row in data['resultObj']['containers']:
                    program_id = row['id']

                info = data

            play_url = '{api_url}/CONTENT/VIDEOURL/LIVE/{channel}/{id}/?deviceId={device_key}&profile=G02&time={time}'.format(api_url=self._api_url, channel=channel, id=id, device_key=self._devicekey, time=militime)
        else:
            if type == 'program':
                typestr = "PROGRAM"
            else:
                typestr = "VOD"

            program_id = id

            program_url = '{api_url}/CONTENT/USERDATA/{type}/{id}'.format(api_url=self._api_url, type=typestr, id=id)
            data = self.download(url=program_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True)

            if not data or not check_key(data['resultObj'], 'containers'):
                if self._debug_mode:
                    log.debug('Failure to retrieve expected data')
                    log.debug('Execution Done: api.play_url')

                return playdata

            for row in data['resultObj']['containers']:
                if check_key(row, 'entitlement') and check_key(row['entitlement'], 'assets'):
                    for asset in row['entitlement']['assets']:
                        if type == 'program':
                            if check_key(asset, 'videoType') and check_key(asset, 'programType') and asset['videoType'] == 'SD_DASH_PR' and asset['programType'] == 'CUTV':
                                asset_id = asset['assetId']
                                break
                        else:
                            if check_key(asset, 'videoType') and check_key(asset, 'assetType') and asset['videoType'] == 'SD_DASH_PR' and asset['assetType'] == 'MASTER':
                                if check_key(asset, 'rights') and asset['rights'] == 'buy':
                                    gui.ok(message=_.NO_STREAM_AUTH, heading=_.PLAY_ERROR)
                                    return playdata

                                asset_id = asset['assetId']
                                break

            if len(unicode(asset_id)) == 0:
                if self._debug_mode:
                    log.debug('Failure, empty asset_id')
                    log.debug('Execution Done: api.play_url')

                return playdata

            play_url = '{api_url}/CONTENT/VIDEOURL/{type}/{id}/{asset_id}/?deviceId={device_key}&profile=G02&time={time}'.format(api_url=self._api_url, type=typestr, id=id, asset_id=asset_id, device_key=self._devicekey, time=militime)

        if self._abortRequested or xbmc.Monitor().abortRequested():
            return playdata

        if program_id and not test:
            info_url = '{api_url}/CONTENT/DETAIL/{type}/{id}'.format(api_url=self._api_url, type=typestr, id=program_id)
            data = self.download(url=info_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True)

            if not data or not check_key(data['resultObj'], 'containers'):
                if self._debug_mode:
                    log.debug('Failure to retrieve expected data')
                    log.debug('Execution Done: api.play_url')

                return playdata

            info = data

        if self._abortRequested or xbmc.Monitor().waitForAbort(1):
            return playdata

        data = self.download(url=play_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True)

        if not data or not check_key(data['resultObj'], 'token') or not check_key(data['resultObj'], 'src') or not check_key(data['resultObj']['src'], 'sources') or not check_key(data['resultObj']['src']['sources'], 'src'):
            if self._debug_mode:
                log.debug('Failure, empty token or source')
                log.debug('Execution Done: api.play_url')

            return playdata

        if check_key(data['resultObj']['src']['sources'], 'contentProtection') and check_key(data['resultObj']['src']['sources']['contentProtection'], 'widevine') and check_key(data['resultObj']['src']['sources']['contentProtection']['widevine'], 'licenseAcquisitionURL'):
            license = data['resultObj']['src']['sources']['contentProtection']['widevine']['licenseAcquisitionURL']

        path = data['resultObj']['src']['sources']['src']
        token = data['resultObj']['token']

        if not test:
            real_url = "{hostscheme}://{netloc}".format(hostscheme=urlparse(path).scheme, netloc=urlparse(path).netloc)
            proxy_url = "http://127.0.0.1:{proxy_port}".format(proxy_port=settings.getInt(key='_proxyserver_port'))

            if self._debug_mode:
                log.debug('Real url: {real_url}'.format(real_url=real_url))
                log.debug('Proxy url: {proxy_url}'.format(proxy_url=proxy_url))

            settings.set(key='_stream_hostname', value=real_url)
            path = path.replace(real_url, proxy_url)

            settings.setInt(key='_drm_token_age', value=time.time())
            settings.set(key='_renew_path', value=path)
            settings.set(key='_renew_token', value=token)

        playdata = {'path': path, 'license': license, 'token': token, 'type': typestr, 'info': info}

        if self._debug_mode:
            log.debug('Returned Playdata: {playdata}'.format(playdata=playdata))
            log.debug('Execution Done: api.play_url')

        return playdata

    def vod_subscription(self):
        if self._debug_mode:
            log.debug('Executing: api.vod_subscription')

        subscription = []

        series_url = '{api_url}/TRAY/SEARCH/VOD?from=1&to=9999&filter_contentType=GROUP_OF_BUNDLES,VOD&filter_contentSubtype=SERIES,VOD&filter_contentTypeExtended=VOD&filter_excludedGenres=erotiek&filter_technicalPackages=10078,10081,10258,10255&dfilter_packages=matchSubscription&orderBy=activationDate&sortOrder=desc'.format(api_url=self._api_url)
        data = self.download(url=series_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True)

        if not data or not check_key(data['resultObj'], 'containers'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.vod_subscription')

            return False

        for row in data['resultObj']['containers']:
            subscription.append(row['metadata']['contentId'])

        write_file(file='vod_subscription.json', data=subscription, isJSON=True)

        if self._debug_mode:
            log.debug('Execution Done: api.vod_subscription')

        return True

    def vod_seasons(self, id):
        if self._debug_mode:
            log.debug('Executing: api.vod_seasons')
            log.debug('Vars: id={id}'.format(id=id))

        seasons = []

        program_url = '{api_url}/CONTENT/DETAIL/GROUP_OF_BUNDLES/{id}'.format(api_url=self._api_url, id=id)

        file = "cache" + os.sep + "vod_seasons_" + unicode(id) + ".json"

        if self._enable_cache and not is_file_older_than_x_minutes(file=ADDON_PROFILE + file, minutes=10):
            data = load_file(file=file, isJSON=True)
        else:
            data = self.download(url=program_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True)

            if data and check_key(data['resultObj'], 'containers') and self._enable_cache:
                write_file(file=file, data=data, isJSON=True)

        if not data or not check_key(data['resultObj'], 'containers'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.vod_seasons')

            return None

        for row in data['resultObj']['containers']:
            for currow in row['containers']:
                if check_key(currow, 'metadata') and check_key(currow['metadata'], 'season') and currow['metadata']['contentSubtype'] == 'SEASON':
                    seasons.append({'id': currow['metadata']['contentId'], 'seriesNumber': currow['metadata']['season'], 'desc': currow['metadata']['shortDescription'], 'image': currow['metadata']['pictureUrl']})

        if self._debug_mode:
            log.debug('Execution Done: api.vod_seasons')

        return seasons

    def vod_season(self, id):
        if self._debug_mode:
            log.debug('Executing: api.vod_season')
            log.debug('Vars: id={id}'.format(id=id))

        season = []
        episodes = []

        program_url = '{api_url}/CONTENT/DETAIL/BUNDLE/{id}'.format(api_url=self._api_url, id=id)

        file = "cache" + os.sep + "vod_season_" + unicode(id) + ".json"

        if self._enable_cache and not is_file_older_than_x_minutes(file=ADDON_PROFILE + file, minutes=10):
            data = load_file(file=file, isJSON=True)
        else:
            data = self.download(url=program_url, type='get', code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True)

            if data and check_key(data['resultObj'], 'containers') and self._enable_cache:
                write_file(file=file, data=data, isJSON=True)

        if not data or not check_key(data['resultObj'], 'containers'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.vod_season')

            return None

        for row in data['resultObj']['containers']:
            for currow in row['containers']:
                if check_key(currow, 'metadata') and check_key(currow['metadata'], 'season') and currow['metadata']['contentSubtype'] == 'EPISODE' and not currow['metadata']['episodeNumber'] in episodes:
                    asset_id = ''

                    for asset in currow['assets']:
                        if check_key(asset, 'videoType') and asset['videoType'] == 'SD_DASH_PR' and check_key(asset, 'assetType') and asset['assetType'] == 'MASTER':
                            asset_id = asset['assetId']
                            break

                    episodes.append(currow['metadata']['episodeNumber'])
                    season.append({'id': currow['metadata']['contentId'], 'assetid': asset_id, 'duration': currow['metadata']['duration'], 'title': currow['metadata']['episodeTitle'], 'episodeNumber': '{season}.{episode}'.format(season=currow['metadata']['season'], episode=currow['metadata']['episodeNumber']), 'desc': currow['metadata']['shortDescription'], 'image': currow['metadata']['pictureUrl']})

        if self._debug_mode:
            log.debug('Execution Done: api.vod_season')

        return season

    def check_data(self, resp, json=True):
        if self._debug_mode:
            log.debug('Executing: api.check_data')
            log.debug('Vars: resp={resp}, json={json}'.format(resp='Unaltered response, see above', json=json))

        if json:
            data = resp.json()

            if data and check_key(data, 'resultCode') and data['resultCode'] == 'KO':
                if self._debug_mode:
                    log.debug('Execution Done: api.check_data')

                return False

            if not data or not check_key(data, 'resultCode') or not data['resultCode'] == 'OK' or not check_key(data, 'resultObj'):
                if self._debug_mode:
                    log.debug('Execution Done: api.check_data')

                return False

        if self._debug_mode:
            log.debug('Execution Done: api.check_data')

        return True

    def download(self, url, type, code=None, data=None, json_data=True, data_return=True, return_json=True, retry=True, check_data=True, allow_redirects=True):
        if self._abortRequested or xbmc.Monitor().abortRequested():
            return None

        if self._debug_mode:
            log.debug('Executing: api.download')
            log.debug('Vars: url={url}, type={type}, code={code}, data={data}, json_data={json_data}, data_return={data_return}, return_json={return_json}, retry={retry}, check_data={check_data}, allow_redirects={allow_redirects}'.format(url=url, type=type, code=code, data=data, json_data=json_data, data_return=data_return, return_json=return_json, retry=retry, check_data=check_data, allow_redirects=allow_redirects))

        if type == "post" and data:
            if json_data:
                resp = self._session.post(url, json=data, allow_redirects=allow_redirects)
            else:
                resp = self._session.post(url, data=data, allow_redirects=allow_redirects)
        else:
            resp = getattr(self._session, type)(url, allow_redirects=allow_redirects)

        if self._debug_mode:
            log.debug('Response')
            log.debug(resp.text)
            log.debug('Response status code: {status_code}'.format(status_code=resp.status_code))

        if (code and not resp.status_code in code) or (check_data and not self.check_data(resp=resp)):
            if not retry:
                if self._debug_mode:
                    log.debug('Not retrying')
                    log.debug('Returned data: None')
                    log.debug('Execution Done: api.download')

                return None

            if self._debug_mode:
                log.debug('Trying to update login data')

            self.new_session(force=True, retry=False)

            if not self.logged_in:
                if self._debug_mode:
                    log.debug('Not logged in at retry')
                    log.debug('Returned data: None')
                    log.debug('Execution Done: api.download')

                return None

            if type == "post" and data:
                if json_data:
                    resp = self._session.post(url, json=data, allow_redirects=allow_redirects)
                else:
                    resp = self._session.post(url, data=data, allow_redirects=allow_redirects)
            else:
                resp = getattr(self._session, type)(url, allow_redirects=allow_redirects)

            if self._debug_mode:
                log.debug('Response')
                log.debug(resp.text)
                log.debug('Response status code: {status_code}'.format(status_code=resp.status_code))

            if (code and not resp.status_code in code) or (check_data and not self.check_data(resp=resp)):
                if self._debug_mode:
                    log.debug('Failure on retry')
                    log.debug('Returned data: None')
                    log.debug('Execution Done: api.download')

                return None

        if data_return:
            try:
                if return_json:
                    try:
                        returned_data = json.loads(resp.json().decode('utf-8'))
                    except:
                        returned_data = resp.json()

                    if self._debug_mode:
                        log.debug('Returned data: {data}'.format(data=returned_data))
                        log.debug('Execution Done: api.download')

                    return returned_data
                else:
                    if self._debug_mode:
                        log.debug('Returned data: Unaltered response, see above')
                        log.debug('Execution Done: api.download')

                    return resp
            except:
                pass

        if self._debug_mode:
            log.debug('Returned data: True')
            log.debug('Execution Done: api.download')

        return True