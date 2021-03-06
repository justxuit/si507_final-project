'''
name: Xuan Huang
uniqname: huangxu

----------

SI 507 Winter 2020
Final Project
'''


import secrets
from requests_oauthlib import OAuth1
import requests
import json
import sqlite3
import paralleldots
import praw
import plotly.graph_objs as go


# KEYS
client_key_twitter = secrets.TWITTER_API_KEY
client_secret_twitter = secrets.TWITTER_API_SECRET
client_secret_reddit = secrets.REDDIT_API_KEY
access_token_twitter = secrets.TWITTER_ACCESS_TOKEN
access_token_secret_twitter = secrets.TWITTER_ACCESS_TOKEN_SECRET
pd_api_key = secrets.PARALLEL_DOTS_API_KEY


# AUTH
oauth_twitter = OAuth1(client_key_twitter,
               client_secret=client_secret_twitter,
               resource_owner_key=access_token_twitter,
               resource_owner_secret=access_token_secret_twitter)

reddit = praw.Reddit(client_id='5tocAlGc2XQ_Eg',
                     client_secret=client_secret_reddit,
                     redirect_uri='http://localhost:8080',
                     user_agent='SI 507 Final Project')
# Enable read-only mode
reddit.read_only = True

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
    connector = '|'

    try:  
        for key in params.keys():
            param_strings.append(f'{key}={params[key]}')
        param_strings.sort()
        unique_key = baseurl + connector + connector.join(param_strings)
    except:
        unique_key = baseurl + connector + connector.join(params)
    return unique_key


def construct_unique_key_reddit(username, limit):
    connector = '|'
    limit = str(limit)
    unique_key = username + connector + limit
    return unique_key


def make_request_twitter(baseurl, params):
    response = requests.get(baseurl, params=params, auth=oauth_twitter)
    return response.json()


def make_request_twitter_with_cache(baseurl, username):
    params = {"screen_name": username, "count": 10,
              "exclude_replies": 'true', "include_rts": 'false'}
    url = construct_unique_key(baseurl, params)
    # Check cache
    if url in CACHEDICT_TWITTER.keys():
        print('Using Twitter cache...')
        twitter_data = CACHEDICT_TWITTER[url]
    else:
        print('Fetching from Twitter API. Please wait...')
        twitter_data = make_request_twitter(baseurl, params)
        CACHEDICT_TWITTER[url] = twitter_data
        save_cache('twitter', CACHEDICT_TWITTER)
    return twitter_data


def format_twitter_data(twitter_data):
    formatted_text = []
    for tweet in twitter_data:
        raw_text = tweet['text']
        text_list = raw_text.split(' ')

        for word in text_list:
            if 'https' in word or '@' in word:
                text_list.remove(word)
        scrubbed_text = ' '.join(text_list)
        formatted_text.append(scrubbed_text)
    return formatted_text


def make_request_reddit(username, number_of_results):
    comments_list = []
    comments = reddit.redditor(username).comments.new(limit=number_of_results)
    for comment in comments:
        comments_list.append(comment.body)
    return comments_list


def make_request_reddit_with_cache(username, limit):
    unique_key = construct_unique_key_reddit(username, limit)
    if unique_key in CACHEDICT_REDDIT.keys():
        print('Using Reddit cache...')
        reddit_data = CACHEDICT_REDDIT[unique_key]
    else:
        print('Fetching from Reddit API. Please wait...')
        reddit_data = make_request_reddit(username, limit)
        CACHEDICT_REDDIT[unique_key] = reddit_data
        save_cache('reddit', CACHEDICT_REDDIT)
    return reddit_data


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
        print('Using PD cache...')
        pd_data = CACHEDICT_PD[unique_key]
    else:
        print('Fetching from ParallelDots API. Please wait...')
        pd_data = make_request_pd(api, text)
        CACHEDICT_PD[unique_key] = pd_data
        save_cache('pd', CACHEDICT_PD)
    return pd_data


def format_pd_data(pd_sentiment = {}, pd_abuse = {}):
    pd_data_formatted = {
        'sentiment': {},
        # 'emotion': {},
        'abuse': {}
    }

    batch_size = len(pd_sentiment)
    pd_data_formatted['sentiment']['total'] = batch_size
    # pd_data_formatted['emotion']['total'] = batch_size
    pd_data_formatted['abuse']['total'] = batch_size

    # Calculate Sentiment Data
    positive_scores = []
    neutral_scores = []
    negative_scores = []
    for result in pd_sentiment:
        try:
            positive_scores.append(result['positive'])
        except:
            positive_scores.append(0)
        
        try:
            neutral_scores.append(result['neutral'])
        except:
            neutral_scores.append(0)

        try:
            negative_scores.append(result['negative'])
        except:
            negative_scores.append(0)
    pd_data_formatted['sentiment']['positive'] = sum(positive_scores)/batch_size
    pd_data_formatted['sentiment']['neutral'] = sum(neutral_scores)/batch_size
    pd_data_formatted['sentiment']['negative'] = sum(negative_scores)/batch_size

    # # Calculate Abuse Data
    abusive_score = []
    hate_speech_score = []
    neither_score = []
    for result in pd_abuse:
        try:
            abusive_score.append(result['abusive'])
        except:
            abusive_score.append(0)

        try:
            hate_speech_score.append(result['hate_speech'])
        except:
            hate_speech_score.append(0)

        try:
            neither_score.append(result['neither'])
        except:
            neither_score.append(0)
    pd_data_formatted['abuse']['abusive'] = sum(abusive_score)/batch_size
    pd_data_formatted['abuse']['hate_speech'] = sum(hate_speech_score)/batch_size
    pd_data_formatted['abuse']['neither'] = sum(neither_score)/batch_size
        
    return pd_data_formatted


