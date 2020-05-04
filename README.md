# IPTV Manager
This Service Add-on allows supported IPTV Add-ons to integrates their Live TV and Radio Channels in the Kodi PVR. 
IPTV Manager will periodically poll those Add-ons for Channels and EPG data, and generate a new `m3u` playlist and
`xmltv` file that the Kodi PVR Addon [IPTV Simple](https://github.com/kodi-pvr/pvr.iptvsimple) can use.

We got inspiration from the [IPTV Merge](https://www.matthuisman.nz/2019/02/iptv-merge-kodi-add-on.html) addon from 
Matt Huisman, but decided to do things a bit differently. With this integration, the Add-ons don't have to generate an
`m3u` file or `xmltv` file themselves but can provide us structured JSON data. 

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

| Setting             | Required | Description                | Example                                                  |
|---------------------|----------|----------------------------|----------------------------------------------------------|
| `iptv.enabled`      | Yes      | Opt-in on polling.         | `true`                                                   |
| `iptv.channels_uri` | Yes      | Endpoint for Channel data. | `plugin://plugin.video.example/iptv/channels?port=$PORT` |
| `iptv.epg_uri`      | No       | Endpoint for EPG data.     | `plugin://plugin.video.example/iptv/epg?port=$PORT`      |

There are two possible method to provide the data for channels and EPG in `iptv.channels_uri` and `iptv.epg_uri`:
* A `plugin://` endpoint

  This is the preferred method if you want to generate the list of channels automatically. IPTV Manager will
  periodically call the Add-on to request the data.

  > **Current implementation:**
  >
  > Due to limitations of Kodi, an Add-on can't just return data on an `RunPlugin()` or `RunScript()` call, 
  > so it needs another way to send the data back to IPTV Manager. Therefore, IPTV Manager temporary binds to free port
  > on `localhost`, and passes this port as the placeholder `$PORT` to the configured endpoint.
  > 
  > IPTV Manager will wait for a while for the Add-on to call us back on the socket. If we don't get a connection back,
  > we will consider the request to have failed and this indicates that something went wrong in the Add-on. 
  >
  > Since querying for EPG data could take a while, it's recommended for an Add-on to open the callback connection as soon
  > as possible, so IPTV Manager doesn't timeout. Once the connection is opened, the Add-on can generate the EPG data and
  > reply in a format documented below by sending the data trough the socket connection.
  >
  > When an exception occurs, the Add-on doesn't send any data and simply closes the socket again. IPTV Manager will see
  > this and knows that something went wrong and can continue with its work. 
  >
  > Example: 
  > 
  > * The endpoint `plugin://plugin.video.example/iptv/epg?port=$PORT` will be called as 
  > `plugin://plugin.video.example/iptv/epg?port=38464`
  > * The Add-on `plugin.video.example` does the routing for this call, and opens a socket connection to `localhost:38464`
  >   as soon as possible.
  > * It will then query it's backend for EPG data for a few days. This might take a few seconds or more.
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
This is a normal `m3u` playlist as documented by IPTV Simple [here](https://github.com/kodi-pvr/pvr.iptvsimple/blob/Matrix/README.md#m3u-format-elements).

#### JSON
This is a `json` format to more easily define your channels without having to create a `m3u` playlist.

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
| `group`    | No       | A group for the channel. This is probably the network or Add-on name.                         |
| `logo`     | No       | A logo for the channel. This can be an URL or a local file relative to the Add-on root.       |
| `radio`    | No       | Indicates if this channel is a Radio channel. (default `false`)                               |

### EPG data
IPTV Manager will periodically use the `iptv.epg_uri` endpoint to update the EPG of the channels. 
The key must match the `id` of the channel from the Channel JSON. 

> In case the constructing of this file takes a long time, it might be beneficial to create this in a background service
> and cache the results. This cached result can then be passed when IPTV Manager asks for an update. 

#### XMLTV
This is a normal `xmltv` file as documented by IPTV Simple [here](https://github.com/kodi-pvr/pvr.iptvsimple/blob/Matrix/README.md#xmltv-format-elemnents).

#### JSON
This is a `json` format to more easily define your channels without having to create a `xmltv` file.

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

### Reply decorator

The following decorator can be used to send a dict back to IPTV Manager.

```python
import socket
import json

# ...

@staticmethod
def reply(host, port):
    """ Send the output of the wrapped function to socket. """

    def decorator(func):
        """ Decorator """

        def inner(*arg, **kwargs):
            """ Execute function """
            # Open connection so the remote end knows we are doing something
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            try:
                # Execute function
                result = func(*arg, **kwargs)

                # Send result
                sock.send(json.dumps(result))
            finally:
                # Close our connection
                sock.close()

        return inner

    return decorator
```

It can be used like this:
```python
routing = routing.Plugin()  # pylint: disable=invalid-name

# ...

@routing.route('/iptv/channels')
def iptv_channels():
    """ Generate channel data for the Kodi PVR integration """
    from resources.lib.modules.iptvmanager import IptvManager

    @IptvManager.reply('127.0.0.1', int(routing.args['port'][0]))
    def generate():
        """ Channel generator """
        return IptvManager(kodi).get_channels()

    generate()

```