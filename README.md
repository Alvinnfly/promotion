# promotion
A homemade flexget plugin to detect torrents' promotion status, only support private trackers based on NexusPHP.

# usage
- install flexget
- download promotion.py to `dist-packages/flexget/plugins/filter`
- add `other_fields: [link]` to rss plugin
- add the following to your configuration file
```
promotion: 
  action: accept
  cookie: * your cookie here *
  username: * your username here *
  promotion: free/twoupfree/halfdown/twouphalfdown/thirtypercent/none
```
- run flexget

# a config.yml demo 
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
# *h&r detection for certain sites*
by adding `not_hr: yes` to configuration file, it would accept only not in h&r mode torrents.

remember this config is not available for other sites!

# updates
- 2019-06-30 add ourbits's h&r detection 
- 2019-07-15 add ttg's h&r detection 
# warning
only tested for the following sites: <del>HDChina</del> TJUPT HDSky NYPT NPUPT SSD Ourbits BYRBT MTeam TTG

h&r detect available for: Ourbits TTG

*theoratically* works for all sites based on NexusPHP, but if it met some sites such as HDChina or NPUBits which changed NexuxPHP's original frontend, it would crush :)

so, use this plugin **at your own risk!** 

# to-do list
- add crush handler
- make promotion field an array
