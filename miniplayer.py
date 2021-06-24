#!/usr/bin/env python3
import os
import sys
import random
import colored
import argparse
import feedparser
from configparser import ConfigParser, _UNSET


DEFAULT_CONFIG = {
    'player': 'mplayer {uri}'
}
DEFAULT_CONFIG_FILES = [
    '/etc/miniplayer.rc',
    '/usr/local/etc/miniplayer.rc',
    os.path.expanduser('~/.miniplayer.rc'),
    os.path.abspath('./miniplayer.rc')
]
PODCAST_STYLE = colored.fg('red') + colored.attr('bold')
STREAM_STYLE = colored.fg('blue') + colored.attr('bold')
_s = colored.stylize

class Logger(object):
    WARNING_STYLE = colored.fg('orange_4a')
    ERROR_STYLE = colored.fg('red')
    INFO_STYLE = colored.fg('green')

    def __init__(self, verbose=False):
        self.verbose = verbose

    def prt(self, msg):
        sys.stdout.write('{msg}\n'.format(msg=msg))

    def warning(self, msg):
        sys.stderr.write(_s("[*] {msg}\n".format(msg=msg), self.WARNING_STYLE))
        
    def error(self, msg):
        sys.stderr.write(_s("[!] {msg}\n".format(msg=msg), self.ERROR_STYLE))

    def info(self, msg):
        if self.verbose:
            sys.stdout.write(_s('[%] {msg}\n'.format(msg=msg), self.INFO_STYLE))


class ListConfigParser(ConfigParser):
    @staticmethod
    def list_conv(v):
        _v = v.strip()
        if _v.startswith('[') and _v.endswith(']'):
            _v = _v[1:-1].strip()
            return _v.split()
        else:
            raise ValueError(v)

    def peeklist(self, section, option):
        v = self.get(section, option, fallback="")
        return v.strip().startswith('[') and v.strip().endswith(']')

    def getlist(self, section, option, *, raw=False, vars=None, fallback=_UNSET, **kwargs):
        return self._get_conv(section, option, ListConfigParser.list_conv, raw=raw, vars=vars,
                              fallback=fallback, **kwargs)


def find_href(episode):
    hrefs = {}
    for link in episode['links']:
        if link.get('rel', None) == 'enclosure':
            hrefs[link.get('type', 'application/octet-stream')] = link.get('href', '')

    ret = None
    for _type in hrefs:
        if _type == 'audio/mpeg':
            ret = hrefs[_type]
            break
        elif ret is None:
            ret = hrefs[_type]

    return ret

def validate_arguments(play_type, args, logger):
    if play_type != 'podcast' and (args.list or args.filter or args.first_only):
        logger.error('-l/--list, -f/--episode-filter & -r/--first-only arguments only work '
                    'for podcasts and you\'re attempting to play a {}'.format(play_type))
        return False
    elif args.list and args.filter:
        logger.error('-l/--list and -f/--episode-filter are mutually exclusive. they make no '
                     'sense together')
        return False
    elif args.first_only and args.list:
        logger.error('-r/--first-only and -l/--list are mututally exclusive. they make no '
                     'sense together')
        return False

    return True
        

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name', metavar='NAME', help='Name of podcast or stream to play.')
    ap.add_argument('-c', '--config-file', metavar='FILENAME', required=False, default=None,
                    dest='config_file', help='Use specific config file, ignoring defaults.')
    ap.add_argument('-f', '--episode-filter', metavar='FILTER', required=False, default=None,
                    dest='filter', help='Filter for episode title (only for podcasts)')
    ap.add_argument('-l', '--list-episodes', required=False, default=False, dest='list',
                    help='List episodes (only for podcasts)', action='store_true')
    ap.add_argument('-r', '--first-only', required=False, default=False, dest='first_only',
                    help='Play only the first episode (only for podcasts)',
                    action='store_true')
    ap.add_argument('-v', '--verbose', required=False, default=False, dest='verbose',
                    help='Verbose (debug) output.', action='store_true')
    args = ap.parse_args()

    logger = Logger(args.verbose)

    config_files = DEFAULT_CONFIG_FILES
    if args.config_file:
        config_files = [args.config_file]

    logger.info("Reading from config files {}".format(', '.join(config_files)))
    cp = ListConfigParser()
    _ = cp.read(config_files)
    logger.info("Read from config files {}".format(', '.join(_)))

    config = DEFAULT_CONFIG
    config.update({key: value for key, value in cp.items('miniplayer')})
    logger.info("Base config is {}".format(str(config)))

    if args.name == '-':
        logger.info("printing all play targets")
        for section in cp.sections():
            if section == 'miniplayer': continue
            desc = cp.get(section, 'description', fallback=None)
            desc = ': {}'.format(desc) if desc else ''
            play_type = cp.get(section, 'type', fallback='stream')

            logger.prt("[{}] {}{}".format(
                    _s('P', PODCAST_STYLE) if play_type == 'podcast' else _s('S', STREAM_STYLE),
                    section, desc)
            )
    elif not cp.has_section(args.name):
        logger.error("Couldn't figure out what to play for name {name}.".format(args.name))
        sys.exit(1)
    else:
        play_type = cp.get(args.name, 'type', fallback='stream')
        if validate_arguments(play_type, args, logger):
            if play_type == 'stream':
                uris = cp.getlist(args.name, 'uri') if cp.peeklist(args.name, 'uri') else [cp.get(args.name, 'uri')]
                logger.info("Got back {} uris from configured stream {}".format(len(uris), args.name))
                chosen_uri = random.choice(uris)
                logger.info("Will play {}.".format(chosen_uri))

                command = config['player'].format(uri=chosen_uri)
                logger.info("Running {}".format(command))
                os.system(command)
            elif play_type == 'podcast':
                logger.info("Got podcast")
                feed_uri = cp.get(args.name, 'uri')
                fp = feedparser.parse(feed_uri)
                if args.list:
                    logger.info("Listing episodes for {}".format(args.name))
                    for item in fp['items']:
                        logger.prt(item['title'])
                else:
                    episodes = fp['items']
                    if args.filter:
                        logger.info("Filtering episode by {}".format(args.filter))
                        episodes = []
                        for item in fp['items']:
                            if args.filter in item['title']:
                                episodes.append(item)

                    if args.first_only:
                        logger.info("Playing only first episode in the feed.")
                        episodes = [episodes[0]] if len(episodes) > 1 else []

                    logger.info("Playing {} episodes...".format(len(episodes)))
                    for ep in episodes:
                        href = find_href(ep)
                        logger.prt("Playing {}".format(ep.get('title', href)))
                        
                        command = config['player'].format(uri=href)
                        logger.info("Running {}".format(command))
                        os.system(command)
            else:
                logger.error("Unknown play type: {} for {}".format(play_type, args.name))
                sys.exit(2)
        else:
            sys.exit(3)


if __name__ == '__main__':
    main()
