from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import json
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import difflib
# from imdb_scraper import IMDbScraperDDGS

class ImprovedIMDbScraper:
    def __init__(self):
        self.ddgs = DDGS()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.base_url = "https://www.imdb.com"
    
    def improved_search_movie(self, movie_title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Improved movie search with better matching and year filtering"""
        try:
            print(f"🔍 Searching for: {movie_title} {f'({year})' if year else ''}")
            
            # More specific search query
            search_query = f'"{movie_title}" site:imdb.com/title/'
            if year:
                search_query += f' {year}'
            
            results = self.ddgs.text(search_query, max_results=10)
            
            best_match = None
            best_score = 0
            
            for result in results:
                if 'imdb.com/title/tt' in result['href']:
                    # Extract IMDb ID
                    match = re.search(r'imdb\.com/title/(tt\d+)', result['href'])
                    if not match:
                        continue
                    
                    # Calculate title similarity score
                    result_title = result['title'].lower()
                    # Remove common IMDb suffixes
                    result_title = re.sub(r'\s*[-–]\s*imdb.*$', '', result_title, flags=re.I)
                    result_title = re.sub(r'\s*\(\d{4}\).*$', '', result_title)
                    
                    # Use fuzzy matching to find best match
                    similarity = difflib.SequenceMatcher(None, 
                                                        movie_title.lower(), 
                                                        result_title.lower()).ratio()
                    
                    # Check year if provided
                    year_match = True
                    if year:
                        year_in_result = re.search(r'\((\d{4})\)', result['title'] + ' ' + result['body'])
                        if year_in_result:
                            year_match = (int(year_in_result.group(1)) == year)
                    
                    # Weight score
                    score = similarity
                    if year_match and year:
                        score += 0.3  # Bonus for year match
                    
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'imdb_id': match.group(1),
                            'title': movie_title,
                            'url': result['href'],
                            'description': result['body'],
                            'search_title': result['title'],
                            'match_score': score
                        }
            
            if best_match and best_score > 0.5:  # Minimum threshold
                print(f"✅ Found: {best_match['search_title']} (Score: {best_score:.2f})")
                return best_match
            else:
                print(f"❌ No good match found for '{movie_title}'")
                return None
                
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return None
    
    # def get_imdb_top_movies(self, limit: int = 250) -> List[Dict]:
    #     """Get IMDb Top 250 movies as a starting point"""
    #     movies = []
    #     try:
    #         url = "https://www.imdb.com/chart/top/"
    #         response = self.session.get(url)
    #         soup = BeautifulSoup(response.content, 'html.parser')
            
    #         # Find movie entries
    #         movie_links = soup.select('td.titleColumn a')
    #         year_elements = soup.select('td.titleColumn span.secondaryInfo')
            
    #         for i, (link, year_elem) in enumerate(zip(movie_links[:limit], year_elements[:limit])):
    #             title = link.get_text(strip=True)
    #             year_text = year_elem.get_text(strip=True)
    #             year = int(re.search(r'\d{4}', year_text).group()) if year_text else None
    #             imdb_id = re.search(r'/title/(tt\d+)/', link['href']).group(1)
                
    #             movies.append({
    #                 'title': title,
    #                 'year': year,
    #                 'imdb_id': imdb_id,
    #                 'rank': i + 1
    #             })
                
    #         print(f"✅ Found {len(movies)} top movies")
    #         return movies
            
    #     except Exception as e:
    #         print(f"❌ Error getting top movies: {e}")
    #         return []
    
    # def get_movies_by_genre(self, genre: str, limit: int = 50) -> List[Dict]:
    #     """Get popular movies by genre"""
    #     movies = []
    #     try:
    #         # Use DDGS to find popular movies in genre
    #         search_query = f'site:imdb.com/title/ {genre} movie popular'
    #         results = self.ddgs.text(search_query, max_results=limit)
            
    #         for result in results:
    #             if 'imdb.com/title/tt' in result['href']:
    #                 match = re.search(r'imdb\.com/title/(tt\d+)', result['href'])
    #                 if match:
    #                     title = re.sub(r'\s*[-–]\s*IMDb.*$', '', result['title'], flags=re.I)
    #                     movies.append({
    #                         'title': title,
    #                         'imdb_id': match.group(1),
    #                         'genre': genre
    #                     })
            
    #         print(f"✅ Found {len(movies)} {genre} movies")
    #         return movies
            
    #     except Exception as e:
    #         print(f"❌ Error getting {genre} movies: {e}")
    #         return []
    
    # def bulk_scrape_movies(self, 
    #                       movie_list: List[Dict], 
    #                       save_interval: int = 10,
    #                       delay_range: tuple = (2, 5)) -> List[Dict]:
    #     """
    #     Bulk scrape movies with progress saving and rate limiting
        
    #     Args:
    #         movie_list: List of dicts with 'title' and optionally 'year', 'imdb_id'
    #         save_interval: Save progress every N movies
    #         delay_range: Random delay range between requests (min, max) seconds
    #     """
    #     all_results = []
    #     failed_movies = []
        
    #     print(f"\n🎬 Starting bulk scrape of {len(movie_list)} movies")
    #     print("=" * 70)
        
    #     for i, movie_info in enumerate(movie_list, 1):
    #         try:
    #             print(f"\n[{i}/{len(movie_list)}] Processing: {movie_info.get('title')}")
                
    #             # If we already have IMDb ID, use it directly
    #             if movie_info.get('imdb_id'):
    #                 from_scraper = IMDbScraperDDGS()  # Use your original scraper
    #                 movie_data = from_scraper.get_movie_details(movie_info['imdb_id'])
    #             else:
    #                 # Search for movie first
    #                 search_result = self.improved_search_movie(
    #                     movie_info.get('title'),
    #                     movie_info.get('year')
    #                 )
                    
    #                 if search_result:
    #                     from_scraper = IMDbScraperDDGS()
    #                     movie_data = from_scraper.get_movie_details(search_result['imdb_id'])
    #                 else:
    #                     failed_movies.append(movie_info)
    #                     continue
                
    #             all_results.append(movie_data)
                
    #             # Save progress periodically
    #             if i % save_interval == 0:
    #                 self.save_progress(all_results, f"imdb_bulk_progress_{i}.json")
    #                 print(f"💾 Progress saved: {i} movies processed")
                
    #             # Random delay to avoid rate limiting
    #             delay = random.uniform(*delay_range)
    #             print(f"⏳ Waiting {delay:.1f} seconds...")
    #             time.sleep(delay)
                
    #         except Exception as e:
    #             print(f"❌ Error processing {movie_info.get('title')}: {e}")
    #             failed_movies.append(movie_info)
    #             continue
        
    #     # Final save
    #     self.save_progress(all_results, "imdb_bulk_final.json")
        
    #     if failed_movies:
    #         with open("failed_movies.json", 'w') as f:
    #             json.dump(failed_movies, f, indent=2)
    #         print(f"\n⚠️ {len(failed_movies)} movies failed. See failed_movies.json")
        
    #     print(f"\n✅ Bulk scraping complete: {len(all_results)} successful")
    #     return all_results
    
    # def save_progress(self, data: List[Dict], filename: str):
    #     """Save scraping progress to file"""
    #     with open(filename, 'w', encoding='utf-8') as f:
    #         json.dump(data, f, indent=2, ensure_ascii=False)
    
    # def get_all_genres(self) -> List[str]:
    #     """Get list of main movie genres"""
    #     return [
    #         'Action', 'Adventure', 'Animation', 'Biography', 'Comedy',
    #         'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy',
    #         'Film-Noir', 'History', 'Horror', 'Music', 'Musical',
    #         'Mystery', 'Romance', 'Sci-Fi', 'Sport', 'Thriller',
    #         'War', 'Western'
    #     ]


# Example usage for different scraping strategies
if __name__ == "__main__":
    scraper = ImprovedIMDbScraper()
    
    # Strategy 1: Test improved search with specific examples
    print("\n=== Testing Improved Search ===")
    test_cases = [
        ("The Dark Knight", 2008),  # Specific year helps
        ("The Dark Knight", None),   # Without year
        ("Inception", 2010),
        ("The Matrix", 1999)
    ]
    
    for title, year in test_cases:
        result = scraper.improved_search_movie(title, year)
        if result:
            print(f"  Found: {result['search_title']}")
    
    # Strategy 2: Scrape Top 250 movies (recommended approach)
    print("\n=== Getting Top Movies ===")
    top_movies = scraper.get_imdb_top_movies(limit=10)  # Start small
    
    # Strategy 3: Scrape by genres
    print("\n=== Getting Movies by Genre ===")
    action_movies = scraper.get_movies_by_genre("Action", limit=5)
    
    # Strategy 4: Bulk scrape with your existing scraper
    print("\n=== Bulk Scraping Example ===")
    movies_to_scrape = [
        {"title": "The Shawshank Redemption", "year": 1994},
        {"title": "The Godfather", "year": 1972},
        {"title": "The Dark Knight", "year": 2008},  # Now with year!
    ]
    
    # Uncomment to run bulk scrape
    # results = scraper.bulk_scrape_movies(movies_to_scrape, save_interval=2)
    
    # IMPORTANT: Better alternative - Use IMDb's official datasets
    print("\n" + "="*70)
    print("📌 RECOMMENDED APPROACH:")
    print("Instead of scraping all movies, consider using IMDb's official datasets:")
    print("https://www.imdb.com/interfaces/")
    print("These provide bulk data legally and efficiently!")
    print("="*70)