def update_twitter_table(text_data, username, associated_reddit = 'NULL'):
    create_twittercomments = '''
        CREATE TABLE IF NOT EXISTS "TwitterComments" (
            "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            "tweetText"	TEXT NOT NULL,
            "avgPositiveScore"	REAL NOT NULL,
            "avgNegativeScore"	REAL NOT NULL,
            "avgNeutralScore"	REAL NOT NULL,
            "avgAbusiveScore"	REAL NOT NULL,
            "avgHateSpeechScore"	REAL NOT NULL,
            "avgNeitherAbuseScore"	REAL NOT NULL,
            "authorUsername"	TEXT NOT NULL,
            "assocRedditName"	TEXT,
            FOREIGN KEY("assocRedditName") REFERENCES "RedditComments"("authorUsername")
        );
    '''
    cur.execute(create_twittercomments)
    conn.commit()
    twitter_comment_data = [f'{text_data}', pd_twitter_analysis['sentiment']['positive'],
                            pd_twitter_analysis['sentiment']['negative'], pd_twitter_analysis['sentiment']['neutral'], pd_twitter_analysis['abuse']['abusive'], pd_twitter_analysis['abuse']['hate_speech'], pd_twitter_analysis['abuse']['neither'], username, associated_reddit]
    insert_tweet = '''
            INSERT INTO TwitterComments
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
    cur.execute(insert_tweet, twitter_comment_data)


def update_reddit_table(text_data, username, associated_twitter = 'NULL'):
    create_redditcomments = '''
        CREATE TABLE IF NOT EXISTS "RedditComments" (
            "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            "commentText"	TEXT NOT NULL,
            "avgPositiveScore"	REAL NOT NULL,
            "avgNegativeScore"	REAL NOT NULL,
            "avgNeutralScore"	REAL NOT NULL,
            "avgAbusiveScore"	REAL NOT NULL,
            "avgHateSpeechScore"	REAL NOT NULL,
            "avgNeitherAbuseScore"	REAL NOT NULL,
            "authorUsername"	TEXT NOT NULL,
            "assocTwitterName"	TEXT,
            FOREIGN KEY("assocTwitterName") REFERENCES "TwitterComments"("authorUsername")
        );
    '''
    cur.execute(create_redditcomments)
    conn.commit()
    reddit_comment_data = [f'{text_data}', pd_reddit_analysis['sentiment']['positive'],
                           pd_reddit_analysis['sentiment']['negative'], pd_reddit_analysis['sentiment']['neutral'], pd_reddit_analysis['abuse']['abusive'], pd_reddit_analysis['abuse']['hate_speech'], pd_reddit_analysis['abuse']['neither'], username, associated_twitter]
    insert_reddit_comment = '''
            INSERT INTO RedditComments
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
    cur.execute(insert_reddit_comment, reddit_comment_data)



