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

class IMDbScraperDDGS:
    def __init__(self):
        self.ddgs = DDGS()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.base_url = "https://www.imdb.com"
    
    def search_movie(self, movie_title: str) -> Optional[Dict]:
        """Search for movie using DDGS and return movie information"""
        try:
            print(f"🔍 Searching for: {movie_title}")
            
            # Use DDGS text search
            results = self.ddgs.text(
                f"{movie_title} IMDb", 
                max_results=5
            )
            
            for result in results:
                if 'imdb.com/title/tt' in result['href']:
                    # Extract IMDb ID from URL
                    match = re.search(r'imdb\.com/title/(tt\d+)', result['href'])
                    if match:
                        imdb_id = match.group(1)
                        return {
                            'imdb_id': imdb_id,
                            'title': movie_title,
                            'url': result['href'],
                            'description': result['body'],
                            'search_title': result['title']
                        }
            
            print(f"❌ Movie '{movie_title}' not found in search results")
            return None
            
        except Exception as e:
            print(f"❌ Error searching for movie: {e}")
            return None
    
    def get_movie_details(self, imdb_id: str) -> Dict:
        """Extract comprehensive movie details from IMDb page"""
        try:
            print(f"🎬 Fetching movie details for {imdb_id}...")
            
            # Main movie page
            url = f"https://www.imdb.com/title/{imdb_id}/"
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            movie_data = {
                'imdb_id': imdb_id,
                'url': url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 1. Extract Title and Basic Info
            movie_data.update(self._extract_basic_info(soup))
            
            # 2. Extract Summary and Synopsis
            movie_data.update(self._extract_summary_synopsis(soup))
            
            # 3. Extract Cast
            movie_data.update(self._extract_cast(soup))
            
            # 4. Extract Storyline
            movie_data.update(self._extract_storyline(soup))
            
            # 5. Extract Motion Picture Rating
            movie_data.update(self._extract_ratings(soup))
            
            # 6. Extract Details (Genre, Release Date, etc.)
            movie_data.update(self._extract_details(soup))
            
            # 7. Extract Box Office Information
            movie_data.update(self._extract_box_office(soup))
            
            # 8. Extract Technical Specifications
            movie_data.update(self._extract_tech_specs(soup))
            
            return movie_data
            
        except Exception as e:
            print(f"❌ Error fetching movie details: {e}")
            return {'imdb_id': imdb_id, 'error': str(e)}
    
    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict:
        """Extract basic movie information"""
        data = {}
        
        try:
            # Title - multiple selectors
            title_selectors = [
                'h1[data-testid="hero__pageTitle"]',
                '.title_wrapper h1',
                'h1'
            ]
            
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title_text = title_element.get_text(strip=True)
                    # Clean title (remove year if present)
                    title_text = re.sub(r'\s*\(\d{4}\)', '', title_text)
                    data['title'] = title_text
                    break
            
            # Year
            year_element = soup.find('a', href=re.compile(r'releaseinfo'))
            if year_element:
                data['year'] = year_element.get_text(strip=True)
            else:
                # Extract from title or page
                year_match = re.search(r'\((\d{4})\)', str(soup))
                if year_match:
                    data['year'] = year_match.group(1)
            
            # Duration
            duration_selectors = [
                'li[data-testid="title-techspec_runtime"]',
                '.title_wrapper .subtext time'
            ]
            
            for selector in duration_selectors:
                duration_element = soup.select_one(selector)
                if duration_element:
                    data['duration'] = duration_element.get_text(strip=True)
                    break
            
            # IMDb Rating
            rating_selectors = [
                'div[data-testid="hero-rating-bar__aggregate-rating__score"]',
                '.imdbRating span[itemprop="ratingValue"]',
                '.ratingValue strong'
            ]
            
            for selector in rating_selectors:
                rating_element = soup.select_one(selector)
                if rating_element:
                    data['imdb_rating'] = rating_element.get_text(strip=True)
                    break
            
            # Rating Count
            count_selectors = [
                'div[data-testid="hero-rating-bar__aggregate-rating__score"] + div',
                '.imdbRating span[itemprop="ratingCount"]'
            ]
            
            for selector in count_selectors:
                count_element = soup.select_one(selector)
                if count_element:
                    count_text = count_element.get_text(strip=True)
                    count_match = re.search(r'([\d,]+)', count_text)
                    if count_match:
                        data['rating_count'] = count_match.group(1)
                    break
            
        except Exception as e:
            print(f"❌ Error extracting basic info: {e}")
        print(data)
        return data
    
    def _extract_summary_synopsis(self, soup: BeautifulSoup) -> Dict:
        """Extract summary and synopsis"""
        data = {}
        
        try:
            # Summary
            summary_selectors = [
                'span[data-testid="plot-l"]',
                '.summary_text',
                '.plot_summary .summary_text'
            ]
            
            for selector in summary_selectors:
                summary_element = soup.select_one(selector)
                if summary_element:
                    summary_text = summary_element.get_text(strip=True)
                    if summary_text and summary_text.lower() != 'add a plot':
                        data['summary'] = summary_text
                        break
            
            # Synopsis
            synopsis_selectors = [
                'div[data-testid="plot-xl"]',
                '.plot-synopsis',
                '.inline.canwrap p'
            ]
            
            for selector in synopsis_selectors:
                synopsis_element = soup.select_one(selector)
                if synopsis_element:
                    synopsis_text = synopsis_element.get_text(strip=True)
                    if synopsis_text and synopsis_text.lower() != 'add a plot':
                        data['synopsis'] = synopsis_text
                        break
            
            # If no synopsis, use summary
            if 'synopsis' not in data and 'summary' in data:
                data['synopsis'] = data['summary']
                
        except Exception as e:
            print(f"❌ Error extracting summary/synopsis: {e}")
        
        return data
    
    def _extract_cast(self, soup: BeautifulSoup) -> Dict:
        """Extract cast information"""
        data = {'cast': []}
        
        try:
            # Modern IMDb cast section
            cast_section = soup.find('div', {'data-testid': 'title-cast'})
            if cast_section:
                cast_items = cast_section.find_all('a', {'data-testid': 'title-cast-item__actor'})
                
                for item in cast_items[:20]:  # Limit to top 20
                    actor_name = item.get_text(strip=True)
                    
                    # Find character name
                    character_span = item.find_next('span', {'data-testid': 'title-cast-item__character'})
                    character_name = character_span.get_text(strip=True) if character_span else "Unknown"
                    
                    data['cast'].append({
                        'actor': actor_name,
                        'character': character_name
                    })
            else:
                # Legacy IMDb cast table
                cast_table = soup.find('table', class_='cast_list')
                if cast_table:
                    cast_rows = cast_table.find_all('tr')[1:]  # Skip header
                    for row in cast_rows[:20]:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            actor_cell = cells[1]
                            character_cell = cells[3]
                            
                            actor_link = actor_cell.find('a')
                            if actor_link:
                                actor_name = actor_link.get_text(strip=True)
                                character_name = character_cell.get_text(strip=True)
                                
                                # Clean character name
                                character_name = re.sub(r'\s+', ' ', character_name).strip()
                                
                                data['cast'].append({
                                    'actor': actor_name,
                                    'character': character_name
                                })
        
        except Exception as e:
            print(f"❌ Error extracting cast: {e}")
        
        return data
    
    def _extract_storyline(self, soup: BeautifulSoup) -> Dict:
        """Extract storyline information"""
        data = {'storyline': {}}
        
        try:
            # Plot summary
            plot_selectors = [
                'div[data-testid="storyline-plot-summary"]',
                '.plot_summary_wrapper'
            ]
            
            for selector in plot_selectors:
                plot_element = soup.select_one(selector)
                if plot_element:
                    plot_text = plot_element.get_text(strip=True)
                    if plot_text:
                        data['storyline']['plot_summary'] = plot_text
                        break
            
            # Genres
            genre_elements = soup.find_all('a', href=re.compile(r'genres='))
            if genre_elements:
                genres = []
                for elem in genre_elements:
                    genre_text = elem.get_text(strip=True)
                    if genre_text and genre_text not in genres:
                        genres.append(genre_text)
                data['storyline']['genres'] = genres
            
            # Keywords
            keyword_elements = soup.find_all('a', href=re.compile(r'keywords'))
            if keyword_elements:
                keywords = []
                for elem in keyword_elements:
                    keyword_text = elem.get_text(strip=True)
                    if keyword_text and keyword_text not in keywords:
                        keywords.append(keyword_text)
                data['storyline']['keywords'] = keywords
            
            # Tagline
            tagline_element = soup.find('div', class_='txt-block')
            if tagline_element and 'Tagline' in tagline_element.get_text():
                tagline_text = tagline_element.get_text().replace('Tagline:', '').strip()
                data['storyline']['tagline'] = tagline_text
                
        except Exception as e:
            print(f"❌ Error extracting storyline: {e}")
        
        return data
    
    def _extract_ratings(self, soup: BeautifulSoup) -> Dict:
        """Extract motion picture ratings"""
        data = {}
        
        try:
            # Content rating
            rating_selectors = [
                'a[href*="parentalguide"]',
                'span.certificate',
                '.subtext .certificate'
            ]
            
            for selector in rating_selectors:
                rating_element = soup.select_one(selector)
                if rating_element:
                    rating_text = rating_element.get_text(strip=True)
                    if rating_text:
                        data['content_rating'] = rating_text
                        break
        
        except Exception as e:
            print(f"❌ Error extracting ratings: {e}")
        
        return data
    
    def _extract_details(self, soup: BeautifulSoup) -> Dict:
        """Extract movie details"""
        data = {'details': {}}
        
        try:
            # Modern details section
            details_section = soup.find('div', {'data-testid': 'title-details'})
            if details_section:
                list_items = details_section.find_all('li', class_='ipc-metadata-list__item')
                
                for item in list_items:
                    try:
                        label = item.find('span', class_='ipc-metadata-list-item__label')
                        if label:
                            key = label.get_text(strip=True).lower().replace(' ', '_').replace(':', '')
                            value_elements = item.find_all('a')
                            if value_elements:
                                values = [elem.get_text(strip=True) for elem in value_elements]
                                data['details'][key] = values if len(values) > 1 else values[0]
                    except:
                        continue
            
            # Release date
            release_element = soup.find('a', href=re.compile(r'releaseinfo'))
            if release_element:
                data['details']['release_date'] = release_element.get_text(strip=True)
            
            # Country of origin
            country_element = soup.find('a', href=re.compile(r'country_of_origin'))
            if country_element:
                data['details']['country'] = country_element.get_text(strip=True)
            
            # Language
            language_elements = soup.find_all('a', href=re.compile(r'primary_language'))
            if language_elements:
                languages = [elem.get_text(strip=True) for elem in language_elements]
                data['details']['languages'] = languages
        
        except Exception as e:
            print(f"❌ Error extracting details: {e}")
        
        return data
    
    def _extract_box_office(self, soup: BeautifulSoup) -> Dict:
        """Extract box office information"""
        data = {'box_office': {}}
        
        try:
            # Modern box office section
            box_office_section = soup.find('div', {'data-testid': 'title-boxoffice'})
            if box_office_section:
                list_items = box_office_section.find_all('li', class_='ipc-metadata-list__item')
                
                for item in list_items:
                    try:
                        label = item.find('span', class_='ipc-metadata-list-item__label')
                        if label:
                            key = label.get_text(strip=True).lower().replace(' ', '_')
                            value = item.get_text().replace(label.get_text(), '').strip()
                            data['box_office'][key] = value
                    except:
                        continue
            
            # Budget and gross from legacy format
            budget_element = soup.find('h4', string='Budget:')
            if budget_element:
                budget_value = budget_element.find_next_sibling(string=True)
                if budget_value:
                    data['box_office']['budget'] = budget_value.strip()
            
            gross_element = soup.find('h4', string='Gross worldwide:')
            if gross_element:
                gross_value = gross_element.find_next_sibling(string=True)
                if gross_value:
                    data['box_office']['gross_worldwide'] = gross_value.strip()
        
        except Exception as e:
            print(f"❌ Error extracting box office: {e}")
        
        return data
    
    def _extract_tech_specs(self, soup: BeautifulSoup) -> Dict:
        """Extract technical specifications"""
        data = {'technical_specs': {}}
        
        try:
            # Modern tech specs section
            tech_section = soup.find('div', {'data-testid': 'title-techspecs'})
            if tech_section:
                list_items = tech_section.find_all('li', class_='ipc-metadata-list__item')
                
                for item in list_items:
                    try:
                        label = item.find('span', class_='ipc-metadata-list-item__label')
                        if label:
                            key = label.get_text(strip=True).lower().replace(' ', '_').replace(':', '')
                            value = item.get_text().replace(label.get_text(), '').strip()
                            data['technical_specs'][key] = value
                    except:
                        continue
            
            # Color, aspect ratio, sound mix from legacy format
            tech_elements = soup.find_all('h4', class_='inline')
            for element in tech_elements:
                text = element.get_text(strip=True).lower()
                if 'color' in text:
                    color_value = element.find_next_sibling(string=True)
                    if color_value:
                        data['technical_specs']['color'] = color_value.strip()
                elif 'aspect ratio' in text:
                    ratio_value = element.find_next_sibling(string=True)
                    if ratio_value:
                        data['technical_specs']['aspect_ratio'] = ratio_value.strip()
                elif 'sound mix' in text:
                    sound_value = element.find_next_sibling(string=True)
                    if sound_value:
                        data['technical_specs']['sound_mix'] = sound_value.strip()
        
        except Exception as e:
            print(f"❌ Error extracting tech specs: {e}")
        
        return data
    
    def get_reviews_via_ddgs(self, movie_title: str, max_reviews: int = 20) -> List[Dict]:
        """Get reviews using DDGS"""
        reviews = []
        
        try:
            print("📝 Searching for reviews...")
            
            # Search for reviews
            review_results = self.ddgs.text(
                f"\"{movie_title}\" \"IMDb\" \"review\"", 
                max_results=max_reviews
            )
            
            for result in review_results:
                if 'imdb.com' in result['href']:
                    review_data = {
                        'title': result['title'].replace(' - IMDb', ''),
                        'content': result['body'],
                        'url': result['href'],
                        'type': 'user',
                        'source': 'ddgs_search'
                    }
                    
                    # Extract rating if available
                    rating_match = re.search(r'(\d+)/10', result['title'] + ' ' + result['body'])
                    if rating_match:
                        review_data['rating'] = rating_match.group(1)
                    
                    reviews.append(review_data)
        
        except Exception as e:
            print(f"❌ Error getting reviews: {e}")
        
        return reviews
    
    def get_featured_reviews_via_ddgs(self, movie_title: str, max_reviews: int = 10) -> List[Dict]:
        """Get featured/critic reviews using DDGS"""
        reviews = []
        
        try:
            print("🌟 Searching for featured reviews...")
            
            # Search for critic/featured reviews
            review_results = self.ddgs.text(
                f"\"{movie_title}\" \"IMDb\" \"critic review\"", 
                max_results=max_reviews
            )
            
            for result in review_results:
                if 'imdb.com' in result['href']:
                    review_data = {
                        'title': result['title'].replace(' - IMDb', ''),
                        'content': result['body'],
                        'url': result['href'],
                        'type': 'critic',
                        'source': 'ddgs_search'
                    }
                    
                    reviews.append(review_data)
        
        except Exception as e:
            print(f"❌ Error getting featured reviews: {e}")
        
        return reviews
    
    def scrape_comprehensive_movie_data(self, movie_title: str) -> Dict:
        """Comprehensive movie data scraping"""
        print(f"\n🎬 Starting comprehensive data collection for: {movie_title}")
        print("=" * 70)
        
        # Step 1: Search for movie
        movie_info = self.search_movie(movie_title)
        if not movie_info:
            return {'error': f'Movie "{movie_title}" not found'}
        
        # Step 2: Get detailed movie information
        movie_data = self.get_movie_details(movie_info['imdb_id'])
        
        # Step 3: Get user reviews
        user_reviews = self.get_reviews_via_ddgs(movie_title, 15)
        movie_data['user_reviews'] = user_reviews
        
        # Step 4: Get featured reviews
        featured_reviews = self.get_featured_reviews_via_ddgs(movie_title, 10)
        movie_data['featured_reviews'] = featured_reviews
        
        # Step 5: Add search info
        movie_data['search_info'] = movie_info
        
        print(f"✅ Data collection completed for: {movie_title}")
        return movie_data

def save_movie_data(movie_data: Dict, format: str = 'both'):
    """Save movie data to file(s)"""
    movie_title = movie_data.get('title', 'unknown_movie').replace(' ', '_')
    
    if format in ['json', 'both']:
        filename = f"imdb_data_{movie_title}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(movie_data, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON data saved to: {filename}")
    
    if format in ['csv', 'both']:
        # Create flattened CSV for main data
        flat_data = {}
        for key, value in movie_data.items():
            if key not in ['cast', 'user_reviews', 'featured_reviews', 'storyline', 'details', 'box_office', 'technical_specs']:
                if isinstance(value, (dict, list)):
                    flat_data[key] = json.dumps(value, ensure_ascii=False)
                else:
                    flat_data[key] = value
        
        df_main = pd.DataFrame([flat_data])
        csv_filename = f"imdb_data_{movie_title}.csv"
        df_main.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"💾 Main data CSV saved to: {csv_filename}")
        
        # Save cast separately
        if movie_data.get('cast'):
            df_cast = pd.DataFrame(movie_data['cast'])
            cast_filename = f"imdb_cast_{movie_title}.csv"
            df_cast.to_csv(cast_filename, index=False, encoding='utf-8')
            print(f"💾 Cast CSV saved to: {cast_filename}")
        
        # Save reviews separately
        if movie_data.get('user_reviews'):
            df_reviews = pd.DataFrame(movie_data['user_reviews'])
            reviews_filename = f"imdb_reviews_{movie_title}.csv"
            df_reviews.to_csv(reviews_filename, index=False, encoding='utf-8')
            print(f"💾 Reviews CSV saved to: {reviews_filename}")

