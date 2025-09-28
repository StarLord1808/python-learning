import requests
from bs4 import BeautifulSoup


headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def scrape_page(url: str):
    headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    # print(soup)
    return soup

def data_load(soup):
# Find all movie containers (each movie is in a div with class containing 'cli-children')
    movie_containers = soup.select('div.sc-15ac7568-0.jQHOho.cli-children')

    movies = []

    for container in movie_containers:
        # --- Title & Link ---
        title_link_tag = container.select_one('a.ipc-title-link-wrapper')
        if not title_link_tag:
            continue
        link = "https://www.imdb.com" + title_link_tag['href']
        full_title = title_link_tag.get_text(strip=True)  # e.g., "1. The Shawshank Redemption"

        # --- Year ---
        year_span = container.select_one('span.cli-title-metadata-item')
        year = year_span.get_text(strip=True) if year_span else "N/A"

        # --- Rating ---
        rating_span = container.select_one('span.ipc-rating-star--rating')
        rating = rating_span.get_text(strip=True) if rating_span else "N/A"

        # Optional: Extract just the title without rank
        # Example: "1. The Shawshank Redemption" → "The Shawshank Redemption"
        title_only = full_title.split('.', 1)[1].strip() if '.' in full_title else full_title

        movies.append({
            "title": title_only,
            "full_title_with_rank": full_title,
            "year": year,
            "rating": rating,
            "link": link
        })
    return movies
if __name__ =="__main__":
    url = 'https://www.imdb.com/chart/top/'
    soup = scrape_page(url)
    movies = data_load(soup)
    with open('Top_250_films.csv','w',encoding='utf-8') as f:
        for movie in movies:
            f.write(f"{movie['title']},{movie['year']},{movie['rating']},{movie['link']}\n")