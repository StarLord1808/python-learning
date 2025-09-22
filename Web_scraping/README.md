# Complete Web Scraping Learning Guide

## Phase 1: HTML Fundamentals (Days 1-2)

### What is HTML?
HTML (HyperText Markup Language) is the skeleton of web pages. Think of it as the structure that holds everything together.

### Key HTML Concepts for Scrapers

#### 1. Tags and Elements
```html
<tagname attribute="value">Content</tagname>
```

**Most Important Tags for Scraping:**
- `<div>` - Generic container (most common)
- `<p>` - Paragraphs of text
- `<span>` - Inline text container
- `<h1>, <h2>, <h3>` - Headings
- `<a>` - Links (href attribute has URLs)
- `<img>` - Images (src attribute has image URLs)
- `<table>, <tr>, <td>` - Tables and their rows/cells
- `<ul>, <ol>, <li>` - Lists and list items

#### 2. Attributes (Your Scraping Targets)
```html
<div id="unique-identifier" class="reusable-style" data-custom="value">
    Content here
</div>
```

**Key Attributes:**
- `id` - Unique identifier (only one per page)
- `class` - Reusable style/category (multiple elements can share)
- `data-*` - Custom data attributes
- `href` - Links in `<a>` tags
- `src` - Sources in `<img>` tags

#### 3. HTML Structure (Nesting)
```html
<html>
  <head>
    <title>Page Title</title>
  </head>
  <body>
    <div class="container">
      <h1 id="main-title">Welcome</h1>
      <div class="content">
        <p class="intro">First paragraph</p>
        <p class="intro">Second paragraph</p>
      </div>
    </div>
  </body>
</html>
```

### 🎯 Practice Exercise 1: HTML Reading
**Task:** Open any website, right-click → "View Page Source"
1. Find the `<title>` tag
2. Look for `<div>` elements with classes
3. Find all `<p>` tags
4. Identify elements with `id` attributes

---

## Phase 2: CSS Selectors (Days 2-3)

### Why CSS Selectors Matter
CSS selectors are how you tell your scraper "get THIS specific element." They're like addresses for HTML elements.

### Essential CSS Selectors

#### 1. Basic Selectors
```css
/* Tag selector - gets all <p> tags */
p

/* Class selector - gets elements with class="intro" */
.intro

/* ID selector - gets element with id="main-title" */
#main-title

/* Attribute selector - gets elements with specific attributes */
[data-id="123"]
```

#### 2. Descendant Selectors (Parent > Child)
```css
/* Gets all <p> tags inside .content */
.content p

/* Gets direct children only (immediate descendants) */
.content > p

/* Gets the first <p> child */
.content > p:first-child

/* Gets the last <p> child */
.content > p:last-child
```

#### 3. Multiple Conditions
```css
/* Element with BOTH classes */
.intro.highlight

/* Elements with EITHER class */
.intro, .highlight

/* Specific attribute values */
a[href*="github.com"]  /* href contains "github.com" */
img[src$=".jpg"]       /* src ends with ".jpg" */
div[class^="post"]     /* class starts with "post" */
```

### 🎯 Practice Exercise 2: Browser Dev Tools
**Task:** Open any news website
1. Right-click → "Inspect Element" (F12)
2. Try these in the Console tab:
```javascript
// Select by class
document.querySelectorAll('.headline')

// Select by tag
document.querySelectorAll('h2')

// Select by ID
document.querySelector('#main-content')
```
3. Hover over results to see them highlight on the page

---

## Phase 3: Browser Developer Tools (Day 3)

### Your Scraper's Best Friend
Dev tools show you exactly what your scraper sees and help debug issues.

### Key Dev Tools Features

#### 1. Elements Tab
- **Inspect**: Right-click any element → Inspect
- **Find**: Ctrl+F to search HTML
- **Copy selector**: Right-click element → Copy → Copy selector