def print_movie_summary(movie_data: Dict):
    """Print a summary of the movie data"""
    print(f"\n{'='*70}")
    print(f"🎬 MOVIE SUMMARY: {movie_data.get('title', 'Unknown')}")
    print(f"{'='*70}")
    
    # Basic Info
    print(f"📺 Title: {movie_data.get('title', 'N/A')}")
    print(f"📅 Year: {movie_data.get('year', 'N/A')}")
    print(f"⏱️  Duration: {movie_data.get('duration', 'N/A')}")
    print(f"⭐ IMDb Rating: {movie_data.get('imdb_rating', 'N/A')}")
    print(f"🎭 Content Rating: {movie_data.get('content_rating', 'N/A')}")
    
    # Summary
    if movie_data.get('summary'):
        print(f"\n📖 Summary: {movie_data.get('summary', 'N/A')[:200]}...")
    
    # Cast
    if movie_data.get('cast'):
        print(f"\n🎭 Top Cast:")
        for actor in movie_data['cast'][:5]:
            print(f"   • {actor.get('actor', 'N/A')} as {actor.get('character', 'N/A')}")
    
    # Reviews
    if movie_data.get('user_reviews'):
        print(f"\n📝 User Reviews: {len(movie_data['user_reviews'])} found")
    
    if movie_data.get('featured_reviews'):
        print(f"🌟 Featured Reviews: {len(movie_data['featured_reviews'])} found")
    
    # Technical Info
    if movie_data.get('technical_specs'):
        print(f"\n🔧 Technical Specs: {len(movie_data['technical_specs'])} items")
    
    if movie_data.get('box_office'):
        print(f"💰 Box Office: {len(movie_data['box_office'])} items")

