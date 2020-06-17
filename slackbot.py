#!/usr/bin/env python
import os
import re
from textwrap import dedent

import requests
import requests_cache
from slack import RTMClient, WebClient
from slack.errors import SlackApiError

import ombi_functions

SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
OMBI_API_KEY = os.environ.get("OMBI_API_KEY")
OMBI_URL = os.environ.get("OMBI_URL")


def slack_message(web_client, channel_id, text, color="#3AA3E3"):
    try:
        response = web_client.chat_postMessage(
            channel=channel_id,
            attachments=[{
                "text": text,
                "fallback": "Unable to show data",
                "callback_id": "message_id",
                "color": color,
                "attachment_type": "default",
            }],
        )
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]
        print(f"Got an error: {e.response['error']}")


def plain_slack_message(web_client, channel_id, text, color="#3AA3E3"):
    try:
        response = web_client.chat_postMessage(
            channel=channel_id,
            text=text)
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]
        print(f"Got an error: {e.response['error']}")


# Maybe for future use
def slack_message_with_button(web_client, channel_id, text, color="#3AA3E3", button_text='', url=''):
    try:
        response = web_client.chat_postMessage(
            channel=channel_id,
            attachments=[{
                "text": text,
                "fallback": "Unable to show data",
                "callback_id": "message_id",
                "color": color,
                "attachment_type": "default",
                "actions": [{
                    "name": "reviewit",
                    "text": button_text,
                    "style": "primary",
                    "type": "button",
                    "value": "review",
                    "url": url
                }],
            }],
        )
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]
        print(f"Got an error: {e.response['error']}")


def get_movies(ombi, web_client, channel_id):
    movies = []
    request_string = None
    try:
        requests = ombi.get_movie_requests()
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    for x in requests:
        if not x['approved'] and not x['denied']:
            movies.append({x['title']: x['requestedUser']['userName']})
    if movies:
        request_string = '- {}'.format('\n- '.join(['{} (by {})'.format(k, v) for x in movies for k, v in x.items()]))
    if request_string:
        slack_message(web_client, channel_id, f"*New movie requests:* \n```{request_string}```")
    else:
        slack_message(web_client, channel_id, f"No requests found", color='danger')


def all_requests(ombi, web_client, channel_id):
    movies = []
    tv = []
    movie_string = None
    tv_string = None
    try:
        movie_requests = ombi.get_movie_requests()
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    try:
        tv_requests = ombi.get_tv_requests()
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    for x in movie_requests:
        if not x['approved'] and not x['denied']:
            movies.append({x['title']: x['requestedUser']['userName']})
    not_approved_tv = [y for x in tv_requests for y in x['childRequests'] if not y['approved'] and not y['denied']]
    for x in not_approved_tv:
        tv.append({x['title']: [x['requestedUser']['userName'], x['seasonRequests'][0]['seasonNumber'], x['seasonRequests'][0]['episodes'][0]['episodeNumber']]})
    if movies:
        movie_string = '- {}'.format('\n- '.join(['{} (by {})'.format(k, v) for x in movies for k, v in x.items()]))
    if tv:
        tv_string = '- {}'.format('\n- '.join(['{} (Season: {} Episode: {} by {})'.format(k, v[1], v[2], v[0]) for x in tv for k, v in x.items()]))
    if movies or tv:
        data_list = []
        if movies:
            data_list.append(movie_string)
        if tv:
            data_list.append(tv_string)
        if data_list:
            strings = '{}'.format('\n'.join(['{}'.format(x) for x in data_list]))
            slack_message(web_client, channel_id, f"*New requests:* \n```{strings}```")
        else:
            slack_message(web_client, channel_id, f"No requests found", color='danger')
    else:
        slack_message(web_client, channel_id, f"No requests found", color='danger')


def get_tv(ombi, web_client, channel_id):
    tv = []
    request_string = None
    try:
        requests = ombi.get_tv_requests()
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    not_approved = [y for x in requests for y in x['childRequests'] if not y['approved'] and not y['denied']]
    for x in not_approved:
        tv.append({x['title']: [x['requestedUser']['userName'], x['seasonRequests'][0]['seasonNumber'], x['seasonRequests'][0]['episodes'][0]['episodeNumber']]})
    if tv:
        request_string = '- {}'.format('\n- '.join(['{} (Season: {} Episode: {} by {})'.format(k, v[1], v[2], v[0]) for x in tv for k, v in x.items()]))
    if request_string:
        slack_message(web_client, channel_id, f"*New TV requests:* \n```{request_string}```")
    else:
        slack_message(web_client, channel_id, f"No requests found", color='danger')


