"""
Scrape specific EyeRounds atlas pages for the requested RETINA conditions.
"""
import json
import os
from scraper import EyeRoundsScraper
from downloader import ImageDownloader
from flashcard_generator import FlashcardGenerator

def main():
    urls = [
        "https://eyerounds.org/atlas/pages/Acute-macular-neuroretinopathy/index.htm",
        "https://eyerounds.org/atlas/pages/leukemic-pseudohypopyon.htm",
        "https://eyerounds.org/atlas/pages/apmppe/index.htm",
        "https://eyerounds.org/atlas/pages/leukemic-pseudohypopyon.htm"
    ]
    
    scraper = EyeRoundsScraper()
    downloader = ImageDownloader()
    generator = FlashcardGenerator()
    
    all_flashcards = []
    
    # Load existing flashcards if any
    if os.path.exists('data/flashcards.json'):
        with open('data/flashcards.json', 'r') as f:
            all_flashcards = json.load(f)
    
    # Track existing URLs to avoid duplicates
    existing_urls = {card['url'] for card in all_flashcards}
    
    for i_url, url in enumerate(urls):
        print(f"\nScraping {url}...")
        data = scraper.scrape_atlas_page(url)
        
        if data:
            # Save raw scraped data for reference
            url_parts = [p for p in url.split('/') if p]
            url_part = url_parts[-1].replace('.htm', '').lower()
            if url_part == 'index' and len(url_parts) > 1:
                url_part = url_parts[-2].lower()
            filename = f"data/scraped_{url_part}.json"
            scraper.save_scraped_data(data, filename)
            
            # Download images and create flashcards for each entry
            for i, entry in enumerate(data.get('entries', [])):
                print(f"  Processing entry {i+1}...")
                downloaded_images = downloader.download_entry_images(entry, i)
                
                # Create a temporary data structure for this entry to use with generator
                entry_data = {
                    'title': data['title'],
                    'url': data['url'],
                    'entries': [entry]
                }
                
                # Save temp entry data
                temp_file = 'data/temp_entry.json'
                with open(temp_file, 'w') as f:
                    json.dump(entry_data, f)
                
                # Generate flashcards for this entry
                new_cards = generator.create_flashcards_from_scraped_data(temp_file, [downloaded_images])
                
                # Add to all flashcards if not already present
                for card in new_cards:
                    # Use a combination of URL and entry index for uniqueness
                    # If it's the duplicate requested URL, we allow it by appending a suffix to the ID
                    card_id = f"{card['url']}_{card['entry_index']}"
                    
                    # Check if this exact URL was already processed in THIS run
                    is_duplicate_url = urls.count(url) > 1 and urls.index(url) < i_url
                    
                    if not any(f"{c['url']}_{c['entry_index']}_{c.get('is_dup', False)}" == f"{card_id}_{is_duplicate_url}" for c in all_flashcards):
                        if is_duplicate_url:
                            card['id'] += "_dup"
                            card['is_dup'] = True
                        all_flashcards.append(card)
                        print(f"    Added flashcard: {card['title']} (Entry {card['entry_index']}){' [Duplicate]' if is_duplicate_url else ''}")
    
    # Save all flashcards
    generator.save_flashcards(all_flashcards)
    print(f"\nTotal flashcards: {len(all_flashcards)}")

if __name__ == "__main__":
    main()
