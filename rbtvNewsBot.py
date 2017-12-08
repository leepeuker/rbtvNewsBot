import requests
import datetime
import time
import json
import praw

FORUM_SOURCE_URL = 'https://www.leepeuker.de/api'
SUBREDDIT = 'nativesys'
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
PROGRAM_START_TIME = datetime.datetime.today()
print(PROGRAM_START_TIME)


# Reddit authentication
def authenticate():
    reddit = praw.Reddit('sysLee', user_agent='rbtvNewsBot (by /u/sysLee)')
    print('Authenticated as {}...'.format(reddit.user.me()))
    return reddit


# Request the news from the forum as json
def get_news_json():
    # Send http request
    request = requests.get(FORUM_SOURCE_URL)
    # Check http response status code (200 = ok)
    if not request.status_code == 200:
        print('Error: HTTP Status Code: {}'.format(request.status_code))
        exit(1)
    # Check application data type (we want only json)
    if 'application/json' not in request.headers['content-type']:
        print('Error: Response wrong application type: {}'.format(request.headers['content-type']))
        exit(1)
    return json.loads(request.text)


# Get the time of the latest new topic from a topic list
def get_new_latest_topic_time(new_topics, latest_topic_time):
    for topic in new_topics:
        if topic['created_at'] > latest_topic_time:
            latest_topic_time = topic['created_at']
    return latest_topic_time


# Get all topics, which were created before the latest_topic_time
def get_new_topics(news_json, latest_topic_time):
    new_topics = []
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
    reddit = authenticate()
    news_json = get_news_json()
    latest_topic_time = PROGRAM_START_TIME
    while 1:
        new_topics = get_new_topics(news_json, latest_topic_time)
        if new_topics:
            for topic in new_topics:
                run_bot(reddit, topic)
            latest_topic_time = get_new_latest_topic_time(new_topics, latest_topic_time)
        else:
            print('no new topic')
        new_topics = []
        news_json = get_news_json()
        time.sleep(10)
    exit(0)


# Post the news to subreddit
def run_bot(reddit, topic):
    subreddit = reddit.subreddit(SUBREDDIT)
    subreddit.submit(topic['title'], url='https://forum.rocketbeans.tv/t/' + topic['slug'])
    return


if __name__ == '__main__':
    main()