def approve(ombi, web_client, channel_id, user, text):
    try:
        movie_requests = ombi.get_movie_requests()
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    try:
        tv_requests = ombi.get_tv_requests()
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    movie_check = [x for x in movie_requests if x['title'].lower() == text[8:].lower() and '!approve' in text.lower()]
    tv_regex = None
    tv_regex = r"^!approve\s(\D+)\sseason"
    tv_regex = re.match(tv_regex, text)
    if tv_regex:
        tv_regex = tv_regex.group(1)
        tv_check = [x for x in tv_requests if x['title'].lower() == tv_regex]
    else:
        tv_check = None
    if movie_check:
        try:
            ombi.approve_movie_request(movie_check[0]['id'])
            slack_message(web_client, channel_id, f"{user} has approved *{movie_check[0]['title']}*", color='#36a64f')
        except ombi_functions.OmbiError as ex:
            slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    elif tv_check:
        match = r"^!approve\s\D+season\D+(\d+)\s\w+\s(\d+)"
        result = re.match(match, text)
        season = result.group(1)
        season = int(season)
        episode = result.group(2)
        episode = int(episode)
        get_data = [y['seasonRequests'] for x in tv_check for y in x['childRequests'] if y['approved'] is False]
        title = [z['title'] for z in tv_requests if z['title'].lower() in text.lower()]
        found = [x for x in get_data for y in x if season == y['seasonNumber'] and episode == y['episodes'][0]['episodeNumber']]
        if found:
            try:
                ombi.approve_tv_request(found[0][0]['childRequestId'])
                slack_message(web_client, channel_id, f"{user} has approved *{title[0]}* (Season {season} Episode {episode})", color='#36a64f')
            except ombi_functions.OmbiError as ex:
                slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    else:
        slack_message(web_client, channel_id, f"*{text[8:]}* not found", color='danger')


def deny(ombi, web_client, channel_id, user, text, reason="Not now"):
    try:
        movie_requests = ombi.get_movie_requests()
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    try:
        tv_requests = ombi.get_tv_requests()
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    movie_check = [x for x in movie_requests
                   if (x['title'].lower() == text[6:].lower()
                   or x['title'].lower() == text[8:].lower())
                   and ('!deny' in text.lower()
                   or '!reject' in text.lower())]
    tv_regex = None
    tv_regex_1 = r"^!deny\s(\D+)\sseason"
    tv_regex_2 = r"^!reject\s(\D+)\sseason"
    tv_regex_1 = re.match(tv_regex_1, text)
    tv_regex_2 = re.match(tv_regex_2, text)
    if tv_regex_1:
        tv_regex = tv_regex_1.group(1)
    elif tv_regex_2:
        tv_regex = tv_regex_2.group(1)
    else:
        pass
    if tv_regex:
        tv_check = [x for x in tv_requests if x['title'].lower() == tv_regex]
    else:
        tv_check = None
    if movie_check:
        try:
            ombi.deny_movie_request(movie_check[0]['id'], reason)
            slack_message(web_client, channel_id, f"{user} has denied *{movie_check[0]['title']}*", color='danger')
        except ombi_functions.OmbiError as ex:
            slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    elif tv_check:
        match1 = r"^!deny\s\D+season\D+(\d+)\s\w+\s(\d+)"
        match2 = r"^!reject\s\D+season\D+(\d+)\s\w+\s(\d+)"
        match1 = re.match(match1, text)
        match2 = re.match(match2, text)
        if match1:
            season = match1.group(1)
            season = int(season)
            episode = match1.group(2)
            episode = int(episode)
        elif match2:
            season = match2.group(1)
            season = int(season)
            episode = match2.group(2)
            episode = int(episode)
        else:
            if '!deny' in text:
                slack_message(web_client, channel_id, f"*{text[5:].title()}* not found", color='danger')
            elif '!reject' in text:
                slack_message(web_client, channel_id, f"*{text[7:].title()}* not found", color='danger')
            return None
        get_data = [y['seasonRequests'] for x in tv_check for y in x['childRequests'] if y['approved'] is False]
        title = [z['title'] for z in tv_requests if z['title'].lower() in text.lower()]
        found = [x for x in get_data for y in x if season == y['seasonNumber'] and episode == y['episodes'][0]['episodeNumber']]
        if found:
            try:
                ombi.deny_tv_request(found[0][0]['childRequestId'])
                slack_message(web_client, channel_id, f"{user} has denied *{title[0]}* (Season {season} Episode {episode})", color='danger')
            except ombi_functions.OmbiError as ex:
                slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
        elif '!deny' in text:
            slack_message(web_client, channel_id, f"*{text[5:].title()}* not found", color='danger')
        elif '!reject' in text:
            slack_message(web_client, channel_id, f"*{text[7:].title()}* not found", color='danger')
    elif '!deny' in text.lower():
        slack_message(web_client, channel_id, f"*{text[5:].title()}* not found", color='danger')
    elif '!reject' in text.lower():
        slack_message(web_client, channel_id, f"*{text[7:].title()}* not found", color='danger')


