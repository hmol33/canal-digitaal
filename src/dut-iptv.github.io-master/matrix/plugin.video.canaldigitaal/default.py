import sys

from resources.lib.plugin import plugin

if __name__ == '__main__':
    plugin.dispatch(sys.argv[2])