# Quick test function
def test_ddgs_connection():
    """Test DDGS connection and basic functionality"""
    print("🧪 Testing DDGS connection...")
    
    try:
        ddgs = DDGS()
        results = list(ddgs.text("The Dark Knight IMDb", max_results=2))
        
        if results:
            print("✅ DDGS is working correctly!")
            print(f"Found {len(results)} results")
            for i, result in enumerate(results):
                print(f"{i+1}. {result['title']}")
            return True
        else:
            print("❌ No results found")
            return False
            
    except Exception as e:
        print(f"❌ DDGS test failed: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Test DDGS connection first
    if test_ddgs_connection():
        # Initialize scraper
        scraper = IMDbScraperDDGS()
        
        # Test movies
        test_movies = [
            "Aquaman",
            "Superman"
        ]
        
        for movie in test_movies:
            print(f"\n{'#'*80}")
            print(f"PROCESSING: {movie}")
            print(f"{'#'*80}")
            
            # Scrape comprehensive data
            movie_data = scraper.scrape_comprehensive_movie_data(movie)
            
            if 'error' not in movie_data:
                # Print summary
                print_movie_summary(movie_data)
                
                # Save data
                save_movie_data(movie_data, 'both')
            else:
                print(f"❌ Failed to scrape data for {movie}: {movie_data['error']}")
            
            # Be respectful - add delay
            time.sleep(3)
    else:
        print("❌ Cannot proceed without DDGS connection")