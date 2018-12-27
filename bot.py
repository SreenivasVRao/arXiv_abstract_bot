import praw
import requests
import bs4
import html2text
import time, os


def get_bot():
    PRAW_CLIENT_ID = os.environ.get('PRAW_CLIENT_ID')
    PRAW_CLIENT_SECRET = os.environ.get('PRAW_CLIENT_SECRET')
    PRAW_PASSWORD = os.environ.get('PRAW_PASSWORD')
    PRAW_USERNAME = os.environ.get('PRAW_USERNAME')
    PRAW_USERAGENT = os.environ.get('PRAW_USERAGENT')
    print PRAW_USERAGENT, PRAW_CLIENT_SECRET, PRAW_CLIENT_ID, PRAW_PASSWORD, PRAW_USERNAME
    return praw.Reddit(
        username=PRAW_USERNAME,
        password=PRAW_PASSWORD,
        client_id=PRAW_CLIENT_ID,
        client_secret=PRAW_CLIENT_SECRET,
        user_agent=PRAW_USERAGENT
        )


r = get_bot()

subreddit = r.subreddit('pythonforengineers')

alreadydone = set()


def scrape_arxiv(url):
    r = requests.get(url)
    soup = bs4.BeautifulSoup(r.text)
    abstract = soup.select('.abstract')[0]
    abstract = html2text.html2text(abstract.decode()).replace('\n', ' ')

    authors = soup.select('.authors')[0]
    authors = html2text.html2text(authors.decode()).replace('\n', ' ')
    authors = authors.replace('(/', '(http://arxiv.org/')

    title = soup.select('.title')[0]
    title =  html2text.html2text(title.decode()).replace('\n', ' ')[2:]

    abs_link = u'[Landing page]({})'.format(url)
    pdf_url = url.replace('/abs/', '/pdf/')
    pdf_link = u'[PDF link]({})'.format(pdf_url)
    links = u'{}  {}'.format(pdf_link, abs_link)
    response = '\n\n'.join([title, authors, abstract, links]) 
    return response


def comment():
    print(time.asctime(), "searching")
    try:
        all_posts = subreddit.new(limit=100)
        for post in all_posts:
            if 'arxiv.org' in post.url:
                if post.id in alreadydone:
                    continue
                for comment in post.comments:
                    if str(comment.author) == 'arxiv_abstract_bot':
                        break
                else:
                    landing_url = post.url
                    if '.pdf' in landing_url:
                        landing_url = post.url.replace('.pdf', '')
                        landing_url = landing_url.replace('/pdf/', '/abs/')

                    response = scrape_arxiv(landing_url)
                    post.reply(response)
                    alreadydone.add(post.id)
                    print(landing_url, response)
                    time.sleep(10)
    except Exception as error:
        print(error)


if __name__ == "__main__":

    while True:
        comment()
        time.sleep(30)
