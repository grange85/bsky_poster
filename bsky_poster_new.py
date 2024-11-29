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
DEBUG = True
def rw_config(action):
    if action == "read":
        config = configparser.ConfigParser()
        #config.read('dummy-config.ini')
        config.read(BLUESKY_POSTER_CONFIG)
        return config
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


def get_rss_content(postdata):

    feedout = feedparser.parse(postdata['feeduri'])
    postdata['title'] = unescape(feedout.entries[0].title.strip())
    postdata['description'] = feedout.entries[0].description
    postdata['link'] = feedout.entries[0].link
    postdata['guid'] = feedout.entries[0].guid

    if postdata['guid'] == postdata['lastpost']:
        return False

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
    hashtags = ([s.strip('#') for s in hashtags])
    hashreturn = {}
    tags = []
    for tag in hashtags:
        startByte = description.encode().find(("#" + tag).encode())
        endByte = startByte + len(tag.encode())+1
        tags.append(f"{tag}|{startByte}|{endByte}")
        hashreturn[tag] = [startByte,endByte]
    if not hashtags:
        return False
    else:
        return tags

def get_url(description):
    if description.find("https://") > 0:
        uri = re.search(r'https:[^( |$)]*', description)
        startByte = description.encode().find(("https://").encode())
        endByte = description.encode().find((" ").encode(), startByte)
        if endByte == -1:
            endByte = len(description.encode())
        urireturn = f"{uri.group()}|{startByte}|{endByte}"
        return urireturn
    else:
        return False


def prepare_post_for_bluesky(postdata):
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # The post structure for Bluesky
    facets = []
    post_structure = {
        "$type": "app.bsky.feed.post",
        "text": postdata['content'],
        "createdAt": now
            }
    if postdata['hashtags'] != False:
        for tag in postdata['hashtags']:
            tagdata = tag.split('|')
            facets.append({
                "index": {
                    "byteStart": int(tagdata[1]),
                    "byteEnd": int(tagdata[2]),
                    },
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#tag",
                        "tag": tagdata[0],
                        }
                    ],
                })
    if postdata['uri'] != False:
        uridata = postdata['uri'].split('|')
        facets.append({
            "index": {
                "byteStart": int(uridata[1]),
                "byteEnd": int(uridata[2]),
                },
            "features": [
                {
                    "$type": "app.bsky.richtext.facet#link",
                    "uri": uridata[0],
                    }
                ],
            })
            
    if postdata['embed_card'] != False:
        post_structure['embed'] = postdata['embed_card']

    if facets:
        post_structure['facets'] = facets 
    return post_structure


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


def publish_on_bluesky(postdata):

    # The complete record for the Bluesky post, including our structured content
    post_record = {
        "collection": "app.bsky.feed.post",
        "repo": postdata['did'],    # The unique DID of our account
        "record": postdata['payload']
    }
    post_request = requests.post(
        BLUESKY_API_ENDPOINT,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {postdata['key']}"
        },
        data=json.dumps(post_record),
    )
    print(json.loads(post_request.content)) 
    response = json.loads(post_request.content)
    #response = post_record
    if "validationStatus" in response:
        if response['validationStatus'] == "valid":
            config = configparser.ConfigParser()
            config.read(BLUESKY_POSTER_CONFIG)
            with open(BLUESKY_POSTER_CONFIG, 'w') as configfile:
                config[postdata['feed']]['lastpost'] = postdata['guid']
                config.write(configfile)
            return response
        else:
            return False
    else:
        return False

def main():
    config = rw_config('read')
    feedlist = config.sections()
    for feed in feedlist:
        print(f"Processing {feed}")
        postdata = {
                "feed": feed,
                "app_password": config[feed]['appw'],
                "handle": config[feed]['user'],
                "lastpost": config[feed]['lastpost'],
                "feeduri": config[feed]['uri'],
            } 
        postdata = get_rss_content(postdata)

        if postdata != False:
            postdata['did'] = get_did(postdata['handle'])
            postdata['key'] = get_api_key(postdata['did'], postdata['app_password'])
            postdata['embed_card'] = get_embed_url_card(postdata['key'], postdata['link'])
            postdata['payload'] = prepare_post_for_bluesky(postdata)
            response = publish_on_bluesky(postdata)
            print(response)
if __name__ == '__main__':
    sys.exit(main())  
