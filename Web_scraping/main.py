import requests
from bs4 import BeautifulSoup

# Step 1: Get a random Wikipedia page
url ={
    "example": "https://www.example.com",   
    "bbc": "https://www.bbc.co.uk/news",
    "amazon": "https://www.amazon.co.uk",
    "imdb": "https://www.imdb.com/"
}


headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

for name,url in url.items():
    print(f"Scraping {name}:{url}")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(f"Status: {response.status_code} for {name}")
    soup = BeautifulSoup(response.text, "lxml")
    soup.prettify()
    with open(f"{name}_summary.txt", "w", encoding="utf-8") as f:
        title = soup.title.string if soup.title else 'No title'
        f.write("Title: " f"{title}""\n")
        f.write(soup.get_text()[:500])
        #Extract all the anchor tags
        anchors = soup.find_all('a')
        
        f.write("Anchors:" f"{anchors}""\n" )
        # extract href from anchor tags with thier text
        f.write(f"{[(anchor.text, anchor.get('href')) for anchor in anchors]}" )
        # f.write("Hrefs:" f"{[anchor.get('href') for anchor in anchors]}" )
        
        
# # Step 2: Parse the HTML
# soup = soup.prettify()
# with open("output.html", "w", encoding="utf-8") as f:
#     f.write(str(soup))  
#     print("Saved the HTML to output.html")

# Step 3: Extract the title (<h1>)
# Extract the title (<h1>)
# title = soup.find("h1", {"id": "firstHeading"}).get_text(strip=True)

# # Extract the first paragraph (avoid empty ones)
# paragraph = None
# for p in soup.select("div.mw-parser-output > p"):
#     if p.get_text(strip=True):
#         paragraph = p.get_text(strip=True)
#         break

# # Step 3: Save to a text file
# with open("wiki_summary.txt", "w", encoding="utf-8") as f:
#     f.write(f"Title: {title}\n\n")
#     f.write(f"Summary: {paragraph}\n")

# print("Saved random Wikipedia article summary to wiki_summary.txt")