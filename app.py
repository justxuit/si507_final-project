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

    try:  
        for key in params.keys():
            param_strings.append(f'{key}={params[key]}')
        param_strings.sort()
        unique_key = baseurl + connector + connector.join(param_strings)
    except:
        unique_key = baseurl + connector.join(params)
    return unique_key


def make_request_twitter(baseurl, params):
    response = requests.get(baseurl, params=params, auth=oauth_twitter)
    return response.json()


def make_request_twitter_with_cache(baseurl, params):
    url = construct_unique_key(baseurl, params)
    # Check cache
    if url in CACHEDICT_TWITTER.keys():
        print('Using cache...')
        twitter_data = CACHEDICT_TWITTER[url]
    else:
        print('Fetching from API. This may take a moment...')
        twitter_data = make_request_twitter(baseurl, params)
        CACHEDICT_TWITTER[url] = twitter_data
        save_cache('twitter', CACHEDICT_TWITTER)
    return twitter_data


def format_twitter_data(twitter_data):
    formatted_text = []
    for tweet in twitter_data:
        raw_text = tweet['text']
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


def make_request_pd_with_cache(api, text):
    unique_key = construct_unique_key(api, text)
    # Check cache
    if unique_key in CACHEDICT_PD.keys():
        print('Using cache...')
        pd_data = CACHEDICT_PD[unique_key]
    else:
        print('Fetching from API. This may take a moment...')
        pd_data = make_request_pd(api, text)
        CACHEDICT_PD[unique_key] = pd_data
        save_cache('pd', CACHEDICT_PD)
    return pd_data


def format_pd_data(pd_response):
    # pd_data_raw = {}
    pd_data_formatted = {
        'sentiment': {},
        'emotion': {},
        'abuse': {}
    }

    if ('sentiment' in pd_response):
        pd_data_formatted['sentiment']['total'] = pd_response['sentiment']
        positive_scores = []
        neutral_scores = []
        negative_scores = []
        for result in pd_response['sentiment']:
            positive_scores.append(result['positive'])
            neutral_scores.append(result['neutral'])
            negative_scores.append(result['negative'])
        pd_data_formatted['sentiment']['positive_scores'] = positive_scores
        pd_data_formatted['sentiment']['neutral_scores'] = neutral_scores
        pd_data_formatted['sentiment']['negative_scores'] = negative_scores
    # elif ('emotion' in pd_response):
    #     happy_scores = []
    #     excited_scores = []
    #     angry_scores = []
    #     sad_scores = []
    #     fear_scores = []
    #     bored_scores = []
    #     for result in pd_response['emotion']:
    #         happy_scores.append(result['Happy'])
    #         excited_scores.append(result['Excited'])
    #         angry_scores.append(result['Angry'])
    #         sad_scores.append(result['Sad'])
    #         fear_scores.append(result['Fear'])
    #         bored_scores.append(result['Bored'])
    #     pd_data_formatted['emotion']['happy_scores'] = happy_scores
    #     pd_data_formatted['emotion']['excited_scores'] = excited_scores
    #     pd_data_formatted['emotion']['angry_scores'] = angry_scores
    #     pd_data_formatted['emotion']['sad_scores'] = sad_scores
    #     pd_data_formatted['emotion']['fear_scores'] = fear_scores
    #     pd_data_formatted['emotion']['bored_scores'] = bored_scores
    else:
        print('sentiment not found')
        
    return pd_data_formatted


def make_request_reddit():
    pass



if __name__ == "__main__":
    params = {"screen_name": "umsi", "count": 1000, "exclude_replies": 'true', "include_rts": 'false'}
    response_twitter = make_request_twitter_with_cache(
        TWITTER_BASE_URL, params)
    # print(response_twitter)
    # print('raw', response_twitter)
    try_text = format_twitter_data(response_twitter)
    # test_words = ["Germany’s largest newspaper comes out swinging against China. This is a must watch for US journalists who seem intent on doing China’s bidding.", "This is shit."]
    print(try_text)

    # response_pd = make_request_pd_with_cache('sentiment', try_text)
    # test_format = format_pd_data(response_pd)
    # # print(response_pd)
    # print(test_format)
