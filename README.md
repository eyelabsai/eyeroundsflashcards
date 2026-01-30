# EyeRounds Flashcard Generator

A tool to scrape ophthalmology images and descriptions from EyeRounds.org and create interactive flashcards for study.

## Features

- Scrapes atlas entries from EyeRounds.org
- Downloads images locally
- Generates flashcards with images and descriptions
- Interactive web-based flashcard review interface
- Filter by category (RETINA, GLAUCOMA, CORNEA, etc.)

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

1. **Scrape atlas entries and generate flashcards:**
```bash
python main.py
```

This will:
- Scrape the atlas index page to find all entries
- Download images from each entry
- Generate flashcards
- Save everything to `data/` directory

2. **View flashcards:**
```bash
streamlit run app.py
```

### Advanced Usage

**Filter by category:**
```bash
python main.py RETINA
python main.py GLAUCOMA
python main.py CORNEA
```

**Limit number of pages:**
```bash
python main.py RETINA 5  # Scrape first 5 RETINA entries
```

**Test scraper only:**
```bash
python scraper.py  # Tests scraping the index and a sample page
```

## Project Structure

```
eyerounds-rip/
├── scraper.py              # Web scraper for EyeRounds pages
├── downloader.py           # Downloads images locally
├── flashcard_generator.py  # Creates flashcard data structure
├── main.py                 # Main pipeline script
├── app.py                  # Streamlit flashcard review app
├── requirements.txt        # Python dependencies
├── data/
│   ├── images/            # Downloaded images
│   ├── flashcards.json    # Generated flashcard data
│   └── scraped_*.json     # Raw scraped data
└── README.md
```

## How It Works

1. **Scraper** (`scraper.py`):
   - Scrapes the atlas index page to find all entry links
   - Extracts images, descriptions, contributors, and photographers from each page
   - Handles both old (webeye.ophth.uiowa.edu) and new (eyerounds.org) URL formats

2. **Downloader** (`downloader.py`):
   - Downloads all images from scraped entries
   - Organizes images with descriptive filenames
   - Saves to `data/images/`

3. **Flashcard Generator** (`flashcard_generator.py`):
   - Creates flashcard data structure
   - Combines images with answer text (photographers + description)
   - Saves to `data/flashcards.json`

4. **App** (`app.py`):
   - Streamlit web interface
   - Shows images first (question)
   - Reveals answer on click/enter
   - Navigation between cards

## Example Flashcard

**Question (shown first):**
- Image(s) from EyeRounds entry

**Answer (revealed on click):**
```
Photographers: Randy Verdick, FOPS (figs. 1a, 1b); Antionette Venckus, CRA (fig. 1f)

These photographs show the appearance of a circumscribed choroidal hemangioma before and after treatment with photodynamic therapy (PDT). The lesion appeared as an elevated choroidal mass with overlying orange plaques and RPE atrophy...
```

## Categories

Available categories for filtering:
- RETINA
- GLAUCOMA
- CORNEA
- CATARACT
- UVEITIS
- OCULOPLASTICS
- NEURO-OP
- TRAUMA
- PATHOLOGY
- VITREOUS
- IRIS
- LENS
- EXTERNAL DISEASE
- CONTACT LENS
- GENETICS
- INHERITED DISEASE
- SYSTEMS

## Notes

- Images are used under Creative Commons Attribution-NonCommercial-NoDerivs 3.0 License
- Respect rate limits when scraping
- Some pages may require JavaScript rendering (not currently supported)

## Troubleshooting

- **No flashcards found**: Run `python main.py` first to scrape and generate flashcards
- **Images not loading**: Check that images were downloaded to `data/images/`
- **Scraping fails**: Check internet connection and that EyeRounds.org is accessible