if __name__ == "__main__":
    CACHEDICT_TWITTER = open_cache('twitter')
    CACHEDICT_REDDIT = open_cache('reddit')
    CACHEDICT_PD = open_cache('pd')

    while True:
        twitter_handle = 'NULL'
        reddit_handle = 'NULL'
        pd_twitter_analysis = {}
        pd_reddit_analysis = {}

        user_input = input("Which social media platform do you want to explore? Enter 'Twitter', 'Reddit', or 'Both', or enter 'exit' to exit: ").lower()

        if (user_input == 'twitter'):
            twitter_handle = input("Please enter Twitter username to look up: ")
            # Twitter Data
            try:
                response_twitter = make_request_twitter_with_cache(TWITTER_BASE_URL, twitter_handle)
                formatted_tweets = format_twitter_data(response_twitter)
                # PD Data
                pd_twitter_sentiment = make_request_pd_with_cache(
                    'sentiment', formatted_tweets)['sentiment']
                pd_twitter_abuse = make_request_pd_with_cache(
                'abuse', formatted_tweets)['abuse']
                pd_twitter_analysis = format_pd_data(
                pd_twitter_sentiment, pd_twitter_abuse)
            except:
                print("No data for that user was found. Please try another username.")

        elif (user_input == 'reddit'):
            reddit_handle = input(
                "Please enter Reddit username to look up: ").lower()
            # Reddit Data
            reddit_comments = make_request_reddit_with_cache(reddit_handle, 10)
            # print(reddit_comments)
            pd_reddit_sentiment = make_request_pd_with_cache('sentiment', reddit_comments)['sentiment']
            pd_reddit_abuse = make_request_pd_with_cache('abuse', reddit_comments)['abuse']
            pd_reddit_analysis = format_pd_data(pd_reddit_sentiment, pd_reddit_abuse)
        elif (user_input == 'both'):
            twitter_handle = input("Please enter Twitter username to look up: ")
            reddit_handle = input("Please enter Reddit username to look up: ")

            response_twitter = make_request_twitter_with_cache(TWITTER_BASE_URL, twitter_handle)
            formatted_tweets = format_twitter_data(response_twitter)
            pd_twitter_sentiment = make_request_pd_with_cache(
                'sentiment', formatted_tweets)['sentiment']
            pd_twitter_abuse = make_request_pd_with_cache(
                'abuse', formatted_tweets)['abuse']
            pd_twitter_analysis = format_pd_data(
                pd_twitter_sentiment, pd_twitter_abuse)

            reddit_comments = make_request_reddit_with_cache(reddit_handle, 10)
            pd_reddit_sentiment = make_request_pd_with_cache(
                'sentiment', reddit_comments)['sentiment']
            pd_reddit_abuse = make_request_pd_with_cache(
                'abuse', reddit_comments)['abuse']
            pd_reddit_analysis = format_pd_data(
                pd_reddit_sentiment, pd_reddit_abuse)
        elif (user_input == 'exit'):
            break
        else:
            print("Please enter a valid command.")


        conn = sqlite3.connect("final_project.db")
        cur = conn.cursor()

        if (user_input == 'twitter'):
            update_twitter_table(formatted_tweets, twitter_handle)
        elif (user_input == 'reddit'):
            update_reddit_table(reddit_comments, reddit_handle)
        elif (user_input == 'both'):
            update_twitter_table(formatted_tweets, twitter_handle, reddit_handle)
            update_reddit_table(reddit_comments, reddit_handle, twitter_handle)

        conn.commit()
        conn.close()

        # Plotly
        sentiment_categories = [
            'Sentiment - Positive', 
            'Sentiment - Negative', 
            'Sentiment - Neutral', 
            'Abusive', 
            'Hate Speech'
            ]

        graph_username = ''
        if (user_input == 'twitter'):
            graph_username = twitter_handle.upper()
            sentiment_values = [
                pd_twitter_analysis['sentiment']['positive'],
                pd_twitter_analysis['sentiment']['negative'],
                pd_twitter_analysis['sentiment']['neutral'],
                pd_twitter_analysis['abuse']['abusive'],
                pd_twitter_analysis['abuse']['hate_speech']
            ]
            semantic_data = go.Bar(x=sentiment_categories, y=sentiment_values)
            semantic_layout = go.Layout(title=f"Twitter Semantic Analysis for: {graph_username}")
            fig = go.Figure(
                data=semantic_data, layout=semantic_layout)
            fig.show()
        elif (user_input == 'reddit'):
            graph_username = reddit_handle.upper()
            sentiment_values = [
                pd_reddit_analysis['sentiment']['positive'],
                pd_reddit_analysis['sentiment']['negative'],
                pd_reddit_analysis['sentiment']['neutral'],
                pd_reddit_analysis['abuse']['abusive'],
                pd_reddit_analysis['abuse']['hate_speech']
            ]
            semantic_data = go.Bar(x=sentiment_categories, y=sentiment_values)
            semantic_layout = go.Layout(title=f"Reddit Semantic Analysis for: {graph_username}")
            fig = go.Figure(
                data=semantic_data, layout=semantic_layout)
            fig.show()
        elif (user_input == 'both'):
            sentiment_values_twitter = [
                pd_twitter_analysis['sentiment']['positive'],
                pd_twitter_analysis['sentiment']['negative'],
                pd_twitter_analysis['sentiment']['neutral'],
                pd_twitter_analysis['abuse']['abusive'],
                pd_twitter_analysis['abuse']['hate_speech']
            ]
            sentiment_values_reddit = [
                pd_reddit_analysis['sentiment']['positive'],
                pd_reddit_analysis['sentiment']['negative'],
                pd_reddit_analysis['sentiment']['neutral'],
                pd_reddit_analysis['abuse']['abusive'],
                pd_reddit_analysis['abuse']['hate_speech']
            ]
            semantic_data = [go.Bar(name='Twitter', x=sentiment_categories, y=sentiment_values_twitter), go.Bar(name='Reddit', x=sentiment_categories, y=sentiment_values_reddit)]
            semantic_layout = go.Layout(
                title=f"Reddit & Twitter Semantic Analysis for: {twitter_handle.upper()} / {reddit_handle.upper()}")
            fig = go.Figure(data=semantic_data, layout=semantic_layout)
            # Change the bar mode
            fig.update_layout(barmode='group')
            fig.show()



