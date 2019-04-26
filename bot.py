import praw
import requests
import bs4
import html2text
import time, os
import bmemcached
import re

# from https://github.com/arxiv-vanity/arxiv-vanity/blob/master/arxiv_vanity/scraper/arxiv_ids.py
ARXIV_ID_PATTERN = r'([a-z\-]+(?:\.[A-Z]{2})?/\d{7}|\d+\.\d+)(v\d+)?'
ARXIV_URL_RE = re.compile(r'arxiv.org/[^\/]+/({})(\.pdf)?'.format(ARXIV_ID_PATTERN), re.I)

def get_bot():
    PRAW_CLIENT_ID = os.environ.get('PRAW_CLIENT_ID')
    PRAW_CLIENT_SECRET = os.environ.get('PRAW_CLIENT_SECRET')
    PRAW_PASSWORD = os.environ.get('PRAW_PASSWORD')
    PRAW_USERNAME = os.environ.get('PRAW_USERNAME')
    PRAW_USERAGENT = os.environ.get('PRAW_USERAGENT')
    return praw.Reddit(
        username=PRAW_USERNAME,
        password=PRAW_PASSWORD,
        client_id=PRAW_CLIENT_ID,
        client_secret=PRAW_CLIENT_SECRET,
        user_agent=PRAW_USERAGENT
        )


r = get_bot()

subreddit = r.subreddit('pythonforengineers')

# alreadydone = set()


def scrape_arxiv(arxiv_id):
    url = 'https://arxiv.org/abs/{}'.format(arxiv_id)
    r = requests.get(url)
    soup = bs4.BeautifulSoup(r.text)
    abstract = soup.select('.abstract')[0]
    abstract = html2text.html2text(abstract.decode()).replace('\n', ' ')

    authors = soup.select('.authors')[0]
    authors = html2text.html2text(authors.decode()).replace('\n', ' ')
    authors = authors.replace('(/', '(http://arxiv.org/')

    title = soup.select('.title')[0]
    title =  html2text.html2text(title.decode()).replace('\n', ' ')[2:]

    abs_link = u'[Abstract page]({})'.format(url)
    pdf_link = u'[Read as PDF](https://arxiv.org/pdf/{})'.format(arxiv_id)
    web_link = u'[Read as web page on arXiv Vanity](https://www.arxiv-vanity.com/papers/{}/)'.format(arxiv_id)
    links = u'{} | {} | {}'.format(pdf_link, abs_link, web_link)
    response = '\n\n'.join([title, authors, abstract, links]) 
    return response


def comment(cache):
    print(time.asctime(), "searching")
    try:
        all_posts = subreddit.new(limit=100)
        for post in all_posts:
            match = ARXIV_URL_RE.search(post.url)
            if match:
                arxiv_id = match.group(1)
                if cache.get(post.id) and cache.get(post.id) is 'T':
                    print "Parsed this post already: %s"%(post.permalink)
                    continue
                for comment in post.comments:
                    if str(comment.author) == 'arxiv_abstract_bot':
                        break
                else:
                    response = scrape_arxiv(arxiv_id)
                    post.reply(response)
                    cache.set(post.id, 'T')
                    print "Parsed post: %s"%(post.permalink)
                    print(arxiv_id, response)
                    time.sleep(10)
    except Exception as error:
        print(error)


def get_memcache_client():
    # Store IDs of comments that the bot has already replied to.
    # Read local cache by default

    MEMCACHEDCLOUD_SERVERS = os.environ.get('MEMCACHEDCLOUD_SERVERS')
    MEMCACHEDCLOUD_USERNAME = os.environ.get('MEMCACHEDCLOUD_USERNAME')
    MEMCACHEDCLOUD_PASSWORD = os.environ.get('MEMCACHEDCLOUD_PASSWORD')

    client = bmemcached.Client((MEMCACHEDCLOUD_SERVERS,), MEMCACHEDCLOUD_USERNAME,
                           MEMCACHEDCLOUD_PASSWORD)
    return client


if __name__ == "__main__":
    cache = get_memcache_client()

    while True:
        comment(cache)
        time.sleep(30)
