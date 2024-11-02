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
            facets.append({
                "$type": "app.bsky.richtext.facet#tag",
                "tag": tag,
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

def get_rss_content(feeduri, last_post, config, feed):

    # Parse the RSS feed
    feedout = feedparser.parse(feeduri)

    # If you plan to post the latest content, it's usually the first entry in the feed
    latest_post_title = feedout.entries[0].title
    latest_post_description = feedout.entries[0].description
    latest_post_link = feedout.entries[0].link
    latest_post_guid = feedout.entries[0].guid

    # hashtags = get_hashtags(latest_post_description)
    # sys.exit()

    if latest_post_guid == last_post:
        return False, False, False
    else:
        with open(BLUESKY_POSTER_CONFIG, 'w') as configfile:
            config[feed]['lastpost'] = latest_post_guid
            config.write(configfile)
    return latest_post_title, latest_post_description, latest_post_link

def prepare_post_for_bluesky(title, link, embed, hashtags):
    """Convert the RSS content into a format suitable for Bluesky."""

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # The post's body text
    post_text = f"{title}"
    # The post structure for Bluesky
    post_structure = {
        "$type": "app.bsky.feed.post",
        "text": post_text,
        "createdAt": now
            }
    post_structure["facets"] = hashtags
    post_structure["embed"] = embed
    return post_structure

def publish_on_bluesky(post_structure, did, key):
    """Publish the structured post on Bluesky."""

    # The complete record for the Bluesky post, including our structured content
    post_record = {
        "collection": "app.bsky.feed.post",
        "repo": did,    # The unique DID of our account
        "record": post_structure
    }

    # Send a POST request to publish the post on Bluesky
    # post_request = requests.post(BLUESKY_API_ENDPOINT, body=json.dumps(post_record), headers=headers)

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
    resp = requests.get(url)
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
        resp = requests.get(img_url)
        resp.raise_for_status()

        blob_resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
            headers={
                "Content-Type": "image/jpg",
                "Authorization": f"Bearer {key}"
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
        app_password = config[feed]['appw']
        handle = config[feed]['user']
        last_post = config[feed]['lastpost']
        feeduri = config[feed]['uri']
        did = get_did(handle)
        key = get_api_key(did, app_password)
        title, description, link = get_rss_content(feeduri, last_post, config, feed)
        if title:
            embed_card = get_embed_url_card(key, link)
            hashtags = get_hashtags(description)
            post_structure = prepare_post_for_bluesky(title, link, embed_card, hashtags)
            response = publish_on_bluesky(post_structure, did, key)
            return response

if __name__ == '__main__':
    sys.exit(main())  
