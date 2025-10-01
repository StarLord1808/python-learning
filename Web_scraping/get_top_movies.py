from bs4 import BeautifulSoup
import re

def get_imdb_top_movies(self, limit: int = 250) -> List[Dict]:
        """Get IMDb Top 250 movies as a starting point"""
        movies = []
        try:
            url = "https://www.imdb.com/chart/top/"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find movie entries
            movie_links = soup.select('td.titleColumn a')
            year_elements = soup.select('td.titleColumn span.secondaryInfo')
            
            for i, (link, year_elem) in enumerate(zip(movie_links[:limit], year_elements[:limit])):
                title = link.get_text(strip=True)
                year_text = year_elem.get_text(strip=True)
                year = int(re.search(r'\d{4}', year_text).group()) if year_text else None
                imdb_id = re.search(r'/title/(tt\d+)/', link['href']).group(1)
                
                movies.append({
                    'title': title,
                    'year': year,
                    'imdb_id': imdb_id,
                    'rank': i + 1
                })
                
            print(f"✅ Found {len(movies)} top movies")
            return movies
            
        except Exception as e:
            print(f"❌ Error getting top movies: {e}")
            return []