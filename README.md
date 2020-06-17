# OmbiSlackBot

Forked from [wymangr](https://github.com/wymangr/OMBI_SlackBot) 

Using a modified [pyombi](https://github.com/larssont/pyombi)

Slack Bot to interact with Ombi, written in python.

This uses the Slack RTM API, and requires a `classic slack bot`.

Requires `python 3.7` or above.
User should set env vars:
```
export SLACK_TOKEN="<slack_token>
export OMBI_API_KEY="<ombi_api_key>"
export OMBI_URL="<ip_or_fqdn>"
```

Requirements:
``` 
$ pip install slackclient>=2.7.0
$ pip install requests 
$ pip install requests_cache
```
Thanks to **wymangr** & **larssont**.
