import json
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from config import *
from unidecode import unidecode
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import sqlite3
import time

# it's ok to use one shared sqlite connection
# as we are making selects only, no need for any kind of serialization as well
conn = sqlite3.connect('twitter.db', check_same_thread=False)
c = conn.cursor()


def create_table():
    try:
        c.execute("CREATE TABLE IF NOT EXISTS sentiment(unix REAL, tweet TEXT, sentiment REAL)")
        c.execute("CREATE INDEX fast_unix ON sentiment(unix)")
        c.execute("CREATE INDEX fast_tweet ON sentiment(tweet)")
        c.execute("CREATE INDEX fast_sentiment ON sentiment(sentiment)")
        conn.commit()
    except Exception as e:
        print(str(e))


analyzer = SentimentIntensityAnalyzer()


class TweetStreamListener(StreamListener):
    # on success
    def on_data(self, data):
        try:
            # decode json
            tweet = json.loads(data)
            # print(tweet)
            vs = analyzer.polarity_scores(tweet['text'])
            if "text" in tweet.keys():
                payload = {'tweet': unidecode(tweet['text']),
                           'ts': (tweet['timestamp_ms']),
                           'sentiment': str(vs['compound'])
                           },
                payload = payload[0]
                ts = payload.get('ts')
                tweet = payload.get('tweet')
                sentiment = payload.get('sentiment')
                c.execute("INSERT INTO sentiment (unix, tweet, sentiment) VALUES (?, ?, ?)", (ts, tweet, sentiment))
                conn.commit()
                print(ts, tweet, sentiment)

        # if there is no tweet
        except KeyError as e:
            print(str(e))
        return True

    # on failure
    def on_error(self, status):
        print(status)


if __name__ == '__main__':
    create_table()
    while True:
        try:
            # create instance of the tweepy tweet stream listener
            listener = TweetStreamListener()
            # set twitter keys/tokens
            auth = OAuthHandler(ckey, csecret)
            auth.set_access_token(atoken, atokensecret)
            # create instance of the tweepy stream
            stream = Stream(auth, listener)
            stream.filter(track=["a", "e", "i", "o", "u"])
        except Exception as e:
            print(str(e))
            time.sleep(5)