#### 2. Network Tab
- Shows all requests (HTML, CSS, JS, images, API calls)
- Filter by type (XHR for AJAX requests)
- See request headers and responses

#### 3. Console Tab
- Test CSS selectors live
- See JavaScript errors
- Execute code snippets

### 🎯 Practice Exercise 3: Network Analysis
**Task:** Go to a shopping website (Amazon, eBay)
1. Open Network tab (F12 → Network)
2. Refresh the page
3. Look for:
   - The main HTML request
   - Any XHR/Fetch requests (these often contain data)
   - Large response sizes (might be JSON data)

---

## Phase 4: Static Scraping with BeautifulSoup (Days 4-5)

### Your First Real Scraper

```python
import requests
from bs4 import BeautifulSoup

# Basic template
def scrape_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raises exception for bad status codes
    
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup
```

### BeautifulSoup Methods You'll Use Daily

#### 1. Finding Elements
```python
# Find first matching element
title = soup.find('h1')
main_content = soup.find('div', {'class': 'content'})
specific_id = soup.find('div', {'id': 'main'})

# Find all matching elements
all_paragraphs = soup.find_all('p')
all_links = soup.find_all('a', {'class': 'external'})

# CSS selectors (more powerful)
headlines = soup.select('.headline')
first_paragraph = soup.select('.content > p:first-child')
```

#### 2. Extracting Data
```python
# Get text content
title_text = soup.find('h1').get_text(strip=True)

# Get attribute values
link_url = soup.find('a')['href']
image_src = soup.find('img').get('src')  # Safer - returns None if not found

# Get HTML content
raw_html = str(soup.find('div'))
```

### 🎯 Practice Exercise 4: News Scraper
**Task:** Build a scraper for a news website
```python
import requests
from bs4 import BeautifulSoup

def scrape_news():
    url = "https://news.ycombinator.com"  # Start with Hacker News - scraper-friendly
    
    soup = scrape_page(url)
    
    # Find all story titles
    stories = soup.find_all('span', {'class': 'titleline'})
    
    for story in stories[:10]:  # First 10 stories
        title = story.find('a').get_text(strip=True)
        link = story.find('a')['href']
        print(f"Title: {title}")
        print(f"Link: {link}")
        print("-" * 50)

scrape_news()
```

---

## Phase 5: Handling Forms and Sessions (Day 6)

### When Simple GET Requests Aren't Enough

#### 1. Sessions (Staying Logged In)
```python
import requests
from bs4 import BeautifulSoup

# Create session to maintain cookies
session = requests.Session()

# Login
login_data = {
    'username': 'your_username',
    'password': 'your_password'
}
session.post('https://example.com/login', data=login_data)

# Now all subsequent requests maintain login
response = session.get('https://example.com/protected-page')
```

#### 2. Handling Forms
```python
def scrape_with_form_submission():
    session = requests.Session()
    
    # Get the form page first
    response = session.get('https://example.com/search')
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find hidden form fields (important!)
    form = soup.find('form')
    hidden_inputs = form.find_all('input', {'type': 'hidden'})
    
    form_data = {}
    for hidden in hidden_inputs:
        form_data[hidden['name']] = hidden['value']
    
    # Add your search data
    form_data['search_query'] = 'python programming'
    
    # Submit form
    results = session.post('https://example.com/search', data=form_data)
    return BeautifulSoup(results.text, 'html.parser')
```

---

## Phase 6: JavaScript and Dynamic Content (Days 7-8)

### When BeautifulSoup Isn't Enough

#### Signs You Need JavaScript Handling:
- Content loads after page loads (spinning wheels)
- "Load more" buttons
- Infinite scroll
- Single Page Applications (React, Vue, Angular)

#### Solution: Selenium or Playwright

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_dynamic_content():
    # Setup Chrome driver
    driver = webdriver.Chrome()
    
    try:
        driver.get('https://example.com')
        
        # Wait for specific element to load
        wait = WebDriverWait(driver, 10)
        content = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "dynamic-content"))
        )
        
        # Now scrape like normal
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract data
        results = soup.find_all('div', {'class': 'result'})
        return results
        
    finally:
        driver.quit()
