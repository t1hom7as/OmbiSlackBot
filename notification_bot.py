#SlackClient documentation: https://pypi.org/project/slackclient/
from slackclient import SlackClient #pip install slackclient
import requests
import re
import os
import time
import urllib3

#Disables the insecure warning from the ombi request
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Edit the two variables below with your OMBI and SLACK BOT Keys
OMBI_API = 'PUT YOUR KEY HERE'
SLACK_BOT_TOKEN = 'PUT YOUR KEY HERE'
#Edit the path of your OMBI URL or IP // ex: http://my_ombi.com or 192.168.1.10:8000
OMBI_PATH = 'PUT YOUR PATH HERE'

slack_client = SlackClient(SLACK_BOT_TOKEN)
notificationbot_id = None

RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
REQUEST_SEARCH = 'Hello! The user'

def deny_move_request(id, response_reason):

    headers = {
    'accept': 'application/json',
    'ApiKey': OMBI_API,
    'Content-Type': 'application/json-patch+json',
    }

    data = '{ "reason": "' + response_reason + '", "id": ' + id + '}'
    
    try:
        response = requests.put(OMBI_PATH + '/api/v1/Request/movie/deny', headers=headers, data=data, verify=False)
    except Exception as e:
        print("Error denying movie requests. Failed response: " + e)
        result = False
        error_msg = "Failed to connect to API"
        return result, error_msg

    try:
        result = response.json()['result']
        error_msg = response.json()['errorMessage']

        return result, error_msg
    except Exception as e:
        print("Error denying movie requests in function: " + e)
        result = False
        error_msg = "Try *{}*.".format(EXAMPLE_COMMAND)
        return result, error_msg
        

def approve_move_request(id):

    headers = {
    'accept': 'application/json',
    'ApiKey': OMBI_API,
    'Content-Type': 'application/json-patch+json',
    }

    data = '{ "id": ' + id + '}'

    try:
        response = requests.post(OMBI_PATH + '/api/v1/Request/movie/approve', headers=headers, data=data, verify=False)
    except Exception as e:
        print("Error approveing movie requests. Failed response: " + e)
        result = False
        error_msg = "Failed to connect to API"
        return result, error_msg

    try:
        result = response.json()['result']
        error_msg = response.json()['errorMessage']

        return result, error_msg
    except Exception as e:
        print("Error approving movie requests in function: " + e)
        result = False
        error_msg = "Try *{}*.".format(EXAMPLE_COMMAND)
        return result, error_msg


def approve_tv_request(id):

    headers = {
    'accept': 'application/json',
    'ApiKey': OMBI_API,
    'Content-Type': 'application/json-patch+json',
    }

    data = '{ "id": ' + id + '}'

    try:
        response = requests.post(OMBI_PATH + '/api/v1/Request/tv/approve', headers=headers, data=data, verify=False)
    except Exception as e:
        print("Error approving tv requests. Failed response: " + e)
        result = False
        error_msg = "Failed to connect to API"
        return result, error_msg

    try:
        result = response.json()['result']
        error_msg = response.json()['errorMessage']

        return result, error_msg
    except Exception as e:
        print("Error approving tv requests in function: " + e)
        result = False
        error_msg = "Try *{}*.".format(EXAMPLE_COMMAND)
        return result, error_msg


def deny_tv_request(id, response_reason):

    headers = {
    'accept': 'application/json',
    'ApiKey': OMBI_API,
    'Content-Type': 'application/json-patch+json',
    }
    
    data = '{ "reason": "' + response_reason + '", "id": ' + id + '}'

    try:
        response = requests.put(OMBI_PATH + '/api/v1/Request/tv/deny', headers=headers, data=data, verify=False)
    except Exception as e:
        print("Error denying tv requests. Failed response: " + e)
        result = False
        error_msg = "Failed to connect to API"
        return result, error_msg

    try:
        result = response.json()['result']
        error_msg = response.json()['errorMessage']

        return result, error_msg
    except Exception as e:
        print("Error denying tv requests in function: " + e)
        result = False
        error_msg = "Try *{}*.".format(EXAMPLE_COMMAND)
        return result, error_msg

