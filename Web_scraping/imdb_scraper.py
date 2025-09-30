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
from imdb_searcher import ImprovedIMDbScraper

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
        """Extract full plot summary from /plotsummary page (not just main page)."""
        data = {}
        
        try:
            # 1. Try to get short summary from main page (fallback)
            short_summary = None
            for selector in ['span[data-testid="plot-xl"]', '.summary_text']:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if text and 'add a plot' not in text.lower():
                        short_summary = text
                        break

            # 2. Fetch full plot summary from /plotsummary page
            if hasattr(self, 'imdb_id') and self.imdb_id:
                plot_url = f"https://www.imdb.com/title/{self.imdb_id}/plotsummary/"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                try:
                    import requests
                    response = requests.get(plot_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        plot_soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # The official plot summaries are in <li> inside <section> with no class,
                        # but usually the FIRST <li> under a section is the "official" one.
                        # Structure: <section><ul><li>...</li></ul></section>
                        first_plot_li = plot_soup.select_one('section ul li')
                        if first_plot_li:
                            full_text = first_plot_li.get_text(strip=True)
                            # Clean up extra whitespace
                            full_text = ' '.join(full_text.split())
                            if full_text and len(full_text) > 50:
                                data['summary'] = full_text
                                data['synopsis'] = full_text  # or expand later if needed
                            else:
                                # Fallback to short summary
                                if short_summary:
                                    data['summary'] = short_summary
                                    data['synopsis'] = short_summary
                        else:
                            if short_summary:
                                data['summary'] = short_summary
                                data['synopsis'] = short_summary
                    else:
                        # Fallback if request fails
                        if short_summary:
                            data['summary'] = short_summary
                            data['synopsis'] = short_summary

                except Exception as e:
                    print(f"⚠️ Failed to fetch /plotsummary: {e}")
                    if short_summary:
                        data['summary'] = short_summary
                        data['synopsis'] = short_summary
            else:
                # No imdb_id? Just use short summary
                if short_summary:
                    data['summary'] = short_summary
                    data['synopsis'] = short_summary

        except Exception as e:
            print(f"❌ Error extracting summary/synopsis: {e}")
        
        return data
    
    def _extract_cast(self, soup: BeautifulSoup) -> Dict:
        """Extract cast information from main IMDb movie page (modern layout)."""
        data = {'cast': []}
        
        try:
            # Find the main cast list container (modern IMDb)
            cast_list = soup.find('div', {'data-testid': 'title-cast-list'})
            if not cast_list:
                cast_list = soup.find('section', {'data-testid': 'title-cast'})  # fallback

            if cast_list:
                # Each actor card is in a list item or direct child
                actor_links = cast_list.find_all('a', href=re.compile(r'/name/nm\d+/'))
                
                for link in actor_links[:20]:
                    actor_name = link.get_text(strip=True)
                    if not actor_name:
                        continue

                    # Character name is usually in the next sibling/child with specific testid
                    character_elem = link.find_next('div', {'data-testid': re.compile(r'.*character.*')})
                    if not character_elem:
                        character_elem = link.find_next('span', string=re.compile(r'.'))
                    
                    character_name = "Unknown"
                    if character_elem:
                        char_text = character_elem.get_text(strip=True)
                        # Clean common IMDb artifacts like "as Tony Stark"
                        char_text = re.sub(r'^(as\s+)?', '', char_text, flags=re.IGNORECASE)
                        char_text = re.sub(r'\s*\([^)]*\)\s*', ' ', char_text)  # remove (credit only), etc.
                        character_name = re.sub(r'\s+', ' ', char_text).strip() or "Unknown"

                    data['cast'].append({
                        'actor': actor_name,
                        'character': character_name
                    })
            else:
                # Fallback: try legacy table (rarely present in modern pages)
                cast_table = soup.find('table', class_='cast_list')
                if cast_table:
                    rows = cast_table.find_all('tr')[1:]
                    for row in rows[:20]:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            actor_link = cells[1].find('a')
                            if actor_link:
                                actor_name = actor_link.get_text(strip=True)
                                char_cell = cells[3]
                                # Remove annotations
                                for span in char_cell.find_all('span'):
                                    span.decompose()
                                character_name = re.sub(r'\s+', ' ', char_cell.get_text(strip=True)) or "Unknown"
                                data['cast'].append({
                                    'actor': actor_name,
                                    'character': character_name
                                })

        except Exception as e:
            print(f"❌ Error extracting cast: {e}")
        
        return data
    
    def _extract_storyline(self, soup: BeautifulSoup) -> Dict:
        """Extract storyline information from modern IMDb movie page."""
        data = {'storyline': {}}
        
        try:
            # 1. Plot Summary (look for <span> or <div> with data-testid containing 'plot')
            plot_element = soup.select_one('span[data-testid="plot-xl"], div[data-testid="plot-xl"]')
            if not plot_element:
                # Fallback: look for any prominent plot-like text near "Storyline" section
                storyline_section = soup.find('section', {'data-testid': 'Storyline'})
                if storyline_section:
                    # Get first non-empty paragraph or span
                    for elem in storyline_section.find_all(['span', 'div']):
                        text = elem.get_text(strip=True)
                        if text and len(text) > 30:  # reasonable plot length
                            plot_element = elem
                            break

            if plot_element:
                plot_text = plot_element.get_text(strip=True)
                if plot_text and len(plot_text) > 10:
                    data['storyline']['plot_summary'] = plot_text

            # 2. Genres (modern layout: inside hero title block or storyline section)
            genre_elements = soup.select('a[href*="/search/title/?genres="]')
            if not genre_elements:
                # Alternative: look for chips with data-testid containing 'genre'
                genre_elements = soup.find_all('span', {'class': re.compile(r'.*chip.*')})
                # But better: use explicit genre links
                genre_elements = soup.select('div[data-testid="genres"] a')

            if genre_elements:
                genres = []
                for elem in genre_elements:
                    text = elem.get_text(strip=True)
                    if text and text not in genres:
                        genres.append(text)
                if genres:
                    data['storyline']['genres'] = genres

            # 3. Tagline (now often in a div with data-testid="storyline-2" or similar)
            # Look for a line that starts with "Taglines:" or is labeled as such
            tagline = None
            # Method 1: Check storyline section for a line containing "Tagline"
            storyline_items = soup.select('li[data-testid="storyline-2"]')
            for item in storyline_items:
                spans = item.find_all('span')
                if len(spans) >= 2:
                    label = spans[0].get_text(strip=True).lower()
                    if 'tagline' in label:
                        tagline = spans[1].get_text(strip=True)
                        break

            # Method 2: Fallback – look for any element with "Tagline:" in text
            if not tagline:
                for elem in soup.find_all('span', string=re.compile(r'Tagline', re.I)):
                    next_elem = elem.find_next('span')
                    if next_elem:
                        tagline = next_elem.get_text(strip=True)
                        break

            if tagline:
                data['storyline']['tagline'] = tagline

            # 4. Keywords (now under "Storyline" > "Plot Keywords")
            # They appear as links inside a list with data-testid="storyline-3"
            keyword_section = soup.select_one('li[data-testid="storyline-3"]')
            if keyword_section:
                keyword_links = keyword_section.find_all('a')
                keywords = []
                for link in keyword_links:
                    kw = link.get_text(strip=True)
                    if kw and kw not in keywords:
                        keywords.append(kw)
                if keywords:
                    data['storyline']['keywords'] = keywords

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
        """Extract box office information from modern IMDb movie page."""
        data = {'box_office': {}}
        
        try:
            # 1. Try modern "Details" section (often contains budget/gross)
            # Look for list items under a section with "Box office" or financial info
            detail_sections = soup.find_all('li', {'data-testid': re.compile(r'title-details|boxoffice')})
            
            for item in detail_sections:
                # Check if this item contains budget, gross, etc.
                label_elem = item.find('span', {'class': re.compile(r'ipc-metadata-list-item__label')})
                if not label_elem:
                    continue
                    
                label = label_elem.get_text(strip=True)
                value_elem = label_elem.find_next_sibling()
                if not value_elem:
                    # Try getting all text and removing label
                    full_text = item.get_text(strip=True)
                    value = full_text.replace(label, '').strip()
                else:
                    value = value_elem.get_text(strip=True)
                
                if not value:
                    continue

                # Normalize keys
                key = label.lower()
                if 'budget' in key:
                    data['box_office']['budget'] = value
                elif 'gross' in key and 'worldwide' in key:
                    data['box_office']['gross_worldwide'] = value
                elif 'opening weekend' in key:
                    data['box_office']['opening_weekend_usa'] = value
                elif 'gross usa' in key or 'gross us' in key:
                    data['box_office']['gross_usa'] = value

            # 2. Fallback: Legacy h4-based extraction (rare, but keep for old pages)
            if not data['box_office']:
                budget_element = soup.find('h4', string=re.compile(r'^Budget:$', re.I))
                if budget_element:
                    next_text = budget_element.next_sibling
                    if next_text and isinstance(next_text, str):
                        data['box_office']['budget'] = next_text.strip()
                    else:
                        # Try next element
                        next_elem = budget_element.find_next(string=True)
                        if next_elem:
                            data['box_office']['budget'] = next_elem.strip()

                gross_element = soup.find('h4', string=re.compile(r'^Gross worldwide:$', re.I))
                if gross_element:
                    next_text = gross_element.next_sibling
                    if next_text and isinstance(next_text, str):
                        data['box_office']['gross_worldwide'] = next_text.strip()
                    else:
                        next_elem = gross_element.find_next(string=True)
                        if next_elem:
                            data['box_office']['gross_worldwide'] = next_elem.strip()

        except Exception as e:
            print(f"❌ Error extracting box office: {e}")
        
        return data
    
    def _extract_tech_specs(self, soup: BeautifulSoup) -> Dict:
        """Extract technical specifications from modern IMDb movie page."""
        data = {'technical_specs': {}}
        
        try:
            # 1. Look in modern metadata sections (e.g., Details, Hero metadata)
            # Runtime often appears in hero section
            runtime_elem = soup.select_one('li[data-testid="title-techspec_runtime"]')
            if runtime_elem:
                value = runtime_elem.get_text(strip=True)
                if value:
                    data['technical_specs']['runtime'] = value

            # Look for other tech specs in detail list items
            detail_items = soup.select('li[data-testid^="title-details"], li[data-testid^="title-techspec"]')
            for item in detail_items:
                label_elem = item.select_one('span.ipc-metadata-list-item__label')
                if not label_elem:
                    continue
                label = label_elem.get_text(strip=True)
                # Get value: either next sibling or rest of item text
                full_text = item.get_text(strip=True)
                value = full_text.replace(label, '').strip()
                
                if not value:
                    continue

                # Normalize key
                key = (
                    label.lower()
                    .replace(':', '')
                    .replace(' ', '_')
                    .replace('(', '')
                    .replace(')', '')
                    .replace('/', '_')
                )

                # Only keep relevant tech specs
                if any(kw in key for kw in ['runtime', 'color', 'aspect', 'sound', 'camera', 'film']):
                    data['technical_specs'][key] = value

            # 2. Fallback: Legacy inline h4 elements (for older pages)
            if not data['technical_specs']:
                tech_elements = soup.find_all('h4', class_='inline')
                for elem in tech_elements:
                    label_text = elem.get_text(strip=True)
                    next_text = elem.next_sibling
                    if next_text and isinstance(next_text, str):
                        value = next_text.strip()
                    else:
                        next_elem = elem.find_next(string=True)
                        value = next_elem.strip() if next_elem else None

                    if not value:
                        continue

                    label_lower = label_text.lower()
                    if 'color' in label_lower:
                        data['technical_specs']['color'] = value
                    elif 'aspect ratio' in label_lower:
                        data['technical_specs']['aspect_ratio'] = value
                    elif 'sound mix' in label_lower:
                        data['technical_specs']['sound_mix'] = value
                    elif 'runtime' in label_lower:
                        data['technical_specs']['runtime'] = value

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
            "The Dark Knight"
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