import time
from imdb_scraper import IMDbScraperDDGS


# Example usage
if __name__ == "__main__":
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
            scraper.print_movie_summary(movie_data)
            
            # Save data
            scraper.save_movie_data(movie_data, 'both')
        else:
            print(f"❌ Failed to scrape data for {movie}: {movie_data['error']}")
        
        # Be respectful - add delay
        time.sleep(3)
else:
    print("❌ Cannot proceed without DDGS connection")