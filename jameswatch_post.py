#! /usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from numpy.random import shuffle
import tweepy
import json
from webpreview import web_preview
from twitter_auth import *
'''
This is what your twitter_auth.py should look like:
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

# OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
'''

# BetaFace API for ethnicity and gender recognition
def ethnicity_gender(imgurl):
    # Public free API key
    api_key = "d45fd466-51e2-4701-8da8-04351c872236"
    endpoint = "https://www.betafaceapi.com/api/v2/media"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {"api_key": api_key,
            "file_uri": imgurl,
            "detection_flags": "classifiers",
            "recognize_targets": ["all@mynamespace"],
            "original_filename": "mugshot.jpg"}
    result = requests.post(endpoint, data=str(data), headers=headers)
    result = (json.loads(result.text))
    try:
        # Get the first recognized face
        tags = result["media"]["faces"][0]["tags"]
    except:
        # Return empty parameters if that doesn't work
        return ["", ""]
    # Ethnicity is always under 31, gender is always under 18
    ethnicity = tags[31]["value"]
    gender = tags[18]["value"]
    return [ethnicity, gender]


api = tweepy.API(auth)

# Fetching a list of existing tweets
existing = tweepy.Cursor(api.user_timeline, id="realJamesWatch").items()
tweets = []
for status in existing:
    tweets.append(status.text)

base_url = "https://news.google.com/"
# Search for "james arrested" on Google news and scrape the result
# Will only scrape the last 100 results but that's all we need
search = base_url + "search?q=james+arrested&hl=en-US&gl=US&ceid=US:en"
news = requests.get(search).text
soup = BeautifulSoup(news, "lxml")
articles = soup.find_all("h3")

# Open the list of comments
with open("comment.json", "r") as comments:
    comments = json.loads(comments.read())

# Open a file with articles that we've already posted
with open("history.json", "r") as history:
    history = json.loads(history.read())

news = []
for article in tqdm(articles):
    a = article.find("a")
    link = base_url + a["href"][2:]
    # Find out the actual url
    try:
        url = requests.get(link).url
    except requests.exceptions.ConnectionError:
        url = link
    # Unless it redirects to the cookies or GDPR consent
    if "gdpr" in url:
        url = link
    # Only append an article URL to the list if we haven't posted it yet
    if url not in history:
        try:
            title, description, image = web_preview(url, parser="lxml")
        # Leave "image" empty if anything goes wrong
        except:
            image = ""

        # Check if the perpetrator is black or female. Females can't be James
        # And we don't want to accidentally post a black dude with racist commentary.
        # The irony will be... hard to understand, to say the least.
        e = ethnicity_gender(image)
        if e[0] == "black" or e[1] == "female":
            continue
        news.append(url)

# Mix comments and article URLs
shuffle(news)
shuffle(comments)

# Remove comments that we already posted
comments = [c for c in comments if c not in tweets]

# Create a dictionary of comments and news
news = news[0:len(comments)]
candidates = dict(zip(comments, news))

for c, n in candidates.items():
    tweet = c + " " + n
    print("Here's the tweet:")
    print(tweet)

    # Tweet comment + whitespace + article URL
    api.update_status(c + " " + n)

    # Append the URL to the history and dump the new history to the history.json file
    history.append(n)
    with open("history.json", "w") as newhistory:
        json.dump(history, newhistory)
    print("Done.")
    exit()

# If we exit the loop that means we ran out of fresh comments
print("No unique comments found. Didn't tweet anything")
