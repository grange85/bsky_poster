import feedparser
import getpass
import json
import requests
import sys
from bs4 import BeautifulSoup
import configparser
from datetime import datetime, timezone
import re
import inspect
# from pathlib import Path

# Constants
BLUESKY_API_ENDPOINT = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
BLUESKY_POSTER_CONFIG = "/home/" + getpass.getuser() + "/.config/bluesky-poster/config.ini"
DID_URL = "https://bsky.social/xrpc/com.atproto.identity.resolveHandle"
API_KEY_URL = "https://bsky.social/xrpc/com.atproto.server.createSession"  # The endpoint to request the API key

def get_did(handle):
    did_resolve = requests.get(DID_URL + f"?handle={handle}")
    response = json.loads(did_resolve.content)["did"]
    return response

def get_hashtags(description):
    hashtags = re.findall(r'#[-A-Za-z0-9]*',description)
    hashtags = ([s.strip('#') for s in hashtags])
    if not hashtags:
        return_value = False
    else:
        facets = []
        for tag in hashtags:
            indexes = (re.search(tag, description))
            facets.append({
                "index": {
                    "byteStart": indexes.span()[0]-1,
                    "byteEnd": indexes.span()[1],
                    },
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#tag",
                        "tag": tag,
                    }
                ],
                })
        return_value = facets

    return return_value


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

def get_rss_content(postdata):

    # Parse the RSS feed
    feedout = feedparser.parse(postdata['feeduri'])

    # If you plan to post the latest content, it's usually the first entry in the feed
    postdata['title'] = feedout.entries[0].title
    postdata['description'] = feedout.entries[0].description
    postdata['link'] = feedout.entries[0].link
    postdata['guid'] = feedout.entries[0].guid

    if postdata['guid'] == postdata['lastpost']:
        return False
    else:
        config = configparser.ConfigParser()
        config.read(BLUESKY_POSTER_CONFIG)
        with open(BLUESKY_POSTER_CONFIG, 'w') as configfile:
            config[postdata['feed']]['lastpost'] = postdata['guid']
            config.write(configfile)
    return postdata

def prepare_post_for_bluesky(postdata):
    """Convert the RSS content into a format suitable for Bluesky."""
    hashtags = get_hashtags(f"{postdata['title']}\n{postdata['description']}")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # The post's body text
    post_text = f"{postdata['title']}\n{postdata['description']}"
    # The post structure for Bluesky
    post_structure = {
        "$type": "app.bsky.feed.post",
        "text": post_text,
        "createdAt": now
            }
    post_structure["facets"] = hashtags
    post_structure["embed"] = postdata['embed_card']
    return post_structure

def publish_on_bluesky(post_structure, did, key):
    """Publish the structured post on Bluesky."""

    # The complete record for the Bluesky post, including our structured content
    post_record = {
        "collection": "app.bsky.feed.post",
        "repo": did,    # The unique DID of our account
        "record": post_structure
    }

    post_request = requests.post(
            BLUESKY_API_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            },
            data=json.dumps(post_record),
        )
    response = json.loads(post_request.content)
    return response


def get_embed_url_card(key, url):

    # the required fields for every embed card
    card = {
        "uri": url,
        "title": "",
        "description": "",
    }

    # fetch the HTML
    headers = {
            "User-Agent": "Grange85Bot/0.0 (https://en.wikipedia.org/wiki/User:Grange85)",
            }
    headers2 = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
            }
    resp = requests.get(url, headers=headers)
    resp.encoding = 'utf-8'
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # parse out the "og:title" and "og:description" HTML meta tags
    title_tag = soup.find("meta", property="og:title")
    if title_tag:
        card["title"] = title_tag["content"]
    description_tag = soup.find("meta", property="og:description")
    if description_tag:
        card["description"] = description_tag["content"]

    # if there is an "og:image" HTML meta tag, fetch and upload that image
    image_tag = soup.find("meta", property="og:image")
    if image_tag:
        img_url = image_tag["content"]
        # naively turn a "relative" URL (just a path) into a full URL, if needed
        if "://" not in img_url:
            img_url = url + img_url
        resp = requests.get(img_url, headers=headers2)
        resp.raise_for_status()

        blob_resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
            headers={
                "Content-Type": "image/jpg",
                "Authorization": f"Bearer {key}",
                "User-Agent": "Grange85Bot/0.0 (https://en.wikipedia.org/wiki/User:Grange85)",
            },
            data=resp.content,
        )
        blob_resp.raise_for_status()
        card["thumb"] = blob_resp.json()["blob"]

    return {
        "$type": "app.bsky.embed.external",
        "external": card,
    }

def main():
    config = configparser.ConfigParser()
    config.read(BLUESKY_POSTER_CONFIG)
    feedlist = config.sections()
    for feed in feedlist:
        postdata = {
                "feed": feed,
                "app_password": config[feed]['appw'],
                "handle": config[feed]['user'],
                "lastpost": config[feed]['lastpost'],
                "feeduri": config[feed]['uri'],
            } 
        

        postdata = get_rss_content(postdata)
        if postdata:
            did = get_did(postdata['handle'])
            key = get_api_key(did, postdata['app_password'])
            postdata['embed_card'] = get_embed_url_card(key, postdata['link'])
            post_structure = prepare_post_for_bluesky(postdata)
            response = publish_on_bluesky(post_structure, did, key)
            #response = post_structure
            print(response)
    return True

if __name__ == '__main__':
    sys.exit(main())  