```

### 🎯 Practice Exercise 5: Dynamic Content
**Task:** Try scraping a site with infinite scroll (Twitter, Instagram, Reddit)
1. First try with requests/BeautifulSoup - see what you get
2. Then try with Selenium - see the difference

---

## Phase 7: Advanced Techniques (Days 9-10)

### 1. Rate Limiting and Politeness
```python
import time
import random

def polite_scraper(urls):
    for url in urls:
        # Random delay between requests
        time.sleep(random.uniform(1, 3))
        
        try:
            response = requests.get(url)
            # Process response
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")
            continue
```

### 2. Handling Different Response Types
```python
def smart_scraper(url):
    response = requests.get(url)
    
    # Check content type
    content_type = response.headers.get('content-type', '')
    
    if 'application/json' in content_type:
        # It's JSON data
        return response.json()
    elif 'text/html' in content_type:
        # It's HTML
        return BeautifulSoup(response.text, 'html.parser')
    else:
        # Something else (PDF, image, etc.)
        return response.content
```

### 3. Error Handling and Retries
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_resilient_session():
    session = requests.Session()
    
    # Define retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # Mount adapter
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
```

---

## Phase 8: Real-World Project (Days 10-14)

### Build a Complete Scraper

**Project: Job Listings Aggregator**
1. Scrape job sites (Indeed, LinkedIn, etc.)
2. Handle pagination
3. Store data in CSV/database
4. Handle rate limiting
5. Monitor for changes

```python
import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_jobs(self, search_term, pages=5):
        jobs = []
        
        for page in range(1, pages + 1):
            print(f"Scraping page {page}...")
            page_jobs = self.scrape_page(search_term, page)
            jobs.extend(page_jobs)
            time.sleep(2)  # Be polite
        
        return jobs
    
    def scrape_page(self, search_term, page):
        # Implementation depends on target site
        pass
    
    def save_to_csv(self, jobs, filename):
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            if jobs:
                writer = csv.DictWriter(file, fieldnames=jobs[0].keys())
                writer.writeheader()
                writer.writerows(jobs)

# Usage
scraper = JobScraper()
jobs = scraper.scrape_jobs('python developer')
scraper.save_to_csv(jobs, f'jobs_{datetime.now().strftime("%Y%m%d")}.csv')
```

---

## Common Pitfalls and Solutions

### 1. Getting Blocked
**Problem:** 403 Forbidden, CAPTCHA, or empty responses
**Solutions:**
- Add realistic User-Agent headers
- Use rotating proxies
- Add delays between requests
- Respect robots.txt

### 2. Dynamic Content Not Loading
**Problem:** Missing data that you can see in browser
**Solutions:**
- Check Network tab for AJAX requests
- Use Selenium/Playwright
- Find API endpoints directly

### 3. Inconsistent Data
**Problem:** Sometimes data is there, sometimes not
**Solutions:**
- Use `.get()` method instead of direct access
- Check if element exists before extracting
- Handle exceptions gracefully

### 4. Performance Issues
**Problem:** Scraper is too slow
**Solutions:**
- Use asyncio/aiohttp for concurrent requests
- Cache responses
- Target specific data endpoints instead of full pages

---

## Next Steps and Advanced Topics

### Tools to Explore Later:
1. **Scrapy** - Industrial-strength scraping framework
2. **Playwright** - Modern alternative to Selenium
3. **aiohttp** - Async HTTP requests
4. **Proxy rotation services**
5. **Browser automation at scale**

### Legal and Ethical Considerations:
1. Always check `robots.txt`
2. Respect rate limits
3. Don't overload servers
4. Check terms of service
5. Consider data privacy laws

Ready to start? Pick a phase and let me know when you want to dive deeper into any section!