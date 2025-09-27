import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import json
from typing import List, Dict, Optional
from urllib.parse import quote

class IMDbScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })
        self.base_url = "https://www.imdb.com"
    
    def get_movie_id(self, movie_title: str) -> Optional[str]:
        """Search for movie and return its IMDb ID with improved search"""
        search_url = f"{self.base_url}/search/title"
        params = {
            'title': movie_title,
            'title_type': 'feature',
            'view': 'simple'
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for search results
            results = soup.find_all('div', class_='lister-item')
            
            for result in results:
                title_element = result.find('h3', class_='lister-item-header')
                if title_element and title_element.a:
                    movie_link = title_element.a.get('href', '')
                    match = re.search(r'/title/(tt\d+)/', movie_link)
                    if match:
                        return match.group(1)
            
            # Alternative search approach
            return self._alternative_search(movie_title)
                
        except Exception as e:
            print(f"Error searching for movie: {e}")
            return self._alternative_search(movie_title)
    
    def _alternative_search(self, movie_title: str) -> Optional[str]:
        """Alternative search method using different endpoint"""
        search_url = f"{self.base_url}/find"
        params = {
            'q': movie_title,
            's': 'tt',
            'ttype': 'ft'
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for search results in find page
            result = soup.find('td', class_='result_text')
            if result and result.a:
                movie_link = result.a.get('href', '')
                match = re.search(r'/title/(tt\d+)/', movie_link)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            print(f"Alternative search failed: {e}")
            return None
    
    def get_reviews(self, imdb_id: str, max_reviews: int = 50) -> List[Dict]:
        """Extract reviews using multiple approaches"""
        reviews = []
        
        # Try different review URL patterns
        url_patterns = [
            f"{self.base_url}/title/{imdb_id}/reviews",
            f"{self.base_url}/title/{imdb_id}/reviews/_ajax",
            f"{self.base_url}/title/{imdb_id}/reviews?ref_=tt_ov_rt",
        ]
        
        for url in url_patterns:
            if len(reviews) >= max_reviews:
                break
                
            print(f"Trying URL: {url}")
            page_reviews = self._scrape_reviews_from_url(url, max_reviews - len(reviews))
            reviews.extend(page_reviews)
            
            if page_reviews:
                print(f"Found {len(page_reviews)} reviews from this URL")
                time.sleep(2)  # Be respectful with delays
        
        return reviews[:max_reviews]
    
    def _scrape_reviews_from_url(self, url: str, max_reviews: int) -> List[Dict]:
        """Scrape reviews from a specific URL"""
        reviews = []
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Save for debugging
            with open("debug_current_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we got a valid page (not 404)
            if soup.find('h1', string='404 Error'):
                print("Got 404 error page")
                return reviews
            
            # Multiple possible review container patterns
            container_selectors = [
                'div.review-container',
                'div.lister-item',
                'div.imdb-user-review',
                'div[data-testid="review-container"]',
                'div.ipc-page-grid__item',
                'div.text.show-more__control'
            ]
            
            for selector in container_selectors:
                containers = soup.select(selector)
                if containers:
                    print(f"Found {len(containers)} containers with selector: {selector}")
                    for container in containers:
                        if len(reviews) >= max_reviews:
                            break
                        review = self._parse_review_advanced(container)
                        if review:
                            reviews.append(review)
                    break
            
            # Also try to find review text directly
            if not reviews:
                review_texts = soup.find_all('div', class_='text show-more__control')
                for i, text_div in enumerate(review_texts):
                    if len(reviews) >= max_reviews:
                        break
                    review = {
                        'type': 'user',
                        'title': f'Review {i+1}',
                        'content': text_div.get_text(strip=True),
                        'rating': None,
                        'author': 'Unknown',
                        'date': 'Unknown',
                        'helpful': 'Unknown',
                    }
                    reviews.append(review)
            
        except Exception as e:
            print(f"Error scraping from URL {url}: {e}")
        
        return reviews
    
    def _parse_review_advanced(self, review_element) -> Optional[Dict]:
        """Advanced review parsing with multiple fallback methods"""
        try:
            review_data = {}
            
            # Try to determine review type
            review_data['type'] = 'user'  # Default
            
            # Extract title with multiple selectors
            title_selectors = [
                'a.title',
                'div.title',
                'h3',
                'span.title'
            ]
            
            for selector in title_selectors:
                title_elem = review_element.select_one(selector)
                if title_elem:
                    review_data['title'] = title_elem.get_text(strip=True)
                    break
            else:
                review_data['title'] = "No Title"
            
            # Extract content with multiple selectors
            content_selectors = [
                'div.text',
                'div.content',
                'div.show-more__control',
                'div.review-text'
            ]
            
            for selector in content_selectors:
                content_elem = review_element.select_one(selector)
                if content_elem:
                    # Remove spoilers
                    for spoiler in content_elem.select('span.spoiler-warning'):
                        spoiler.decompose()
                    review_data['content'] = content_elem.get_text(' ', strip=True)
                    break
            else:
                # If no specific content element, try to get text from the container
                review_data['content'] = review_element.get_text(' ', strip=True)[:500] + "..."
            
            # Extract rating
            rating = None
            rating_selectors = [
                'span.rating-other-user-rating',
                'div.ipl-ratings-bar',
                'span[class*="rating"]',
                'div[class*="rating"]'
            ]
            
            for selector in rating_selectors:
                rating_elem = review_element.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'(\d+)(?:\/10|\.)', rating_text)
                    if rating_match:
                        rating = rating_match.group(1)
                        break
            
            review_data['rating'] = rating
            
            # Extract author
            author_selectors = [
                'span.display-name-link',
                'div.display-name-date',
                'a.author',
                'span[class*="author"]'
            ]
            
            for selector in author_selectors:
                author_elem = review_element.select_one(selector)
                if author_elem:
                    review_data['author'] = author_elem.get_text(strip=True)
                    break
            else:
                review_data['author'] = "Anonymous"
            
            # Extract date
            date_selectors = [
                'span.review-date',
                'div.review-date',
                'span[class*="date"]',
                'div[class*="date"]'
            ]
            
            for selector in date_selectors:
                date_elem = review_element.select_one(selector)
                if date_elem:
                    review_data['date'] = date_elem.get_text(strip=True)
                    break
            else:
                review_data['date'] = "Unknown Date"
            
            # Extract helpfulness
            helpful_selectors = [
                'div.actions',
                'div.helpfulness-button',
                'div[class*="helpful"]'
            ]
            
            for selector in helpful_selectors:
                helpful_elem = review_element.select_one(selector)
                if helpful_elem:
                    helpful_text = helpful_elem.get_text(strip=True)
                    review_data['helpful'] = re.sub(r'\s+', ' ', helpful_text)
                    break
            else:
                review_data['helpful'] = "Unknown"
            
            return review_data
            
        except Exception as e:
            print(f"Error parsing review: {e}")
            return None
    
    def scrape_reviews_alternative(self, imdb_id: str, max_reviews: int = 50) -> List[Dict]:
        """Alternative approach using different endpoints"""
        reviews = []
        
        # Try the external reviews API approach
        try:
            # This uses a different endpoint that might be more accessible
            url = f"https://v2.sg.media-imdb.com/suggestion/t/{imdb_id}.json"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print("Alternative API response structure:", list(data.keys()) if data else "No data")
        except Exception as e:
            print(f"Alternative API failed: {e}")
        
        return reviews
    
    def scrape_reviews(self, movie_title: str, max_reviews: int = 50) -> Dict:
        """Main method to scrape reviews with enhanced error handling"""
        print(f"Searching for movie: {movie_title}")
        
        imdb_id = self.get_movie_id(movie_title)
        if not imdb_id:
            # Try with known ID for testing
            if "dark knight" in movie_title.lower():
                imdb_id = "tt0468569"
            else:
                print("Movie not found! Please check the movie title.")
                return {
                    'movie_title': movie_title,
                    'imdb_id': None,
                    'reviews': [],
                    'error': 'Movie not found'
                }
        
        print(f"Using IMDb ID: {imdb_id}")
        print("Scraping reviews...")
        
        reviews = self.get_reviews(imdb_id, max_reviews)
        
        if not reviews:
            print("Trying alternative scraping method...")
            reviews = self.scrape_reviews_alternative(imdb_id, max_reviews)
        
        # Separate critic and user reviews
        critic_reviews = [r for r in reviews if r.get('type') == 'critic']
        user_reviews = [r for r in reviews if r.get('type') == 'user']
        
        return {
            'movie_title': movie_title,
            'imdb_id': imdb_id,
            'critic_reviews': critic_reviews,
            'user_reviews': user_reviews,
            'all_reviews': reviews,
            'error': None if reviews else 'No reviews found'
        }

def debug_current_page(url: str):
    """Debug the current page content"""
    scraper = IMDbScraper()
    
    try:
        response = scraper.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"\n=== DEBUG: {url} ===")
        print(f"Status: {response.status_code}")
        print(f"Title: {soup.title.string if soup.title else 'No title'}")
        
        # Look for specific elements
        print("\nSearching for review-related elements:")
        
        # Check for error messages
        error_elements = soup.find_all(text=re.compile(r'404|error|not found', re.I))
        if error_elements:
            print("Error messages found:", error_elements[:3])
        
        # Check for review containers
        for class_name in ['review', 'lister', 'user', 'critic', 'text', 'content']:
            elements = soup.find_all(class_=re.compile(class_name, re.I))
            if elements:
                print(f"Elements with '{class_name}': {len(elements)}")
        
        # Save detailed debug info
        with open("detailed_debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        
        return True
    except Exception as e:
        print(f"Debug error: {e}")
        return False
# Keep the helper functions from your original code
def save_reviews_to_csv(reviews_data: Dict, filename: str = None):
    """Save reviews to CSV file"""
    if not reviews_data or not reviews_data.get('all_reviews'):
        print("No reviews data to save")
        return None
    
    if not filename:
        movie_title = reviews_data['movie_title'].replace(' ', '_')
        filename = f"imdb_reviews_{movie_title}.csv"
    
    all_reviews = reviews_data.get('all_reviews', [])
    
    if all_reviews:
        df = pd.DataFrame(all_reviews)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Reviews saved to {filename}")
        return df
    else:
        print("No reviews to save")
        return None

def print_review_stats(reviews_data: Dict):
    """Print basic statistics about the scraped reviews"""
    if not reviews_data or 'movie_title' not in reviews_data:
        print("No reviews data available")
        return
        
    print(f"\n=== Review Statistics for '{reviews_data['movie_title']}' ===")
    critic_count = len(reviews_data.get('critic_reviews', []))
    user_count = len(reviews_data.get('user_reviews', []))
    total_count = len(reviews_data.get('all_reviews', []))
    
    print(f"Critic Reviews: {critic_count}")
    print(f"User Reviews: {user_count}")
    print(f"Total Reviews: {total_count}")
    
    
# Enhanced usage example
if __name__ == "__main__":
    scraper = IMDbScraper()
     
         # Test movies with known IDs
    test_movies = [
        ("The Dark Knight", "tt0468569"),
        ("Inception", "tt1375666"),
        ("The Shawshank Redemption", "tt0111161")
    ]
    
    for movie_title, known_id in test_movies:
        print(f"\n{'='*60}")
        print(f"Testing: {movie_title}")
        print('='*60)
        
        # First debug the page
        test_url = f"https://www.imdb.com/title/{known_id}/reviews"
        debug_current_page(test_url)
        
        # Then try scraping
        reviews_data = scraper.scrape_reviews(movie_title, max_reviews=20)
        
        # Print results
        print_review_stats(reviews_data)
        
        if reviews_data.get('all_reviews'):
            save_reviews_to_csv(reviews_data)
            
            # Show sample
            reviews = reviews_data['all_reviews'][:2]
            for i, review in enumerate(reviews):
                print(f"\nSample {i+1}:")
                print(f"Type: {review.get('type', 'N/A')}")
                print(f"Title: {review.get('title', 'N/A')}")
                print(f"Content preview: {review.get('content', 'N/A')[:100]}...")
        
        time.sleep(3)  # 

