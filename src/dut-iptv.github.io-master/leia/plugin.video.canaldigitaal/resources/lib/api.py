import datetime, os, time, xbmc

from resources.lib.base import gui, settings
from resources.lib.base.constants import ADDON_ID, ADDON_PROFILE
from resources.lib.base.exceptions import Error
from resources.lib.base.log import log
from resources.lib.base.session import Session
from resources.lib.base.util import check_key, clean_filename, combine_playlist, find_highest_bandwidth, get_credentials, is_file_older_than_x_minutes, load_file, set_credentials, write_file
from resources.lib.constants import CONST_BASE_HEADERS, CONST_BASE_URL, CONST_DEFAULT_API, CONST_LOGIN_HEADERS, CONST_LOGIN_URL
from resources.lib.language import _

try:
    from urllib.parse import parse_qs, urlparse, quote
except ImportError:
    from urlparse import parse_qs, urlparse
    from urllib import quote

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
                self._session.headers = CONST_BASE_HEADERS
                self._session.headers.update({'Authorization': 'Bearer ' + self._session_token})

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
            if not force:
                if self._debug_mode:
                    log.debug('Password length = 0 and force is false')
                    log.debug('Execution Done: api.new_session')

                settings.setBool(key="_last_login_success", value=self.logged_in)
                self._last_login_success = self.logged_in

                return False

            password = gui.input(message=_.ASK_PASSWORD, hide_input=True).strip()

            if not len(password) > 0:
                if self._debug_mode:
                    log.debug('Password length = 0')
                    log.debug('Execution Done: api.new_session')

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

        try:
            self._session_token
        except:
            self._session_token = settings.get(key='_session_token')

        if self._debug_mode:
            log.debug('Execution Done: api.check_vars')

    def login(self, username, password, channels=False, retry=True):
        if self._debug_mode:
            log.debug('Executing: api.login')
            log.debug('Vars: username={username}, password={password}, channels={channels}, retry={retry}'.format(username=username, password=password, channels=channels, retry=retry))

        oauth = ''

        settings.remove(key='_cookies')
        self._cookies = ''
        settings.remove(key='_session_token')
        self._session_token = ''
        self._session = Session(cookies_key='_cookies')
        self._session.headers = CONST_BASE_HEADERS
        auth_url = '{login_url}/authenticate?redirect_uri=https%3A%2F%2Flivetv.canaldigitaal.nl%2Fauth.aspx&state={state}&response_type=code&scope=TVE&client_id=StreamGroup'.format(login_url=CONST_LOGIN_URL, state=int(time.time()))

        if self._debug_mode:
            log.debug('Clear Setting _cookies')
            log.debug('Creating new Requests Session')
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        data = self.download(url=auth_url, type="get", code=[200], data=None, json_data=False, data_return=True, return_json=False, retry=retry, check_data=False, allow_redirects=False)

        if not data:
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.login')

            gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)
            self.clear_session()
            return False

        self._session.headers = CONST_LOGIN_HEADERS
        self._session.headers.update({'Referer': auth_url})

        session_post_data = {
            "Password": password,
            "Username": username,
        }

        if self._debug_mode:
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        resp = self.download(url=CONST_LOGIN_URL, type="post", code=None, data=session_post_data, json_data=False, data_return=True, return_json=False, retry=retry, check_data=False, allow_redirects=False)

        if (resp.status_code != 302):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.login')

            gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)
            self.clear_session()
            return False

        params = parse_qs(urlparse(resp.headers['Location']).query)

        if check_key(params, 'code'):
            oauth = params['code'][0]

        if self._debug_mode:
            log.debug('Params: {params}'.format(params=params))
            log.debug('OAuth: {oauth}'.format(oauth=oauth))

        if len(oauth) == 0:
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.login')

            gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)
            self.clear_session()
            return False

        challenge_url = "{base_url}/m7be2iphone/challenge.aspx".format(base_url=CONST_BASE_URL)
        browser_name = settings.get(key='_browser_name')

        session_post_data = {
            "autotype": "nl",
            "app": "cds",
            "prettyname": browser_name,
            "model": "web",
            "serial": self._devicekey,
            "oauthcode": oauth
        }

        self._session.headers = CONST_BASE_HEADERS
        self._session.headers.update({'Content-Type': 'application/json;charset=UTF-8'})

        if self._debug_mode:
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        data = self.download(url=challenge_url, type="post", code=[200], data=session_post_data, json_data=True, data_return=True, return_json=True, retry=retry, check_data=False, allow_redirects=False)

        if not data or not check_key(data, 'id') or not check_key(data, 'secret'):
            if check_key(data, 'error') and data['error'] == 'toomany':
                gui.ok(message=_.TOO_MANY_DEVICES, heading=_.LOGIN_ERROR_TITLE)
            else:
                gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)

            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.login')

            self.clear_session()
            return False

        login_url = "{base_url}/m7be2iphone/login.aspx".format(base_url=CONST_BASE_URL)

        self._session.headers = CONST_BASE_HEADERS
        self._session.headers.update({'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})

        if self._debug_mode:
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        secret = '{id}\t{secr}'.format(id=data['id'], secr=data['secret'])

        session_post_data = {
            "secret": secret,
            "uid": self._devicekey,
            "app": "cds",
        }

        resp = self.download(url=login_url, type="post", code=None, data=session_post_data, json_data=False, data_return=True, return_json=False, retry=retry, check_data=False, allow_redirects=False)

        if (resp.status_code != 302):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.login')

            gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)
            self.clear_session()
            return False

        ssotoken_url = "{base_url}/m7be2iphone/capi.aspx?z=ssotoken".format(base_url=CONST_BASE_URL)

        self._session.headers = CONST_BASE_HEADERS

        if self._debug_mode:
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        data = self.download(url=ssotoken_url, type="get", code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=retry, check_data=False, allow_redirects=False)

        if not data or not check_key(data, 'ssotoken'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.login')

            gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)
            self.clear_session()
            return False

        session_url = "{api_url}/session".format(api_url=CONST_DEFAULT_API)

        session_post_data = {
            "sapiToken": data['ssotoken'],
            "deviceType": "PC",
            "deviceModel": browser_name,
            "osVersion": '{name} {version}'.format(name=settings.get(key='_os_name'), version=settings.get(key='_os_version')),
            "deviceSerial": self._devicekey,
            "appVersion": settings.get(key='_browser_version'),
            "brand": "cds"
        }

        self._session.headers = CONST_BASE_HEADERS
        self._session.headers.update({'Content-Type': 'application/json;charset=UTF-8'})

        if self._debug_mode:
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        data = self.download(url=session_url, type="post", code=[200], data=session_post_data, json_data=True, data_return=True, return_json=True, retry=retry, check_data=False, allow_redirects=False)

        if not data or not check_key(data, 'token'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.login')

            gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)
            self.clear_session()
            return False

        self._session_token = data['token']
        settings.set(key='_session_token', value=self._session_token)
        self._session_age = time.time()
        settings.setInt(key='_session_age', value=self._session_age)

        if self._debug_mode:
            log.debug('Session Token: {session_token}'.format(session_token=self._session_token))
            log.debug('Settings _channels_age: {channels_age}'.format(channels_age=self._channels_age))
            log.debug('Time - 86400 seconds: {time}'.format(time=int(time.time() - 86400)))

        if channels or self._channels_age < int(time.time() - 86400):
            self.get_channels_for_user()

        self._username = username
        self._password = password

        if settings.getBool(key='save_password', default=False):
            set_credentials(username=username, password=password)
        else:
            set_credentials(username=username, password='')

        self.logged_in = True
        self._session.headers = CONST_BASE_HEADERS
        self._session.headers.update({'Authorization': 'Bearer ' + self._session_token})

        if self._debug_mode:
            log.debug('Request Session Headers')
            log.debug(self._session.headers)
            log.debug('Execution Done: api.login')

        return True

    def clear_session(self):
        if self._debug_mode:
            log.debug('Executing: api.clear_session')

        settings.remove(key='_cookies')
        self._cookies = ''
        settings.remove(key='_session_token')
        self._session_token = ''

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
        self._session.headers = CONST_BASE_HEADERS
        self._session.headers.update({'Authorization': 'Bearer ' + self._session_token})

        if self._debug_mode:
            log.debug('Executing: api.get_channels_for_user')
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        channels_url = "{api_url}/assets?query=channels,3&limit=999&from=0".format(api_url=CONST_DEFAULT_API);

        data = self.download(url=channels_url, type="get", code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=False, allow_redirects=False)

        if not data or not check_key(data, 'assets'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.get_channels_for_user')

            return False

        write_file(file="channels.json", data=data['assets'], isJSON=True)

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
        channelno = 0

        for row in channels:
            channelno += 1
            channeldata = self.get_channel_data(row=row, channelno=channelno)
            id = unicode(channeldata['channel_id'])

            if len(id) > 0:
                path = 'plugin://{addonid}/?_=play_video&channel={channel}&id={id}&type=channel&_l=.pvr'.format(addonid=ADDON_ID, channel=channeldata['channel_id'], id=channeldata['channel_id'])
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

                channeldata = self.get_channel_data(row=row, channelno=1)
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

                    playdata = self.play_url(type='channel', channel=id, id=id, test=True)

                    if first and not self._last_login_success:
                        if test_run:
                            self.update_prefs()

                        settings.setBool(key='_test_running', value=False)
                        return 5

                    if len(playdata['path']) > 0:
                        CDMHEADERS = CONST_BASE_HEADERS
                        CDMHEADERS['User-Agent'] = user_agent
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

                    self._session.headers = CONST_BASE_HEADERS
                    self._session.headers.update({'Authorization': 'Bearer ' + self._session_token})
                    yesterday = datetime.datetime.now() - datetime.timedelta(1)
                    fromtime = datetime.datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S.000Z')
                    tilltime = datetime.datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:59.999Z')

                    program_url = "{api_url}/schedule?channels={id}&from={fromtime}&until={tilltime}".format(api_url=CONST_DEFAULT_API, id=id, fromtime=fromtime, tilltime=tilltime);
                    data = self.download(url=program_url, type="get", code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=False, allow_redirects=False)

                    if data and check_key(data, 'epg') and check_key(data['epg'][0], 'id'):
                        if settings.getInt(key='_last_playing') > int(time.time() - 300):
                            if test_run:
                                self.update_prefs()

                            settings.setBool(key='_test_running', value=False)
                            return 5

                        playdata = self.play_url(type='program', channel=id, id=data['epg'][0]['id'], test=True)

                        if len(playdata['path']) > 0:
                            CDMHEADERS = CONST_BASE_HEADERS
                            CDMHEADERS['User-Agent'] = user_agent
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
            channeldata = self.get_channel_data(row=row, channelno=1)
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

    def get_channel_data(self, row, channelno=0):
        if self._debug_mode:
            log.debug('Executing: api.get_channel_data')
            log.debug('Vars: row={row}, channelno={channelno}'.format(row=row, channelno=channelno))

        channeldata = {
            'channel_id': '',
            'channel_number': int(channelno),
            'description': '',
            'label': '',
            'station_image_large': '',
        }

        if not check_key(row, 'id') or not check_key(row, 'title'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.get_channel_data')

            return channeldata

        #if '18+' in row['title']:
        #    if self._debug_mode:
        #        log.debug('Skipping XXX')
        #
        #    return channeldata

        path = ADDON_PROFILE + "images" + os.sep + unicode(row['id']) + ".png"
        image = ''

        if os.path.isfile(path):
            image = path
        else:
            if check_key(row, 'images') and check_key(row['images'][0], 'url'):
                image = row['images'][0]['url']

        channeldata['channel_id'] = row['id']
        channeldata['label'] = row['title']
        channeldata['station_image_large'] = image

        if self._debug_mode:
            log.debug('Returned data: {channeldata}'.format(channeldata=channeldata))
            log.debug('Execution Done: api.get_channel_data')

        return channeldata

    def play_url(self, type, channel=None, id=None, test=False, from_beginning='False'):
        self._session.headers = CONST_BASE_HEADERS
        self._session.headers.update({'Authorization': 'Bearer ' + self._session_token})

        if self._debug_mode:
            log.debug('Executing: api.play_url')
            log.debug('Vars: type={type}, channel={channel}, id={id}, test={test}'.format(type=type, channel=channel, id=id, test=test))
            log.debug('Request Session Headers')
            log.debug(self._session.headers)

        playdata = {'path': '', 'license': None, 'info': None}

        if not type or not len(unicode(type)) > 0:
            if self._debug_mode:
                log.debug('Failure executing api.play_url, no type set')
                log.debug('Execution Done: api.play_url')

            return playdata

        if not test:
            while not self._abortRequested and not xbmc.Monitor().abortRequested() and settings.getBool(key='_test_running'):
                settings.setInt(key='_last_playing', value=time.time())

                if self._abortRequested or xbmc.Monitor().waitForAbort(1):
                    self._abortRequested = True
                    break

            if self._abortRequested or xbmc.Monitor().abortRequested():
                return playdata

        if type == 'channel':
            info_url = '{api_url}/assets/{channel}'.format(api_url=CONST_DEFAULT_API, channel=channel)
        else:
            info_url = '{api_url}/assets/{id}'.format(api_url=CONST_DEFAULT_API, id=id)

        play_url = info_url + '/play'

        if not test:
            data = self.download(url=info_url, type="get", code=[200], data=None, json_data=False, data_return=True, return_json=True, retry=True, check_data=True, allow_redirects=True)

            if not data or not check_key(data, 'id'):
                if self._debug_mode:
                    log.debug('Failure to retrieve expected data')
                    log.debug('Execution Done: api.play_url')

                return playdata

            session_post_data = {
                "player": {
                    "name":"Bitmovin",
                    "version":"8.22.0",
                    "capabilities": {
                        "mediaTypes": ["DASH","HLS","MSSS","Unspecified"],
                        "drmSystems": ["Widevine"],
                    },
                    "drmSystems": ["Widevine"],
                },
            }

            if type == 'channel' and check_key(data, 'params') and check_key(data['params'], 'now') and check_key(data['params']['now'], 'id'):
                play_url2 = '{api_url}/assets/{id}/play'.format(api_url=CONST_DEFAULT_API, id=data['params']['now']['id'])
                info = data['params']['now']

                data = self.download(url=play_url2, type="post", code=[200], data=session_post_data, json_data=True, data_return=True, return_json=True, retry=True, check_data=True, allow_redirects=True)

                if data and check_key(data, 'url'):
                    if not settings.getBool(key='ask_start_from_beginning') or not gui.yes_no(message=_.START_FROM_BEGINNING, heading=info['title']):
                        data = self.download(url=play_url, type="post", code=[200], data=session_post_data, json_data=True, data_return=True, return_json=True, retry=True, check_data=True, allow_redirects=True)
                else:
                    data = self.download(url=play_url, type="post", code=[200], data=session_post_data, json_data=True, data_return=True, return_json=True, retry=True, check_data=True, allow_redirects=True)
            else:
                info = data
                data = self.download(url=play_url, type="post", code=[200], data=session_post_data, json_data=True, data_return=True, return_json=True, retry=True, check_data=True, allow_redirects=True)
        else:
            if self._abortRequested or xbmc.Monitor().abortRequested():
                return playdata

            data = self.download(url=play_url, type="post", code=[200], data=session_post_data, json_data=True, data_return=True, return_json=True, retry=True, check_data=True, allow_redirects=True)

        if not data or not check_key(data, 'url'):
            if self._debug_mode:
                log.debug('Failure to retrieve expected data')
                log.debug('Execution Done: api.play_url')

            return playdata

        if check_key(data, 'drm') and check_key(data['drm'], 'licenseUrl'):
            license = data['drm']['licenseUrl']

        path = data['url']

        if not test:
            real_url = "{hostscheme}://{netloc}".format(hostscheme=urlparse(path).scheme, netloc=urlparse(path).netloc)
            proxy_url = "http://127.0.0.1:{proxy_port}".format(proxy_port=settings.getInt(key='_proxyserver_port'))

            if self._debug_mode:
                log.debug('Real url: {real_url}'.format(real_url=real_url))
                log.debug('Proxy url: {proxy_url}'.format(proxy_url=proxy_url))

            settings.set(key='_stream_hostname', value=real_url)
            path = path.replace(real_url, proxy_url)

        playdata = {'path': path, 'license': license, 'info': info}

        if self._debug_mode:
            log.debug('Returned Playdata: {playdata}'.format(playdata=playdata))
            log.debug('Execution Done: api.play_url')

        return playdata

    def vod_seasons(self, id):
        if self._debug_mode:
            log.debug('Executing: api.vod_seasons')
            log.debug('Vars: id={id}'.format(id=id))

        seasons = []

        if self._debug_mode:
            log.debug('Execution Done: api.vod_seasons')

        return seasons

    def vod_season(self, id):
        if self._debug_mode:
            log.debug('Executing: api.vod_seasons')
            log.debug('Vars: id={id}'.format(id=id))

        season = []
        episodes = []

        if self._debug_mode:
            log.debug('Execution Done: api.vod_season')

        return season

    def check_data(self, resp, json=False):
        if self._debug_mode:
            log.debug('Executing: api.check_data')
            log.debug('Vars: resp={resp}, json={json}'.format(resp='Unaltered response, see above', json=json))

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