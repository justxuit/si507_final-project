'''
name: Xuan Huang
uniqname: huangxu

----------

SI 507 Winter 2020
Final Project
'''



from requests_oauthlib import OAuth1
import json
import requests
import paralleldots
import secrets

CACHE_FILENAME = "twitter_cache.json"
CACHE_DICT = {}

# KEYS
client_key_twitter = secrets.TWITTER_API_KEY
client_secret_twitter = secrets.TWITTER_API_SECRET
access_token_twitter = secrets.TWITTER_ACCESS_TOKEN
access_token_secret_twitter = secrets.TWITTER_ACCESS_TOKEN_SECRET
pd_api_key = secrets.PARALLEL_DOTS_API_KEY


# AUTH
oauth_twitter = OAuth1(client_key_twitter,
               client_secret=client_secret_twitter,
               resource_owner_key=access_token_twitter,
               resource_owner_secret=access_token_secret_twitter)
paralleldots.set_api_key(pd_api_key)


# URLS
TWITTER_BASE_URL = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
PD_BASE_URL = 'https://apis.paralleldots.com/v4/'
PD_APIS = ['sentiment', 'emotion', 'abuse']

# CACHES
CACHEFILE_TWITTER = 'twitter_cache.json'
CACHEDICT_TWITTER = {}
CACHEFILE_REDDIT = 'reddit_cache.json'
CACHEDICT_REDDIT = {}
CACHEFILE_PD = 'pd_cache.json'
CACHEDICT_PD = {}

    

# def test_oauth():
#     ''' Helper function that returns an HTTP 200 OK response code and a 
#     representation of the requesting user if authentication was 
#     successful; returns a 401 status code and an error message if 
#     not. Only use this method to test if supplied user credentials are 
#     valid. Not used to achieve the goal of this assignment.'''

#     url = "https://api.twitter.com/1.1/account/verify_credentials.json"
#     auth = OAuth1(client_key_twitter, client_secret_twitter,
#                   access_token_twitter, access_token_secret_twitter)
#     authentication_state = requests.get(url, auth=auth).json()
#     return authentication_state


def open_cache(api):
    cache_filename = api + '_cache.json'
    try:
        cache_file = open(cache_filename, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(api, cache_dict):
    cache_filename = api + '_cache.json'
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(cache_filename, "w")
    fw.write(dumped_json_cache)
    fw.close()


def construct_unique_key(baseurl, params):
    param_strings = []
    connector = '_'

    for key in params.keys():
        param_strings.append(f'{key}={params[key]}')
    param_strings.sort()
    unique_key = baseurl + connector + connector.join(param_strings)
    return unique_key


def make_request_twitter(baseurl, params):
    response = requests.get(baseurl, params=params, auth=oauth_twitter)
    return response.json()


def make_request_twitter_with_cache(baseurl, params):
    url = construct_unique_key(baseurl, params)

    # Check cache
    if url in CACHEDICT_TWITTER.keys():
        twitter_data = CACHEDICT_TWITTER[url]
    else:
        twitter_data = make_request_twitter(baseurl, params)
        CACHEDICT_TWITTER[url] = twitter_data
        save_cache('twitter', CACHEDICT_TWITTER)
    return twitter_data


def format_twitter_data_for_analysis(twitter_data):
    formatted_text = []
    for tweet in twitter_data:
        raw_text = tweet['retweeted_status']['text']
        formatted_text.append(raw_text)
    return formatted_text


def make_request_pd(api, text):
    if (api == 'sentiment'):
        response = paralleldots.batch_sentiment(text)
    elif (api == 'emotion'):
        response = paralleldots.batch_emotion(text)
    elif (api == 'abuse'):
        response = paralleldots.batch_abuse(text)
    return response


def make_request_reddit():
    pass



if __name__ == "__main__":
    params = {"screen_name": "realDonaldTrump", "count": 5}
    response_twitter = make_request_twitter_with_cache(
        TWITTER_BASE_URL, params)
    # print(response_twitter)
    try_text = format_twitter_data_for_analysis(response_twitter)
    # test_words = ["Germany’s largest newspaper comes out swinging against China. This is a must watch for US journalists who seem intent on doing China’s bidding.", "This is shit."]

    response_pd = make_request_pd('sentiment', try_text)
    print(response_pd)
