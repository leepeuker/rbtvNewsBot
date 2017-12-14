import datetime
import json
import logging
import praw
import requests
import time

# URL to request news json
FORUM_SOURCE_URL = 'https://forum.rocketbeans.tv/c/news.json'
# Posting new topics to this subreddit
SUBREDDIT = 'rocketbeans'
# Delay in seconds between checking for news
TIME_SLEEP = 300
# Name of info/error log
LOG_NAME = 'rbtvNewsBot.log'
# RBTV json time format
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
# Set start time of program
PROGRAM_START_TIME = datetime.datetime.today()


# Reddit authentication
def authenticate():
    reddit = praw.Reddit('rbtvNewsBot', user_agent='rbtvNewsBot (by /u/sysLee)')
    logging.info('{}: Authenticated as {}'.format(datetime.datetime.today(), reddit.user.me()))
    return reddit


# Request the news from the forum as json
def get_news_json():
    # Send http request
    request = requests.get(FORUM_SOURCE_URL)
    # Check http response status code (200 = ok)
    if not request.status_code == 200:
        logging.error('{}: get_news_json() - HTTP request error ("{}")'.format(datetime.datetime.today(), request.status_code))
        return
    # Check application data type (we want only json)
    if 'application/json' not in request.headers['content-type']:
        logging.error('{}: get_news_json() - Wrong HTTP application type ("{}")'.format(datetime.datetime.today(), request.headers['content-type']))
        return
    # Check if response is not empty
    if not request.text:
        logging.error('{}: get_news_json() - HTTP response empty'.format(datetime.datetime.today()))
        return
    return json.loads(request.text)


# Get the time of the latest new topic from topic list
def get_new_latest_topic_time(new_topics, latest_topic_time):
    for topic in new_topics:
        if topic['created_at'] > latest_topic_time:
            latest_topic_time = topic['created_at']
    return latest_topic_time


# Get all topics, which were created before the latest_topic_time
def get_new_topics(news_json, latest_topic_time):
    new_topics = []
    if news_json:
        for topic in news_json['topic_list']['topics']:
            topic['created_at'] = datetime.datetime.strptime(topic['created_at'], TIME_FORMAT)
            if topic['pinned']:
                if topic['created_at'] > latest_topic_time:
                    new_topics.append(topic)
            elif topic['created_at'] > latest_topic_time:
                new_topics.append(topic)
            else:
                break
    return new_topics


# Main function
def main():
    logging.basicConfig(filename=LOG_NAME, level=logging.INFO)
    logging.info('{}: Started rbtvNewsBot'.format(PROGRAM_START_TIME))

    reddit = authenticate()
    news_json = get_news_json()
    latest_topic_time = PROGRAM_START_TIME

    while 1:
        new_topics = get_new_topics(news_json, latest_topic_time)
        logging.info('{}: Found {} new topic/s'.format(datetime.datetime.today(), len(new_topics)))
        if new_topics:
            # logging.info('{}: Found {} new topic/s'.format(datetime.datetime.today(), len(new_topics)))
            for topic in new_topics:
                run_bot(reddit, topic)
            latest_topic_time = get_new_latest_topic_time(new_topics, latest_topic_time)
        new_topics = []
        news_json = get_news_json()
        time.sleep(TIME_SLEEP)
    exit(0)


# Post the news to subreddit
def run_bot(reddit, topic):
    subreddit = reddit.subreddit(SUBREDDIT)
    subreddit.submit(topic['title'], url='https://forum.rocketbeans.tv/t/' + topic['slug'] + '/' + topic['id'])
    logging.info('{}: New topic/s successfully posted to reddit'.format(datetime.datetime.today()))
    return


if __name__ == '__main__':
    main()
