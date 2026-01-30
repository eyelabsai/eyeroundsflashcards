"""
Streamlit flashcard app for EyeRounds ophthalmology study
Modern, clean UI with image-first flashcard format
"""
import streamlit as st
import json
from pathlib import Path
import random

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="EyeRounds Flashcards",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: #1a73e8;
        margin-bottom: 0.5rem;
    }
    
    /* Card container */
    .flashcard-container {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Image container */
    .image-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Answer box */
    .answer-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1rem;
        border-left: 4px solid #4caf50;
    }
    
    .answer-box h4 {
        color: #2e7d32;
        margin-bottom: 1rem;
    }
    
    /* Category badge */
    .category-badge {
        display: inline-block;
        background: #1a73e8;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* Navigation buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card title */
    .card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    /* Progress indicator */
    .progress-text {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    /* Source link */
    .source-link {
        font-size: 0.85rem;
        color: #666;
    }
    
    .source-link a {
        color: #1a73e8;
    }
</style>
""", unsafe_allow_html=True)


CATEGORIES = [
    'CATARACT', 'CONTACT LENS', 'CORNEA', 'EXTERNAL DISEASE', 'GENETICS',
    'GLAUCOMA', 'INHERITED DISEASE', 'IRIS', 'LENS', 'NEURO-OP', 
    'PATHOLOGY', 'OCULOPLASTICS', 'RETINA', 'SYSTEMS', 'TRAUMA', 
    'UVEITIS', 'VITREOUS'
]


@st.cache_data
def load_flashcards():
    """Load flashcards from JSON file"""
    # Try new format first
    flashcard_file = Path('data/all_flashcards.json')
    if flashcard_file.exists():
        with open(flashcard_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('flashcards', [])
    
    # Fall back to old format
    old_file = Path('data/flashcards.json')
    if old_file.exists():
        with open(old_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return []


def get_unique_categories(flashcards):
    """Get sorted list of unique categories"""
    categories = set()
    for card in flashcards:
        cat = card.get('category', 'UNCATEGORIZED')
        categories.add(cat)
    return ['ALL'] + sorted(list(categories))


def filter_flashcards(flashcards, category):
    """Filter flashcards by category"""
    if category == 'ALL':
        return flashcards
    return [c for c in flashcards if c.get('category', 'UNCATEGORIZED') == category]


def display_images(images, show_captions=False):
    """Display images in a responsive grid."""
    if not images:
        st.warning("No images available for this card.")
        return
    
    # Filter out duplicates and extract URLs
    unique_images = []
    seen = set()
    for img in images:
        # Handle both old format (string URLs) and new format (dict with url key)
        if isinstance(img, str):
            url = img
            alt = ""
        else:
            url = img.get('url', '')
            alt = img.get('alt', '')
        
        if url and url not in seen:
            seen.add(url)
            unique_images.append({'url': url, 'alt': alt})
    
    num_images = len(unique_images)
    
    if num_images == 0:
        st.warning("No images available for this card.")
        return
    
    if num_images == 1:
        img = unique_images[0]
        caption = img['alt'] if (show_captions and img['alt']) else None
        st.image(img['url'], caption=caption, use_container_width=True)
    elif num_images == 2:
        col1, col2 = st.columns(2)
        with col1:
            img = unique_images[0]
            caption = img['alt'] if (show_captions and img['alt']) else None
            st.image(img['url'], caption=caption, use_container_width=True)
        with col2:
            img = unique_images[1]
            caption = img['alt'] if (show_captions and img['alt']) else None
            st.image(img['url'], caption=caption, use_container_width=True)
    else:
        # Multiple images in grid (max 3 columns)
        cols = st.columns(min(3, num_images))
        for i, img in enumerate(unique_images):
            with cols[i % len(cols)]:
                caption = img['alt'] if (show_captions and img['alt']) else None
                st.image(img['url'], caption=caption, use_container_width=True)


def main():
    flashcards = load_flashcards()
    
    if not flashcards:
        st.error("No flashcards found!")
        st.info("""
        **To get started:**
        1. Run `python extract_atlas.py` to extract the atlas database
        2. Run `python scrape_all.py --no-images` to scrape all conditions
        3. Run `python generate_flashcards.py` to generate flashcards
        4. Then refresh this page
        """)
        return
    
    # Get categories
    categories = get_unique_categories(flashcards)
    
    # Initialize session state
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = 'ALL'
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 👁️ EyeRounds Study")
        st.markdown("---")
        
        # Category filter
        st.markdown("### Filter by Topic")
        
        new_category = st.selectbox(
            "Category",
            categories,
            index=categories.index(st.session_state.selected_category) if st.session_state.selected_category in categories else 0,
            label_visibility="collapsed"
        )
        
        # Handle category change
        if new_category != st.session_state.selected_category:
            st.session_state.selected_category = new_category
            st.session_state.current_index = 0
            st.session_state.show_answer = False
            st.rerun()
        
        # Filter cards
        filtered_cards = filter_flashcards(flashcards, st.session_state.selected_category)
        
        st.markdown("---")
        
        # Stats
        st.metric("Cards Available", len(filtered_cards))
        st.metric("Total in Database", len(flashcards))
        
        if len(filtered_cards) > 0:
            st.markdown("---")
            st.markdown("### Navigation")
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Prev", use_container_width=True):
                    st.session_state.current_index = (st.session_state.current_index - 1) % len(filtered_cards)
                    st.session_state.show_answer = False
                    st.rerun()
            with col2:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state.current_index = (st.session_state.current_index + 1) % len(filtered_cards)
                    st.session_state.show_answer = False
                    st.rerun()
            
            if st.button("🎲 Random Card", use_container_width=True):
                st.session_state.current_index = random.randint(0, len(filtered_cards) - 1)
                st.session_state.show_answer = False
                st.rerun()
            
            st.markdown("---")
            
            # Card selector
            st.markdown("### Jump to Card")
            card_options = [f"{i+1}. {c.get('title', 'Unknown')[:25]}..." for i, c in enumerate(filtered_cards)]
            selected_card = st.selectbox(
                "Select card",
                range(len(filtered_cards)),
                index=st.session_state.current_index,
                format_func=lambda x: card_options[x],
                label_visibility="collapsed"
            )
            
            if selected_card != st.session_state.current_index:
                st.session_state.current_index = selected_card
                st.session_state.show_answer = False
                st.rerun()
    
    # Main content
    if len(filtered_cards) == 0:
        st.warning(f"No flashcards found for category: {st.session_state.selected_category}")
        return
    
    # Ensure index is valid
    if st.session_state.current_index >= len(filtered_cards):
        st.session_state.current_index = 0
    
    current_card = filtered_cards[st.session_state.current_index]
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>👁️ EyeRounds Flashcards</h1>
        <p>Card {st.session_state.current_index + 1} of {len(filtered_cards)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Category badge
    category = current_card.get('category', 'UNCATEGORIZED')
    st.markdown(f'<span class="category-badge">{category}</span>', unsafe_allow_html=True)
    
    # Title - only show after reveal
    if st.session_state.show_answer:
        st.markdown(f"### {current_card.get('title', 'Unknown Condition')}")
    else:
        st.markdown("### What is the diagnosis?")
    
    # Images section
    st.markdown("---")
    st.markdown("#### 🖼️ Clinical Images")
    
    images = current_card.get('images', [])
    display_images(images, show_captions=st.session_state.show_answer)
    
    # Answer section
    st.markdown("---")
    
    if not st.session_state.show_answer:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("👁️ Reveal Answer", type="primary", use_container_width=True):
                st.session_state.show_answer = True
                st.rerun()
        
        st.markdown("""
        <div style="text-align: center; color: #666; margin-top: 1rem;">
            <em>Study the images, then click to reveal the diagnosis</em>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show answer
        st.markdown("#### ✅ Answer")
        st.markdown(f"**{current_card.get('title', 'Unknown')}**")
        
        description = current_card.get('description', '')
        if description:
            st.markdown(description)
        
        # Contributor info
        st.markdown("---")
        
        contributor = current_card.get('contributor', '')
        photographer = current_card.get('photographer', '')
        source_url = current_card.get('source_url', '')
        
        if contributor:
            st.markdown(f"**Contributor:** {contributor}")
        if photographer:
            st.markdown(f"**Photographer:** {photographer}")
        if source_url:
            st.markdown(f"**Source:** [{source_url}]({source_url})")
        
        # Next card button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➡️ Next Card", type="primary", use_container_width=True):
                st.session_state.current_index = (st.session_state.current_index + 1) % len(filtered_cards)
                st.session_state.show_answer = False
                st.rerun()


if __name__ == "__main__":
    main()
