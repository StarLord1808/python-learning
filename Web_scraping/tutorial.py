import requests
# from bs4 import BeautifulSoup
from wiki_scraper import  scrape_page
import csv
def shorten_url(url):
    try:
        # TinyURL API endpoint
        response = requests.get(f"http://tinyurl.com/api-create.php?url={url}")
        if response.status_code == 200:
            return response.text  # returns the shortened URL as plain text
        else:
            return url  # fallback to original if failed
    except Exception as e:
        print(f"Error shortening URL: {e}")
        return url 

def scrape_news():
    url = "https://news.ycombinator.com"  # Start with Hacker News - scraper-friendly
    # print(url)
    soup = scrape_page(url)
    
    # Find all story titles
    stories = soup.find_all('span', {'class': 'titleline'})
    data=[]
    for story in stories[:10]:  # First 10 stories
        title = story.find('a').get_text(strip=True)
        link = story.find('a')['href']
        short_link = shorten_url(link)
        data.append({
            "Title": title,
            "Link": link,
            "Short Link": short_link
            })
    
    with open("ycombinator_stories.csv",'w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=["Title","Link","Short Link"])
            writer.writeheader()
            writer.writerows(data)
            # f.write(f"Title: {title},\nLink:{link}\nShortLink: {short_link}\n")

if __name__ == "__main__":
    scrape_news()