def get_unapproved_movie_requests():

    needs_approval = []

    headers = {
    'accept': 'application/json',
    'ApiKey': OMBI_API,
    }

    try:
        response = requests.get(OMBI_PATH + '/api/v1/Request/movie', headers=headers, verify=False)
    except Exception as e:
        print("Error getting movie requests. Failed response: " + e)
        result = False
        error_msg = "Failed to connect to API"
        return result, error_msg

    try:
        for r in response.json():

            if r['canApprove'] is True:
                if r['denied'] is not True:

                    requestid = r['id']
                    user = r['requestedUser']['userAlias']
                    request_title = r['title']

                    request = str(requestid) + ' - ' + str(user) + ' - ' + str(request_title)

                    needs_approval.append(request)
                else:
                    continue
            else:
                continue

        return needs_approval

    except Exception as e:
        print("Error getting movie requests in function: " + e)
        result = False
        error_msg = "Try *{}*.".format(EXAMPLE_COMMAND)
        return result, error_msg
   

def get_unapproved_tv_requests():

    needs_approval = []

    headers = {
    'accept': 'application/json',
    'ApiKey': OMBI_API,
    }

    try:
        response = requests.get(OMBI_PATH + '/api/v1/Request/tv', headers=headers, verify=False)
    except Exception as e:
        print("Error getting tv requests. Failed response: " + e)
        result = False
        error_msg = "Failed to connect to API"
        return result, error_msg

    try:
        for r in response.json():
            if r['childRequests'][0]['canApprove'] is True:
                if r['childRequests'][0]['denied'] is not True:

                    requestid = r['childRequests'][0]['id']
                    user = r['childRequests'][0]['requestedUser']['userAlias']
                    request_title = r['childRequests'][0]['title']

                    request = str(requestid) + ' - ' + str(user) + ' - ' + str(request_title)

                    needs_approval.append(request)
                else:
                    continue
            else:
                continue
    except Exception as e:
        print("Error getting tv requests in function: " + e)
        result = False
        error_msg = "Try *{}*.".format(EXAMPLE_COMMAND)
        return result, error_msg
    
    return needs_approval


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    try:
        for event in slack_events:
            if event['type'] == 'message':
                if event['type'] != 'subtype':
                    user_id, message = parse_direct_mention(event["text"])
                    if user_id == notificationbot_id:
                        return message, event["channel"]
                    elif user_id == 'request_found':
                        if message == 'movie':
                            return 'get movie requests', event["channel"]
                        elif message == 'tv':
                            return 'get tv requests', event["channel"]
    except Exception as e:
        print("Error parsing bot commands: " + e)
        return None, None

    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None

        If you have OMBI request notifications enabled to send to SLACK if there is no direct 
        mention it will look for the default ombi request notification, if found it will
        automatically return the ID of the request
    """
    #searches for direct mention in the message using the "MENTION_REGEX" variable at the top
    matches = re.search(MENTION_REGEX, message_text)
    #searches for the start of the default request message "Hello! The user" in the message using the "REQUEST_SEARCH" variable at the top
    requested = re.search(REQUEST_SEARCH, message_text)
    try:
        #if a direct mention is found, it will return the mention ID & Message
        if matches:
            return (matches.group(1), matches.group(2).strip())

        #if direct mention isn't found, it will look for a new request
        elif requested:
            movie = re.search('Movie', message_text)
            tv = re.search('Tv show', message_text)
            if movie:
                return ('request_found', 'movie')
            elif tv:
                return ('request_found', 'tv')    
        else:
            return (None, None)
    except Exception as e:
        print("Error parsing direct mention: " + e)
        return (None, None)
    
    return (None, None)


def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = "Commands:\napprove movie [id]\ndeny movie [id] [reason]\napprove tv [id]\ndeny tv [id] [reason]\nget movie requests\nget tv requests"
    elif 'approve movie' in command:
        request_id = re.sub(r"\D", "", command)
        
        try:
            result, error_msg = approve_move_request(request_id)

            if result is True:
                response = 'Movie has been approved successfully!'
            else:
                response = 'Failed to approve Movie. Error: ' + str(error_msg)

        except Exception as e:
            print("Error approving Movie: " + e)
            response = "Try *{}*.".format(EXAMPLE_COMMAND)
    

    elif 'deny movie' in command:
        request_id = re.sub(r"\D", "", command).encode('utf-8')
        deny_reason = re.sub(r'.*?\d ', "", command).encode('utf-8')
        
        try:
            result, error_msg = deny_move_request(request_id, deny_reason)

            if result is True:
                response = 'Movie has been denied successfully..'
            else:
                response = 'Failed to deny Movie. Error: ' + str(error_msg)
        except Exception as e:
            print("Error denying Movie: " + e)
            response = "Try *{}*.".format(EXAMPLE_COMMAND)

    elif 'deny tv' in command:
        request_id = re.sub(r"\D", "", command).encode('utf-8')
        deny_reason = re.sub(r'.*?\d ', "", command).encode('utf-8')
        
        try:
            result, error_msg = deny_tv_request(request_id, deny_reason)

            if result is True:
                response = 'TV request has been denied successfully..'
            else:
                response = 'Failed to deny TV request. Error: ' + str(error_msg)
        except Exception as e:
            print("Error denying TV: " + e)
            response = "Try *{}*.".format(EXAMPLE_COMMAND)

    elif 'approve tv' in command:
        request_id = re.sub(r"\D", "", command)
        
        try:
            result, error_msg = approve_tv_request(request_id)

            if result is True:
                response = 'TV Show has been approved successfully!'
            else:
                response = 'Failed to approve TV Show. Error: ' + str(error_msg)

        except Exception as e:
            print("Error approving TV: " + e)
            response = "Try *{}*.".format(EXAMPLE_COMMAND)

    elif 'get movie requests' in command:

        try:
            unapprved_request = get_unapproved_movie_requests()

            if unapprved_request != []:
                unapprved_request = str(unapprved_request).replace("', '", "\n")
                unapprved_request = str(unapprved_request).replace("['", "")
                unapprved_request = str(unapprved_request).replace("']", "")
                response = 'Unapproved Movie Requests:\n' + str(unapprved_request)
            else:
                response = 'There are no Movie requests that need to be approved!'

        except Exception as e:
            print("Error getting Movie requests: " + e)
            response = "Try *{}*.".format(EXAMPLE_COMMAND)

    elif 'get tv requests' in command:

        try:
            unapprved_request = get_unapproved_tv_requests()

            if unapprved_request != []:
                unapprved_request = str(unapprved_request).replace("', '", "\n")
                unapprved_request = str(unapprved_request).replace("['", "")
                unapprved_request = str(unapprved_request).replace("']", "")
                response = 'Unapproved TV Requests:\n' + str(unapprved_request)
            else:
                response = 'There are no TV requests that need to be approved!'

        except Exception as e:
            print("Error getting TV requests: " + e)
            response = "Try *{}*.".format(EXAMPLE_COMMAND)

    try:
        # Sends the response back to the channel
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )
    except Exception as e:
        print("Error sending response to the channel: " + e)


if __name__ == "__main__":
    try:
        if slack_client.rtm_connect(with_team_state=False):
            print("Starter Bot connected and running!")
            # Read bot's user ID by calling Web API method `auth.test`
            notificationbot_id = slack_client.api_call("auth.test")["user_id"]
            while True:
                command, channel = parse_bot_commands(slack_client.rtm_read())
                if command:
                    print('Command Found: ' + command)
                    handle_command(command, channel)
                time.sleep(RTM_READ_DELAY)
        else:
            print("Connection failed. Exception traceback printed above.")
    except Exception as e:
        print('There was a failure: ' + e)
        pass