def search_movie(ombi, web_client, channel_id, user, text, search=True):
    data = text[14:]
    data = data.strip()
    movie_string = None
    try:
        movie_search = ombi.search_movie(data)
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    movie_title = {}
    for x in movie_search:
        movie_title[x['title']] = x['theMovieDbId']
    if search:
        slack_message(web_client, channel_id, f"{user} searched for {data}")
        if movie_title:
            movie_string = '- {}'.format('\n- '.join(['{} ({})'.format(k, v) for k, v in movie_title.items()]))
        if movie_string:
            slack_message(web_client, channel_id, f'```{str(movie_string)}```')
        else:
            slack_message(web_client, channel_id, f'*{data}* not found', color='danger')
    else:
        movie_data = {k: v for k, v in movie_title.items() if k.lower() == data.lower()}
        return movie_data


def search_tv(ombi, web_client, channel_id, user, text):
    data = text[11:]
    tv_string = None
    try:
        tv_search = ombi.search_tv(data)
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
    slack_message(web_client, channel_id, f"{user} searched for {data}")
    tv_title = {}
    for x in tv_search:
        tv_title[x['title']] = x['id']
    if tv_title:
        tv_string = '- {}'.format('\n- '.join(['{} ({})'.format(k, v) for k, v in tv_title.items()]))
    if tv_string:
        slack_message(web_client, channel_id, f'```{str(tv_string)}```')
    else:
        slack_message(web_client, channel_id, f'*{data}* not found', color='danger')


def request_movie(ombi, web_client, channel_id, user, text):
    search = search_movie(ombi=ombi, web_client=web_client, channel_id=channel_id, user=user, text=text, search=False)
    match = r"^!request\smovie\s(.+)"
    match = re.match(match, text)
    if match:
        match = match.group(1)
    else:
        print('No match found')
        slack_message(web_client, channel_id, f"*{text}* not found", color='danger')
    data = [v for k, v in search.items() if k.lower() == match.lower()]
    try:
        ombi.request_movie(data[0])
        slack_message(web_client, channel_id, f"{user} requested {match.title()}")
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')


def request_tv(ombi, web_client, channel_id, user, text):
    tv_data = get_tv_data(web_client, channel_id)
    match = r"^!request\s+tv\s+(\D+)\sseason\s+(\d+)\s+episode\s+(\d+)"
    match = re.match(match, text)
    if match:
        title = match.group(1)
        season = match.group(2)
        episode = match.group(3)
    else:
        slack_message(web_client, channel_id, f'*{text}* not found', color='danger')
        return None
    tv_id = [v for k, v in tv_data.items() if title.lower() == k.lower()]
    try:
        ombi.request_tv(tv_id[0], season, episode)
        slack_message(web_client, channel_id, f"{user} requested {title.title()} Season {season} Episode {episode}")
    except ombi_functions.OmbiError as ex:
        slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')


