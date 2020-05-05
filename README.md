# IPTV Manager
This Service Add-on allows supported IPTV Add-ons to integrates their Live TV and Radio Channels in the Kodi PVR.
IPTV Manager will periodically poll those Add-ons for Channels and EPG data, and generate a new M3U playlist and
XMLTV file that the Kodi PVR Addon [IPTV Simple](https://github.com/kodi-pvr/pvr.iptvsimple) can use.

We got inspiration from the [IPTV Merge](https://www.matthuisman.nz/2019/02/iptv-merge-kodi-add-on.html) addon from
Matt Huisman, but decided to do things a bit differently. With this integration, the Add-ons do not have to generate
an M3U file or XMLTV file themselves but can provide us structured JSON data.

> **Note:** IPTV Manager is still under development, and things might still change. The goal is to create an Add-on that
> can be included in the Kodi Add-on Repository, so we need to find a way that works best.

Supported Add-ons:
* [VTM GO (plugin.video.vtm.go)](https://github.com/add-ons/plugin.video.vtm.go/)
* [VRT NU (plugin.video.vrt.nu)](https://github.com/add-ons/plugin.video.vrt.nu/)
* [VRT Radio (plugin.audio.vrt.radio)](https://github.com/add-ons/plugin.audio.vrt.radio/)
* [Regio TV (plugin.video.regiotv)](https://github.com/add-ons/plugin.video.regiotv/)

## Integration
To make an IPTV Add-on compatible with IPTV Manager, the Add-on needs a few things to add so IPTV Manager can detect it
and poll it for channels and EPG data.

The following settings needs to be added. We can pick these up so we know how to communicate with the Add-on.

| Setting             | Required | Description                | Example                                       |
|---------------------|----------|----------------------------|-----------------------------------------------|
| `iptv.enabled`      | Yes      | Opt-in on polling.         | `true`                                        |
| `iptv.channels_uri` | Yes      | Endpoint for Channel data. | `plugin://plugin.video.example/iptv/channels` |
| `iptv.epg_uri`      | No       | Endpoint for EPG data.     | `plugin://plugin.video.example/iptv/epg`      |

There are two possible method to provide the data for channels and EPG in `iptv.channels_uri` and `iptv.epg_uri`:
* A `plugin://` endpoint

  This is the preferred method if you want to generate the list of channels automatically. IPTV Manager will
  periodically call the Add-on to request the data.

  > **Current implementation:**
  >
  > Due to limitations of Kodi, an Add-on cannot just return data on an `RunPlugin()` or `RunScript()` call,
  > so it needs another way to send the data back to IPTV Manager. Therefore, IPTV Manager temporary binds to free port
  > on `localhost`, and passes this port to the configured endpoint.
  >
  > IPTV Manager will wait for a while for the Add-on to call us back on the socket. If we do not get a connection back,
  > we will consider the request to have failed and this indicates that something went wrong in the Add-on.
  >
  > Since querying for EPG data could take a while, it is recommended for an Add-on to open the callback connection as soon
  > as possible, so IPTV Manager does not timeout. Once the connection is opened, the Add-on can generate the EPG data and
  > reply in a format documented below by sending the data trough the socket connection.
  >
  > When an exception occurs, the Add-on does not send any data and simply closes the socket again. IPTV Manager will see
  > this and knows that something went wrong and can continue with its work.
  >
  > Example:
  >
  > * The endpoint `plugin://plugin.video.example/iptv/epg` will be called as
  > `plugin://plugin.video.example/iptv/epg?port=38464`
  > * The Add-on `plugin.video.example` does the routing for this call, and opens a socket connection to `localhost:38464`
  >   as soon as possible.
  > * It will then query its backend for EPG data for a few days. This might take a few seconds or more.
  > * It generates the json required and sends it trough the socket connection.
  > * It closes the socket connection.
  >
  > Example code can be found at the bottom of this file.

* A web endpoint

  You can also point to an online URL that contains the data.

### Channel data
IPTV Manager will periodically use the `iptv.channels_uri` endpoint to know about the channels that the addon provides.

Two formats are supported, and they are auto-detected.

#### M3U
This is a normal M3U playlist as documented by IPTV Simple [here](https://github.com/kodi-pvr/pvr.iptvsimple/blob/Matrix/README.md#m3u-format-elements).

#### JSON-M3U
This is a JSON format to more easily define your channels without having to create a M3U playlist.
It is documented at: https://github.com/add-ons/service.iptv.manager/wiki/JSON-M3U-format

```json
{
  "version": 1,
  "streams": [
    {
      "id": "channel-one.be",
      "name": "Channel One",
      "group": "Belgium TV",
      "logo": "resources/logos/channel-one.png",
      "stream": "plugin://plugin.video.example/stream/channel-one"
    },
    {
      "id": "channel-two.be",
      "name": "Channel Two",
      "group": "Belgium TV",
      "logo": "https://www.example.com/logos/channel-two.png",
      "stream": "https://www.example.com/steams/channel-two.m3u8"
    },
    {
      "id": "radio-one.be",
      "name": "Radio One",
      "group": "Belgium Radio",
      "logo": "resources/logos/radio-one.png",
      "stream": "plugin://plugin.video.example/stream/radio-one",
      "radio": true
    }
  ]
}
```

| Attribute  | Required | Description                                                                                   |
|------------|----------|-----------------------------------------------------------------------------------------------|
| `id`       | Yes      | An unique identifier for the channel. This will be used to link with the EPG data.            |
| `name`     | Yes      | The name of the channel.                                                                      |
| `stream`   | Yes      | The endpoint for the Live stream. This can be an online HLS stream or a `plugin://` endpoint. |
| `preset`   | No       | A preferred channel number.                                                                   |
| `group`    | No       | A group for the channel (usually the network or add-on name). *This defaults to Add-on name.* |
| `logo`     | No       | A logo for the channel (a URL or local file). *This defaults to the Add-on icon.*             |
| `radio`    | No       | Indicates if this channel is a Radio channel. *This defaults to `false`.*                     |

### EPG data
IPTV Manager will periodically use the `iptv.epg_uri` endpoint to update the EPG of the channels.
The key must match the `id` of the channel from the Channel JSON.

> In case the constructing of this file takes a long time, it might be beneficial to create this in a background service
> and cache the results. This cached result can then be passed when IPTV Manager asks for an update.

#### XMLTV
This is a normal XMLTV file as documented by IPTV Simple [here](https://github.com/kodi-pvr/pvr.iptvsimple/blob/Matrix/README.md#xmltv-format-elemnents).

#### JSONTV
This is a JSON format to more easily define your channels without having to create an XMLTV file.
It is documented at: https://github.com/add-ons/service.iptv.manager/wiki/JSONTV-format

```json
{
  "version": 1,
  "epg": {
    "channel-one.be": [
      {
        "start": "2020-04-01T12:45:00",
        "stop": "2020-04-01T12:50:00",
        "title": "My Show",
        "description": "Description of My Show",
        "subtitle": "Episode name for My Show",
        "episode": "S01E05",
        "image": "https://www.example.com/shows/my-show/s01e05.png",
        "date": "2018-04-01"
      },
      {},
      {},
      {}
    ],
    "channel-two.be": [
      {},
      {},
      {}
    ]
  }
}
```

| Attribute     | Required | Description                                                    |
|---------------|----------|----------------------------------------------------------------|
| `start`       | Yes      | The start time of the program in `YYYY-MM-DDTHH:MM:SS` format. |
| `stop`        | Yes      | The end time of the program in `YYYY-MM-DDTHH:MM:SS` format.   |
| `title`       | Yes      | The title of the program.                                      |
| `description` | No       | The description of the program.                                |
| `subtitle`    | No       | The subtitle of the program. This can be the Episode name.     |
| `episode`     | No       | The episode number in case of a show in the `S01E01` format.   |
| `image`       | No       | A URL to an image for this program.                            |
| `date`        | No       | The original air date for this program.                        |


## Example code
An add-on wanting to implement IPTV Manager support can use the below example to extend.

```python
# -*- coding: utf-8 -*-
""" Kodi PVR Integration module """

from __future__ import absolute_import, division, unicode_literals

import json
import socket

from resources.lib.data import CHANNELS


class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port

    def via_socket(func):
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.send(json.dumps(func(self)))
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels():
        """Return JSON-M3U formatted information to IPTV Manager"""
        channels = []
        for entry in CHANNELS:
            channels.append(dict(
                id=foo.get('id'),
                name=foo.get('label'),
                logo=foo.get('logo'),
                stream=foo.get('url'),
            ))
        return dict(version=1, streams=channels)

    @via_socket
    def send_epg():
        """Return JSONTV formatted information to IPTV Manager"""
        from tvguide import TVGuide
        epg_data = TVGuide().get_epg_data()
        return dict(version=1, epg=epg_data)
```

It can be used like this:
```python
import routing
routing = routing.Plugin()

@plugin.route('/iptv/channels')
def iptv_channels():
    """Return JSON-M3U formatted data for all live channels"""
    from iptvmanager import IPTVManager
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_channels()


@plugin.route('/iptv/epg')
def iptv_epg():
    """Return JSONTV formatted data for all live channel EPG data"""
    from iptvmanager import IPTVManager
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_epg()
```
