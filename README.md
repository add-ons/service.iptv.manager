# IPTV Manager
This Service Add-on integrates Live TV and Radio Channels from supported Add-ons in the Kodi PVR. 
It will periodically poll those IPTV Add-ons for Channels and EPG data.

The principle is based on the [IPTV Merge](https://www.matthuisman.nz/2019/02/iptv-merge-kodi-add-on.html) addon from 
Matt Huisman, but with this integration, the Add-ons don't have to generate an `m3u` file or `xmltv` file themselves, 
but can work with structured JSON data. 

Supported Add-ons:
* [VTM GO (plugin.video.vtm.go)](https://github.com/add-ons/plugin.video.vtm.go/)

## Integration
To make an IPTV Add-on compatible with IPTV Manager, a few things needs to be done.

### IPTV JSON
Place the following file as `iptv.json` in the root of the Add-on. This allows IPTV Manager to detect the Add-on and 
know the endpoints for the Channel and EPG data.

```json
{
    "version": 1,
    "channels": "plugin://plugin.video.example/iptv/channels?output=$FILE",
    "channels_format": "json",
    "epg": "plugin://plugin.video.example/iptv/epg?output=$FILE",
    "epg_format": "xmltv"
}
```

| Attribute         | Required | Description                                                          |
|-------------------|----------|----------------------------------------------------------------------|
| `version`         | Yes      | Always `1`.                                                          |
| `channels`        | Yes      | Endpoint for Channel data.                                           |
| `channels_format` | Yes      | Format for Channel data, can be `json` or `m3u` (default is `json`). |
| `epg`             | No       | Endpoint for EPG data.                                               |
| `epg_format`      | No       | Format for EPG data, can be `json` or `xmltv` (default is `json`).   |

There are two possible method to provide the data for channels and EPG:
* A local file (example: `iptv.channels.json`)
  This is the preferred method if the list of channels are statically defined. The file path is relative to the root of
  the Add-on.
  
  There is not really a use-case to use this for `epg` data, since that's by nature dynamic data.

* A dynamic endpoint (example: `plugin://plugin.video.example/iptv/channels?output=$FILE`)
  This is the preferred method if you want to generate the list of channels automatically.
  
  IPTV Manager will make a call to this endpoint, provide a temporary file in `$FILE`, and wait until that file contains
  the result.  In case of an error, the Add-on should remove the `$FILE`, so IPTV Manager can continue. 

  > Due to limitations of Kodi, an Add-on can't just return data, so it needs to write the data to a temporary file that 
  > is passed as the `$FILE` parameter.
 
* A web endpoint (example: `https://www.example.com/channels.json`)
  You can also point to an online URL that contains the data.

### Channel data

IPTV Manager will periodically use the `channels` endpoint defined in the `iptv.json` file to know about the channels
that the addon provides.

The format of this channel data will be based on the `channels_format` parameter.

#### M3U (`channels_format` parameter is `m3u`)

This is a normal `m3u` playlist as documented by IPTV Simple [here](https://github.com/kodi-pvr/pvr.iptvsimple/blob/Matrix/README.md#m3u-format-elements).

#### JSON (`channels_format` parameter is `json`)

```json
[
  {
    "id": "channel-one.be",
    "name": "Channel One",
    "logo": "resources/logos/channel-one.png",
    "stream": "plugin://plugin.video.example/stream/channel-one"
  },
  {
    "id": "channel-two.be",
    "name": "Channel Two",
    "logo": "https://www.example.com/logos/channel-two.png",
    "stream": "https://www.example.com/steams/channel-two.m3u8"
  },
  {
    "id": "radio-one.be",
    "name": "Radio One",
    "logo": "resources/logos/radio-one.png",
    "stream": "plugin://plugin.video.example/stream/radio-one",
    "radio": true
  }
]
```

| Attribute  | Required | Description                                                                                   |
|------------|----------|-----------------------------------------------------------------------------------------------|
| `id`       | Yes      | An unique identifier for the channel. This will be used to link with the EPG data.            |
| `name`     | Yes      | The name of the channel.                                                                      |
| `logo`     | Yes      | A logo for the channel. This can be an URL or a local file relative to the Add-on root.       |
| `stream`   | Yes      | The endpoint for the Live stream. This can be an online HLS stream or a `plugin://` endpoint. |
| `radio`    | No       | Indicates if this channel is a Radio channel. (default `false`)                               |

### EPG data

IPTV Manager will periodically use the `epg` endpoint defined in the `iptv.json` file to update the EPG of the channels. 
The key must match the `id` of the channel from the Channel JSON. 

> In case the constructing of this file takes a long time, it might be beneficial to create this in a background service
> and cache the results. This cached result can then be passed when IPTV Manager asks for an update. 

#### XMLTV (`epg_format` parameter is `xmltv`)

This is a normal `xmltv` file as documented by IPTV Simple [here](https://github.com/kodi-pvr/pvr.iptvsimple/blob/Matrix/README.md#xmltv-format-elemnents).

#### JSON (`epg_format` parameter is `json`)

```json
{
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
    {...}
  ],
  "channel-two.be": [
    {...}
  ]
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
