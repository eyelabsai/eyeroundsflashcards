"""
Main script to run the full pipeline: scrape -> download -> generate flashcards
"""
import os
import json
from scraper import EyeRoundsScraper
from downloader import ImageDownloader
from flashcard_generator import FlashcardGenerator


def main(category=None, max_pages=None):
    """
    Main function to scrape EyeRounds atlas and generate flashcards
    
    Args:
        category: Optional category filter (e.g., 'RETINA', 'GLAUCOMA')
        max_pages: Maximum number of pages to scrape (None for all)
    """
    print("=" * 60)
    print("EyeRounds Flashcard Generator")
    print("=" * 60)
    
    scraper = EyeRoundsScraper()
    downloader = ImageDownloader()
    generator = FlashcardGenerator()
    
    # Manual list of different disease pages organized by category
    # RETINA category
    retina_diseases = [
        {
            'title': 'Acute Macular Neuroretinopathy (AMN)',
            'url': 'https://webeye.ophth.uiowa.edu/eyeforum/atlas/pages/acute-macular-neuroretinopathy/index.htm',
            'category': 'RETINA'
        },
        {
            'title': 'Acute posterior multifocal placoid pigment epitheliopathy (APMPPE)',
            'url': 'https://webeye.ophth.uiowa.edu/eyeforum/atlas/pages/apmppe/index.htm',
            'category': 'RETINA'
        },
        # Leukemic pseudohypopyon - need to find correct URL
    ]
    
    # Other categories
    other_diseases = [
        {
            'title': 'Choroidal Hemangioma (Circumscribed)',
            'url': 'https://webeye.ophth.uiowa.edu/eyeforum/atlas/pages/choroidal-hemangioma-circumscribed/index.htm',
            'category': 'RETINA'
        },
        {
            'title': 'Retinoblastoma',
            'url': 'https://webeye.ophth.uiowa.edu/eyeforum/atlas/pages/retinoblastoma/index.htm',
            'category': 'RETINA'
        },
    ]
    
    # Combine based on category filter
    if category and category.upper() == 'RETINA':
        disease_pages = retina_diseases + other_diseases
    else:
        disease_pages = retina_diseases + other_diseases
    
    # Step 1: Try to get atlas entry URLs from index, or use manual list
    print("\n[Step 1] Finding atlas pages...")
    index_url = "https://eyerounds.org/atlas/index.htm"
    atlas_entries = scraper.scrape_atlas_index(index_url, category=category)
    
    # If index scraping didn't work, use manual list
    if not atlas_entries:
        print("⚠️  Index scraping found no entries, using manual disease list...")
        atlas_entries = disease_pages
        print(f"Using {len(atlas_entries)} manual disease pages")
    else:
        print(f"Found {len(atlas_entries)} atlas entries from index")
        if category:
            print(f"Filtered by category: {category}")
    
    # Limit number of pages if specified
    if max_pages:
        atlas_entries = atlas_entries[:max_pages]
        print(f"Limiting to first {max_pages} entries")
    
    all_flashcards = []
    
    # Step 2: Scrape each atlas page
    for idx, atlas_entry in enumerate(atlas_entries, 1):
        url = atlas_entry['url']
        title = atlas_entry['title']
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(atlas_entries)}] Processing: {title}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        # Step 2a: Scrape
        print("\n[2a/4] Scraping page...")
        data = scraper.scrape_atlas_page(url)
        
        if not data:
            print(f"⚠️  Failed to scrape {url}, skipping...")
            continue
        
        if not data.get('entries'):
            print(f"⚠️  No entries found on page, skipping...")
            continue
        
        # Save scraped data
        page_name = url.split('/')[-2] if '/' in url else f'page_{idx}'
        scraped_file = f'data/scraped_{page_name}.json'
        os.makedirs('data', exist_ok=True)
        scraper.save_scraped_data(data, scraped_file)
        
        # Step 2b: Download images
        print(f"\n[2b/4] Downloading images...")
        all_downloaded = []
        for i, entry in enumerate(data.get('entries', [])):
            print(f"  Downloading images for entry {i+1}...")
            downloaded = downloader.download_entry_images(entry, i)
            all_downloaded.append(downloaded)
            print(f"    ✓ Downloaded {len(downloaded)} images")
        
        # Step 2c: Generate flashcards
        print(f"\n[2c/4] Generating flashcards...")
        flashcards = generator.create_flashcards_from_scraped_data(
            scraped_file, 
            all_downloaded
        )
        all_flashcards.extend(flashcards)
        print(f"  ✓ Generated {len(flashcards)} flashcards")
    
    # Step 3: Save all flashcards
    if all_flashcards:
        print(f"\n{'='*60}")
        print("[Step 3] Saving all flashcards...")
        print(f"{'='*60}")
        generator.save_flashcards(all_flashcards)
        print(f"\n{'='*60}")
        print(f"✅ Successfully created {len(all_flashcards)} flashcards!")
        print(f"{'='*60}")
        print("\nTo view flashcards, run:")
        print("  streamlit run app.py")
    else:
        print("\n❌ No flashcards were created. Please check the scraping process.")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    category = None
    max_pages = None
    
    if len(sys.argv) > 1:
        category = sys.argv[1] if sys.argv[1] != 'None' else None
    if len(sys.argv) > 2:
        try:
            max_pages = int(sys.argv[2])
        except ValueError:
            pass
    
    if category:
        print(f"Filtering by category: {category}")
    if max_pages:
        print(f"Limiting to {max_pages} pages")
    
    main(category=category, max_pages=max_pages)
