import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from typing import List, Dict, Optional

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
        })
        self.base_url = "https://www.imdb.com"
    
    def get_movie_id(self, movie_title: str) -> Optional[str]:
        """Search for movie and return its IMDb ID"""
        search_url = f"{self.base_url}/find"
        params = {
            'q': movie_title,
            's': 'tt',
            'ttype': 'ft',
            'ref_': 'fn_ft'
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the first search result
            result = soup.find('td', class_='result_text')
            if result and result.a:
                movie_link = result.a.get('href', '')
                # Extract IMDb ID from URL (e.g., /title/tt0468569/)
                match = re.search(r'/title/(tt\d+)/', movie_link)
                if match:
                    return match.group(1)
            
            return None
                
        except Exception as e:
            print(f"Error searching for movie: {e}")
            return None
    
    def get_reviews(self, imdb_id: str, max_reviews: int = 50, review_type: str = "all") -> List[Dict]:
        """Extract reviews from IMDb - combined function for both types"""
        reviews = []
        start = 0
        
        while len(reviews) < max_reviews:
            url = f"{self.base_url}/title/{imdb_id}/reviews"
            params = {
                'sort': 'helpfulnessScore',
                'dir': 'desc',
                'ratingFilter': 0
            }
            
            if start > 0:
                params['start'] = start
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find review containers - updated class names
                review_containers = soup.find_all('div', class_=lambda x: x and 'review-container' in x)
                
                if not review_containers:
                    review_containers = soup.find_all('div', class_='lister-item')
                
                if not review_containers:
                    print("No review containers found")
                    break
                
                new_reviews_count = 0
                for container in review_containers:
                    if len(reviews) >= max_reviews:
                        break
                    
                    review_data = self._parse_review(container)
                    if review_data:
                        # Filter by type if requested
                        if review_type == "all" or review_data['type'] == review_type:
                            reviews.append(review_data)
                            new_reviews_count += 1
                
                if new_reviews_count == 0:
                    print("No new reviews parsed from this page")
                    break
                
                # Check for next page
                load_more = soup.find('div', class_='load-more-data')
                if not load_more:
                    break
                    
                # Get the next start parameter from data-key
                next_start = load_more.get('data-key')
                if not next_start:
                    break
                    
                start = int(next_start)
                print(f"Loading more reviews... (start: {start})")
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error fetching reviews: {e}")
                break
        
        return reviews
    
    def _parse_review(self, review_element) -> Optional[Dict]:
        """Parse individual review elements with updated selectors"""
        try:
            # Determine review type
            is_critic = bool(review_element.find('span', class_=lambda x: x and 'critic' in x.lower()))
            review_type = 'critic' if is_critic else 'user'
            
            # Extract title
            title_element = review_element.find('a', class_='title')
            if not title_element:
                title_element = review_element.find('div', class_='title')
            title = title_element.get_text(strip=True) if title_element else "No Title"
            
            # Extract content
            content_element = review_element.find('div', class_='text')
            if not content_element:
                content_element = review_element.find('div', class_='content')
            if content_element:
                # Remove spoiler elements if present
                for spoiler in content_element.find_all('span', class_='spoiler-warning'):
                    spoiler.decompose()
                content = content_element.get_text(' ', strip=True)
            else:
                content = "No Content"
            
            # Extract rating
            rating = None
            rating_element = review_element.find('span', class_='rating-other-user-rating')
            if rating_element:
                rating_spans = rating_element.find_all('span')
                if rating_spans:
                    rating = rating_spans[0].get_text(strip=True)
            else:
                # Alternative rating location
                rating_element = review_element.find('div', class_='ipl-ratings-bar')
                if rating_element:
                    rating_text = rating_element.get_text(strip=True)
                    rating_match = re.search(r'(\d+)/10', rating_text)
                    if rating_match:
                        rating = rating_match.group(1)
            
            # Extract author
            author_element = review_element.find('span', class_='display-name-link')
            if not author_element:
                author_element = review_element.find('div', class_='display-name-date')
            author = author_element.get_text(strip=True) if author_element else "Anonymous"
            
            # Extract date
            date_element = review_element.find('span', class_='review-date')
            if not date_element:
                date_element = review_element.find('div', class_='review-date')
            date = date_element.get_text(strip=True) if date_element else "Unknown Date"
            
            # Extract helpfulness
            helpful_element = review_element.find('div', class_='actions')
            if not helpful_element:
                helpful_element = review_element.find('div', class_='helpfulness-button')
            helpful_text = helpful_element.get_text(strip=True) if helpful_element else "0 out of 0 found this helpful"
            
            # Clean up helpful text
            helpful_text = re.sub(r'\s+', ' ', helpful_text)
            
            return {
                'type': review_type,
                'title': title,
                'content': content,
                'rating': rating,
                'author': author,
                'date': date,
                'helpful': helpful_text,
            }
            
        except Exception as e:
            print(f"Error parsing review: {e}")
            return None
    
    def scrape_reviews(self, movie_title: str, max_reviews: int = 50) -> Dict:
        """Main method to scrape reviews"""
        print(f"Searching for movie: {movie_title}")
        
        imdb_id = self.get_movie_id(movie_title)
        if not imdb_id:
            print("Movie not found! Please check the movie title.")
            return {
                'movie_title': movie_title,
                'imdb_id': None,
                'reviews': [],
                'error': 'Movie not found'
            }
        
        print(f"Found IMDb ID: {imdb_id}")
        print("Scraping reviews...")
        
        reviews = self.get_reviews(imdb_id, max_reviews)
        
        # Separate critic and user reviews
        critic_reviews = [r for r in reviews if r['type'] == 'critic']
        user_reviews = [r for r in reviews if r['type'] == 'user']
        
        return {
            'movie_title': movie_title,
            'imdb_id': imdb_id,
            'critic_reviews': critic_reviews,
            'user_reviews': user_reviews,
            'all_reviews': reviews,
            'error': None
        }

def debug_imdb_page(imdb_id: str):
    """Debug function to see what's actually on the page"""
    scraper = IMDbScraper()
    url = f"https://www.imdb.com/title/{imdb_id}/reviews"
    
    try:
        response = scraper.session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("\n=== DEBUG INFO ===")
        print(f"URL: {url}")
        print(f"Status Code: {response.status_code}")
        
        # Save HTML for inspection
        with open("debug_imdb.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("HTML saved to debug_imdb.html")
        
        # Look for review containers
        containers = soup.find_all('div', class_=True)
        review_containers = []
        
        for container in containers:
            classes = container.get('class', [])
            if any('review' in cls.lower() for cls in classes):
                review_containers.append(container)
                print(f"Found review container with classes: {classes}")
        
        print(f"Total review containers found: {len(review_containers)}")
        
        # Look for specific elements
        titles = soup.find_all('a', class_='title')
        print(f"Title elements found: {len(titles)}")
        
        contents = soup.find_all('div', class_='text')
        print(f"Content elements found: {len(contents)}")
        
        return True
        
    except Exception as e:
        print(f"Debug error: {e}")
        return False

def save_reviews_to_csv(reviews_data: Dict, filename: str = None):
    """Save reviews to CSV file"""
    if not reviews_data or not reviews_data.get('all_reviews'):
        print("No reviews data to save")
        return
    
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

# Example usage
if __name__ == "__main__":
    # Initialize the scraper
    scraper = IMDbScraper()
    
    # Test with The Dark Knight
    movie_title = "The Dark Knight"
    imdb_id = "tt0468569"  # Known IMDb ID for The Dark Knight
    
    print(f"\n{'='*60}")
    print(f"Scraping reviews for: {movie_title} (IMDb: {imdb_id})")
    print('='*60)
    
    # First, debug the page to see what's there
    debug_imdb_page(imdb_id)
    
    # Then try scraping
    reviews_data = scraper.scrape_reviews(movie_title, max_reviews=30)
    
    # Print statistics
    print_review_stats(reviews_data)
    
    # Save to CSV
    df = save_reviews_to_csv(reviews_data)
    
    # Display sample reviews if available
    if reviews_data.get('all_reviews'):
        reviews = reviews_data['all_reviews']
        print(f"\nFirst 3 reviews preview:")
        for i, review in enumerate(reviews[:3]):
            print(f"\n--- Review {i+1} ({review['type']}) ---")
            print(f"Title: {review['title']}")
            print(f"Author: {review['author']}")
            print(f"Rating: {review['rating']}")
            print(f"Date: {review['date']}")
            print(f"Preview: {review['content'][:150]}...")
    
    # Also try alternative approach with direct URL
    print(f"\n{'='*60}")
    print("Trying alternative approach...")
    print('='*60)
    
    # Alternative: Use the reviews export URL
    export_url = f"https://www.imdb.com/title/{imdb_id}/reviews/_ajax"
    try:
        response = scraper.session.get(export_url)
        with open("debug_ajax.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("AJAX response saved to debug_ajax.html")
    except Exception as e:
        print(f"Alternative approach failed: {e}")