def get_tv_data(web_client, channel_id):
    url = "http://api.tvmaze.com/shows?page={}"
    tv_data = {}
    tv_cache = False
    for x in range(0, 300):
        req = requests.get(url.format(x))
        if x == 0 and req.from_cache is False:
            tv_cache = True
            slack_message(web_client, channel_id, 'Caching all TV shows...', color='warning')
        if req.status_code != 200:
            break
        req = req.json()
        for y in req:
            tv_data[y['name'].lower()] = y['externals']['thetvdb']
    if tv_cache:
        slack_message(web_client, channel_id, 'TV Cache complete', color='#36a64f')
    return tv_data


def clear_tv_cache(web_client, channel_id):
    try:
        clear = requests_cache.clear()
        slack_message(web_client, channel_id, 'TV cache cleared', color='#36a64f')
    except AttributeError:
        slack_message(web_client, channel_id, 'TV cache not found', color='danger')
        print("TV cache not found")


def install_cache(web_client, channel_id):
    try:
        install = requests_cache.install_cache('tv.db', expire_after=86400)
    except AttributeError:
        slack_message(web_client, channel_id, 'TV cache not found', color='danger')
        print("TV cache not found")


def display_help(web_client, channel_id):
    help_string = dedent("""\
        *Command help:*
        > *Show all tv and movie requests:*
        > `!get all requests`
        > *Show all tv requests:*
        > `!get tv requests`
        > *Show all movie requests:*
        > `!get movie requests`
        > *Search a tv show:*
        > `!search tv <search_string>`
        > *Search a movie:*
        > `!search movie <search_string>`
        > *Request a tv show:*
        > `!request tv <tv_id>`
        > Request a movie:*
        > `!request movie <movie_id>`
        >  *Approve a tv show:*
        > `!approve <tv_show> season <season_number> episode <episode_number>`
        > *Approve a movie:*
        > `!approve <movie>`
        > *Deny a tv show:*
        > `!deny <tv_show> season <season_number> episode <episode_number>`
        > *Deny a movie:*
        > `!deny <movie>`
        > *Reject a tv show:*
        > `!reject <tv_show> season <season_number> episode <episode_number>`
        > *Reject a movie:*
        > `!reject <movie>`
        > *Displays all valid commands:*
        > `!help`
        """)
    plain_slack_message(web_client, channel_id, help_string)


@RTMClient.run_on(event='message')
def pull_data(**payload):
    run = False
    while True:
        try:
            try:
                ombi = ombi_functions.Ombi(api_key=OMBI_API_KEY, host=OMBI_URL)
            except ombi_functions.OmbiError as ex:
                slack_message(web_client, channel_id, f"*Error:*\n```{ex}```", color='danger')
            web_client = payload['web_client']
            rtm_client = payload['rtm_client']
            data = payload['data']
            channel_id = data['channel']
            # To allow to tag the slack username
            user = f"<@{data.get('user')}>"
            text = data.get('text').lower()
            if '!get all requests' in text:
                all_requests(ombi, web_client, channel_id)
            elif "!get movie requests" in text:
                get_movies(ombi, web_client, channel_id)
            elif '!get tv requests' in text:
                get_tv(ombi, web_client, channel_id)
            elif '!approve' in text:
                approve(ombi, web_client, channel_id, user, text)
            elif '!deny' in text or '!reject' in text:
                deny(ombi, web_client, channel_id, user, text)
            elif '!search movie' in text:
                search_movie(ombi, web_client, channel_id, user, text)
            elif '!search tv' in text:
                search_tv(ombi, web_client, channel_id, user, text)
            elif '!request movie' in text:
                request_movie(ombi, web_client, channel_id, user, text)
            elif '!request tv' in text:
                request_tv(ombi, web_client, channel_id, user, text)
            elif '!install tv cache' in text:
                install_tv_cache(web_client, channel_id)
            elif '!cache tv' in text:
                get_tv_data(web_client, channel_id)
            elif '!clear tv cache' in text:
                clear_tv_cache(web_client, channel_id)
            elif '!help' in text:
                display_help(web_client, channel_id)
            elif '!' in text:
                slack_message(web_client, channel_id, f"*{text}* is not a valid command\nUse `!help` to show options", color='danger')
            break
        except AttributeError:
            if run:
                print("TV cache not found\nInstalling...")
                slack_message(web_client, channel_id, 'TV cache not found\nInstalling...', color='warning')
                raise
            install_cache(web_client, channel_id)
            run = True


rtm_client = RTMClient(token=SLACK_TOKEN)
rtm_client.start()
