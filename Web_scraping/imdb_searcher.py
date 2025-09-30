import re
from typing import Dict, Optional
import difflib

class ImprovedIMDbScraper:
    def __init__(self, ddgs):
        self.ddgs = ddgs

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

