import feedparser
import getpass
import json
import requests
import sys
from bs4 import BeautifulSoup
import configparser
from datetime import datetime, timezone
from pprint import pprint
from html import unescape
import re
import inspect

# Constants
BLUESKY_API_ENDPOINT = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
BLUESKY_POSTER_CONFIG = "/home/" + getpass.getuser() + "/.config/bluesky-poster/config.ini"
DID_URL = "https://bsky.social/xrpc/com.atproto.identity.resolveHandle"
API_KEY_URL = "https://bsky.social/xrpc/com.atproto.server.createSession"

def rw_config():
    return False

def get_did(handle):
    did_resolve = requests.get(DID_URL + f"?handle={handle}")
    response = json.loads(did_resolve.content)["did"]
    return response


def get_api_key(did, app_password):
    # Data to be sent to the server
    post_data = {
        "identifier": did,  # The user's DID
        "password": app_password  # The app password generated earlier
    }

    headers = {
        "Content-Type": "application/json"  # Specifies the format of the data being sent
    }

    # Send a POST request with the required data to obtain the API key
    api_key_response = requests.post(API_KEY_URL, headers=headers, json=post_data)

    # Parse the response to extract the API key
    return json.loads(api_key_response.content)["accessJwt"]


def get_rss_content(feeduri):

    postdata = {}
    feedout = feedparser.parse(feeduri)
    postdata['title'] = unescape(feedout.entries[0].title.strip())
    postdata['description'] = feedout.entries[0].description
    postdata['link'] = feedout.entries[0].link
    postdata['guid'] = feedout.entries[0].guid

    # remove html tags
    post_content = re.sub('<[^<]+?>', '', postdata['description'].strip())

    # replace multiple line-breaks with a single line-break
    post_content = re.sub(r'\n+', '\n', post_content)

    # remove unwanted line from flickr feeds
    post_content = re.sub(r'grange85 posted a photo:\n', '', post_content)

    # add title
    postdata['content'] = f"{postdata['title'].strip()}\n{post_content}"
    postdata['hashtags'] = get_hashtags(postdata['content'])
    postdata['uri'] = get_url(postdata['content'])

    return postdata

def get_hashtags(description):
    hashtags = re.findall(r'#[A-Za-z][-\'A-Za-z0-9]*',description)
    print(hashtags)
    hashtags = ([s.strip('#') for s in hashtags])
    hashreturn = {}
    for tag in hashtags:
        startByte = description.encode().find(("#" + tag).encode())
        endByte = startByte + len(tag.encode())+1
        hashreturn[tag] = [startByte,endByte]
    if not hashtags:
        return_value = False
    else:
        return hashreturn

def get_url(description):
    if description.find("https://") > 0:
        uri = re.search(r'https:[^( |$)]*', description)
        startByte = description.encode().find(("https://").encode())
        endByte = description.encode().find((" ").encode(), startByte)
        if endByte == -1:
            endByte = len(description.encode())
        urireturn = {uri.group(): [startByte, endByte]}
        return urireturn
    else:
        return False

def main():
    rssdata = get_rss_content(r'dummy-feed.xml')
    print(rssdata)
if __name__ == '__main__':
    sys.exit(main())  
