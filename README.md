# mini-player
Small python mplayer proxy for easily playing streams &amp; podcasts on the command line.

I have a small Leovo x131e Chromebook that I put Debian on and I use as a shop computer. It's
basically trash, no battery, very little processing power, it just serves to show me PDFs of
wiring diagrams and play some audio while I work without complaining too much about being
full of steel wool shavings, spray paint and dust. It works beautifully for this, and this 
small Python script just makes it slightly easier to play music or podcasts. Configure your
favorite podcasts and radio streams in the `miniplayer.rc` file, then just refer to them
by name with `python miniplayer.py <whatever>`. Personally, I configure it aliased as `play`
so I can `play bootliquor` and get a stream.

## Usage
```
usage: miniplayer.py [-h] [-c FILENAME] [-f FILTER] [-l] [-v] NAME

positional arguments:
  NAME                  Name of podcast or stream to play.

optional arguments:
  -h, --help            show this help message and exit
  -c FILENAME, --config-file FILENAME
                        Use specific config file, ignoring defaults.
  -f FILTER, --episode-filter FILTER
                        Filter for episode title (only for podcasts)
  -l, --list-episodes   List episodes (only for podcasts)
  -v, --verbose         Verbose (debug) output.
```

Most things are self-explanatory, but the two podcast options may bear some explanation.

`-l/--list-episodes` will just list the titles of the episodes in a given podcast feed. It's
designed specificially to be used before `-f/--episode-filter`.

`-f/--episode-filter` will filter the _titles_ of episodes and only play episodes that contain
the passed filter. Normally we just play all episodes starting from the newest (first in the
feed). This is designed to allow you to only play a given episode. It's not a regex, it's not
complex, it's literally:

```
if episode_title contains <<my filter>>:
  add to play list
```


## Configuration
Default miniplayer.rc files are:
```
/etc/miniplayer.rc
/usr/local/etc/miniplayer.rc
~/.miniplayer.rc
./miniplayer.rc
```

There's an example in `miniplayer.rc-example`. The overall configuration (currently only
the `player` option) should be in the `miniplayer` section. `player` should be a command
with a placeholder for the URI to play that can be passed to Python's `os.system`. For podcasts
where multiple episodes will be played, it just runs `os.system` in a loop. Multiple files
will not be played in a single command.

```
[miniplayer]
player = mplayer -quiet "{uri}"
```

### Source configuration - Radio Stream
```
[n5md]
type = stream
uri = [
        http://ice4.somafm.com/n5md-128-aac
        http://ice6.somafm.com/n5md-128-aac
        http://ice2.somafm.com/n5md-128-aac
        http://ice1.somafm.com/n5md-128-aac
    ]
```

The *section* title should be the `name` as referenced in usage above. `type` should be `stream`,
and uri should either be a single stream URI (it will be passed directly to your configured 
`player` above, so whatever your player can handle is a valid URI) or a list of URIs separated 
by newlines, prefixed with `[` and suffixed with `]`. If multiple URIs, the script will pass 
them to `random.choice` to pick one at random.

### Source configuration - Podcast
```
[tal]
type = podcast
uri = http://feed.thisamericanlife.org/talpodcast
```

Just as simple as stream, type should be `podcast` and uri should point to *only* a single
feed URI. It will be parsed by `feedparser`.
