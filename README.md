# Donkey

This project is a web based MP3 server and player for Raspberry Pi.

It uses [`pymad`](https://github.com/jaqx0r/pymad) and [`pyalsaaudio`](https://github.com/larsimmisch/pyalsaaudio) to provide MP3 playback via RPi PCM audio device. Web server is based on [Tornado](https://github.com/tornadoweb/tornado) framework and SQLite database. System monitoring is provided by [`psutil`](https://pythonhosted.org/psutil/). Uploaded MP3 file processing is carried out by [LAME](http://lame.sourceforge.net/).

The code was written in a couple of days as a tiny office music player with web based support and uploading functionality. After more than a year of active testing with around 1000 songs in the playlist it still works well.

Donkey is available under the MIT license. The included LICENSE file describes this in detail.
