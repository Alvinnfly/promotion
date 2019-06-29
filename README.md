# promotion
A homemade flexget plugin to detect torrents' promotion status, only support NexusPHP based private trackers.
# usage
- download promotion.py to dist-packages/flexget/plugins/filter
- add the following to your configuration file
```
promotion: 
  action: accept
  cookie: * your cookie here *
  promotion: free/twoupfree/halfdown/twouphalfdown/thirtypercent/none
```
- run flexget
# warning
only tested for the following sites: HDChina TJUPT NYPT Ourbits BYRBT MTeam
*theoratically* works for all sites based on NexusPHP, but if it met some sites such as HDChina which changed its frontend, it would crush. 
# to-do list
detect Ourbits's h&r status
add crush handler
