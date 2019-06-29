# promotion
A homemade flexget plugin to detect torrents' promotion status, only support private trackers based on NexusPHP.
# usage
- download promotion.py to dist-packages/flexget/plugins/filter
- add `other_fields: [link]` to rss plugin
- add the following to your configuration file
```
promotion: 
  action: accept
  cookie: * your cookie here *
  promotion: free/twoupfree/halfdown/twouphalfdown/thirtypercent/none
```
- run flexget
# a demo config.yml
executing the following configuration file would add free torrents in rss link to transmission
```
templates:
  anchors:
    _transmission: &transmission
      host: 127.0.0.1
      port: 9091
      username: ***
      password: ***

tasks:
  ***: 
    rss: 
      url: ***
      other_fields: [link]
    promotion: 
      promotion: free
      action: accept
      username: ***
      cookie: ***
    transmission:
      <<: *transmission
      action: add 
```
# warning
only tested for the following sites: HDChina TJUPT NYPT Ourbits BYRBT MTeam

*theoratically* works for all sites based on NexusPHP, but if it met some sites such as HDChina which changed its frontend, it would crush. 

so, use this plugin ** at your own risks! ** 

# to-do list
- detect Ourbits's h&r status
- add crush handler
