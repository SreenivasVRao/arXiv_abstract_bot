import praw
import requests
import bs4
import html2text
import time


USERNAME = 'arXiv_abstract_bot'
PASSWORD = '********'
CLIENT_ID = '*******'
SECRET = '********'

r = praw.Reddit(
    username=USERNAME,
    password=PASSWORD,
    client_id=CLIENT_ID,
    client_secret=SECRET,
    user_agent='linux:arXiv_abstract_bot:0.2 (by /u/arXiv_abstract_bot)'
    )

subreddit = r.subreddit('machinelearning')

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
                    if str(comment.author) == USERNAME:
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

    # while True:
    #     comment()
    #     time.sleep(30)
