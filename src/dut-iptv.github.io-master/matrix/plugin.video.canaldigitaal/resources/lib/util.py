from resources.lib.base import settings, uaparser

def update_os_browser():
    user_agent = settings.get(key='_user_agent')
    settings.set(key='_browser_name', value=uaparser.detect(user_agent)['browser']['name'])
    settings.set(key='_browser_version', value=uaparser.detect(user_agent)['browser']['version'])
    settings.set(key='_os_name', value=uaparser.detect(user_agent)['os']['name'])
    settings.set(key='_os_version', value=uaparser.detect(user_agent)['os']['version'])

def update_settings():
    pass