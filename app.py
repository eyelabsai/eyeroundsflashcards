"""
Streamlit flashcard app for EyeRounds ophthalmology study
Modern, clean UI with image-first flashcard format.
After reveal, GPT-4o can provide oral-boards-style treatment & next steps.
"""
import os
import streamlit as st
import json
from pathlib import Path
import random

# Load .env for OpenAI API key
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
    /* Hide Streamlit header, toolbar, and footer completely */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    
    /* Main container - zero top padding */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 1000px;
    }
    
    section.main [data-testid="block-container"] {
        padding-top: 0.5rem !important;
    }
    
    /* Reduce all vertical gaps */
    .main [data-testid="stVerticalBlock"] > div { 
        padding-top: 0 !important; 
        padding-bottom: 0 !important; 
    }
    
    /* Compact header */
    .main-header {
        text-align: center;
        padding: 0.25rem 0;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #1a73e8 0%, #1565c0 100%);
        border-radius: 8px;
        color: white;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0;
        font-size: 0.75rem;
        color: rgba(255,255,255,0.9);
    }
    
    /* Tight spacing */
    .main .element-container { margin-bottom: 0.1rem !important; }
    .main h3 { margin-top: 0.3rem !important; margin-bottom: 0.2rem !important; font-size: 1.1rem !important; }
    .main h4 { margin-top: 0.2rem !important; margin-bottom: 0.15rem !important; font-size: 0.95rem !important; }
    .main hr { margin: 0.4rem 0 !important; border-color: #e0e0e0; }
    .main p { margin-bottom: 0.2rem !important; }
    
    /* Card container */
    .flashcard-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-bottom: 0.5rem;
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
    
    /* Category badge - compact */
    .category-badge {
        display: inline-block;
        background: #1a73e8;
        color: white;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Shrink gap around embedded html (keyboard zone) */
    .main [data-testid="stFrame"] { margin-bottom: 0.1rem !important; }
    
    /* Smaller clinical images - cap size so they don't dominate */
    .main [data-testid="stImage"] img { max-width: 280px !important; max-height: 220px !important; object-fit: contain; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.5rem;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.3rem;
    }
    
    /* Navigation buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.4rem 0.8rem;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
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
    
    /* Treatment box - oral boards - interactive accordion design */
    .treatment-box {
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        margin: 1rem 0 1.5rem 0;
        overflow: hidden;
        border: none;
    }
    .treatment-box .treatment-title {
        font-size: 1rem;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
        padding: 0.6rem 1rem;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .treatment-box .treatment-content {
        padding: 0;
    }
    .treatment-box p {
        margin: 0 0 0.4rem 0 !important;
        color: #333;
        font-size: 0.9rem;
        line-height: 1.55;
    }
    .treatment-box ul, .treatment-box ol {
        margin: 0.2rem 0 0.5rem 0;
        padding-left: 1.1rem;
    }
    .treatment-box li {
        margin-bottom: 0.3rem;
        color: #333;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .treatment-box li::marker {
        color: #1565c0;
    }
    .treatment-box strong {
        color: #0d47a1;
        font-weight: 600;
    }
    /* Color-coded collapsible sections */
    .treatment-box details {
        border-bottom: 1px solid #e8e8e8;
    }
    .treatment-box details:last-of-type {
        border-bottom: none;
    }
    .treatment-box summary {
        padding: 0.7rem 1rem;
        cursor: pointer;
        font-weight: 700;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transition: background 0.2s;
        list-style: none;
    }
    .treatment-box summary::-webkit-details-marker { display: none; }
    .treatment-box summary::before {
        content: "▶";
        font-size: 0.7rem;
        transition: transform 0.2s;
    }
    .treatment-box details[open] summary::before {
        transform: rotate(90deg);
    }
    .treatment-box summary:hover {
        filter: brightness(0.97);
    }
    .treatment-box details .section-content {
        padding: 0.5rem 1rem 0.8rem 1.5rem;
        background: #fafafa;
    }
    /* Section 1: Data Acquisition - Blue */
    .treatment-box .section-data summary {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #0d47a1;
    }
    /* Section 2: Diagnosis - Green */
    .treatment-box .section-diagnosis summary {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        color: #2e7d32;
    }
    .treatment-box .section-diagnosis strong { color: #2e7d32; }
    .treatment-box .section-diagnosis li::marker { color: #2e7d32; }
    /* Section 3: Management - Purple */
    .treatment-box .section-management summary {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        color: #6a1b9a;
    }
    .treatment-box .section-management strong { color: #6a1b9a; }
    .treatment-box .section-management li::marker { color: #6a1b9a; }
    /* Section 4: Follow-up Questions - Orange */
    .treatment-box .section-questions summary {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        color: #e65100;
    }
    .treatment-box .section-questions strong { color: #e65100; }
    /* Sub-headers within sections */
    .treatment-box h3, .treatment-box h4 {
        color: #555;
        margin: 0.6rem 0 0.3rem 0;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    /* Legacy h1/h2 fallback */
    .treatment-box h1, .treatment-box h2 {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #0d47a1;
        margin: 0;
        padding: 0.6rem 1rem;
        font-size: 0.95rem;
        font-weight: 700;
        border-top: 1px solid #e0e0e0;
    }
    .treatment-box h1:first-child, .treatment-box h2:first-child {
        border-top: none;
    }
    
    /* Floating next card button - orange for contrast */
    .floating-next-btn {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(255, 107, 53, 0.4);
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
    }
    .floating-next-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.5);
        background: linear-gradient(135deg, #ff7f50 0%, #ffa500 100%);
        color: white;
    }
    .floating-next-btn:active {
        transform: translateY(0);
    }
    /* Floating Prev button - same style, left side */
    .floating-prev-btn {
        position: fixed;
        bottom: 24px;
        right: 140px;
        z-index: 9999;
        background: linear-gradient(135deg, #5c6bc0 0%, #3949ab 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(57, 73, 171, 0.4);
        transition: all 0.2s ease;
        text-decoration: none;
    }
    .floating-prev-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(57, 73, 171, 0.5);
        color: white;
    }
    .floating-prev-btn:active {
        transform: translateY(0);
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


def filter_by_search(cards, query):
    """Filter cards by keyword search (title, description, keywords). Case-insensitive."""
    if not query or not query.strip():
        return cards
    q = query.strip().lower()
    out = []
    for c in cards:
        title = (c.get("title") or "").lower()
        description = (c.get("description") or c.get("answer") or "").lower()
        keywords = (c.get("keywords") or "").lower()
        if q in title or q in description or q in keywords:
            out.append(c)
    return out


def get_oral_boards_treatment(card):
    """Call GPT-4o with ABO oral boards structure: Data Acquisition, Diagnosis, Management."""
    if not OPENAI_API_KEY or OPENAI_API_KEY.strip() == "your_openai_api_key_here":
        return None, "Add your OpenAI API key to `.env` (OPENAI_API_KEY=...) to use this."
    try:
        import httpx
        from openai import OpenAI
        diagnosis = card.get("title", "Unknown")
        description = (card.get("description") or card.get("answer") or "").strip()
        contributor = card.get("contributor", "")
        photographer = card.get("photographer", "")
        context = f"Diagnosis: {diagnosis}.\nFindings/context: {description}"
        if contributor:
            context += f"\nContributor: {contributor}."
        if photographer:
            context += f"\nPhotographer: {photographer}."
        # Custom httpx client without env proxies to avoid "proxies" argument errors
        with httpx.Client(trust_env=False) as http_client:
            client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an ABO-style ophthalmology oral boards examiner. Cases are scored on Data Acquisition, Diagnosis, and Management. Examiners may ask: "Why is this information useful?" "How would you perform this surgery?" "What if that therapy didn't help?" They do not encourage, teach, or acknowledge right/wrong—they assess. Give output a candidate could use to prepare: clear, systematic, concise. Use bullet points and short paragraphs. Structure your response using the three ABO categories below."""
                    },
                    {
                        "role": "user",
                        "content": f"""{context}

Using ABO Candidate Performance Criteria, provide a concise study outline in three sections:

**1. Data Acquisition**
- What relevant history to elicit (onset, progression, trauma, surgery, systemic risk factors).
- Important exam findings and ancillary testing to order (e.g., A/B scan, imaging, labs).

**2. Diagnosis**
- Differential diagnosis (what else to consider).
- Most likely diagnosis and key investigations that support it.

**3. Management**
- Safe, effective treatment plan: first-line and alternatives (dosing/renal adjustment if relevant), referral when appropriate.
- Potential complications of proposed treatment and expected outcomes/prognosis (cite trials if relevant, e.g., COMS).
- How to communicate the management plan and prognosis to the patient/family (clear, ethical).

End with 1–2 classic examiner follow-up questions (e.g., "How would you discuss prognosis with the patient?" "What if that didn't help? What other treatment might you consider?"). Be concise and board-style."""
                    }
                ],
                max_tokens=1200,
            )
        text = response.choices[0].message.content
        return text.strip(), None
    except Exception as e:
        return None, str(e)


def render_treatment_html(text):
    """Convert treatment markdown to styled HTML with collapsible color-coded sections."""
    import re
    try:
        import markdown
        
        # Split text into sections based on numbered headers
        sections = []
        current_section = {"title": "", "content": "", "class": ""}
        
        lines = text.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check for section headers like "1. Data Acquisition" or "**1. Data Acquisition**"
            header_match = re.match(r'^[*#]*\s*(\d+)\.\s*([^*#\n]+)', line.strip().replace('**', ''))
            if header_match:
                # Save previous section
                if current_section["title"]:
                    sections.append(current_section)
                
                num = header_match.group(1)
                title = header_match.group(2).strip()
                
                # Assign class based on section number
                if num == "1":
                    css_class = "section-data"
                    icon = "📊"
                elif num == "2":
                    css_class = "section-diagnosis"
                    icon = "🔍"
                elif num == "3":
                    css_class = "section-management"
                    icon = "💊"
                else:
                    css_class = "section-questions"
                    icon = "❓"
                
                current_section = {"title": f"{icon} {num}. {title}", "content": "", "class": css_class}
            else:
                current_section["content"] += line + "\n"
            i += 1
        
        # Don't forget the last section
        if current_section["title"]:
            sections.append(current_section)
        
        # Check for follow-up questions at the end (often not numbered)
        if sections and ("follow-up" in sections[-1]["content"].lower() or "examiner" in sections[-1]["content"].lower()):
            # Extract follow-up questions from last section
            last_content = sections[-1]["content"]
            followup_match = re.search(r'((?:examiner|follow.?up)[^\n]*(?:\n.+)*)', last_content, re.IGNORECASE)
            if followup_match:
                followup_text = followup_match.group(1)
                sections[-1]["content"] = last_content[:followup_match.start()]
                sections.append({"title": "❓ Examiner Follow-up Questions", "content": followup_text, "class": "section-questions"})
        
        # Build HTML with collapsible sections
        if sections:
            html_parts = []
            for idx, sec in enumerate(sections):
                content_html = markdown.markdown(sec["content"], extensions=["nl2br", "tables"])
                # First section open by default
                open_attr = "open" if idx == 0 else ""
                html_parts.append(f'''
                <details class="{sec["class"]}" {open_attr}>
                    <summary>{sec["title"]}</summary>
                    <div class="section-content">{content_html}</div>
                </details>
                ''')
            body = "".join(html_parts)
        else:
            # Fallback if no sections detected
            body = markdown.markdown(text, extensions=["nl2br", "tables"])
        
        return f'<div class="treatment-box"><div class="treatment-title">📋 Oral Boards Study Guide</div><div class="treatment-content">{body}</div></div>'
    except Exception:
        # Fallback: escape and wrap in <p> with line breaks
        import html as html_module
        escaped = html_module.escape(text).replace("\n", "<br>")
        return f'<div class="treatment-box"><div class="treatment-title">📋 Oral Boards Study Guide</div><div class="treatment-content"><p>{escaped}</p></div></div>'


# Max width in pixels for clinical images (smaller so more fit on screen)
IMAGE_MAX_WIDTH = 280

def display_images(images, show_captions=False):
    """Display images in a responsive grid, capped size so they're not huge."""
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
        st.image(img['url'], caption=caption, width=IMAGE_MAX_WIDTH)
    elif num_images == 2:
        col1, col2 = st.columns(2)
        with col1:
            img = unique_images[0]
            caption = img['alt'] if (show_captions and img['alt']) else None
            st.image(img['url'], caption=caption, width=IMAGE_MAX_WIDTH)
        with col2:
            img = unique_images[1]
            caption = img['alt'] if (show_captions and img['alt']) else None
            st.image(img['url'], caption=caption, width=IMAGE_MAX_WIDTH)
    else:
        # Multiple images in grid (max 3 columns)
        cols = st.columns(min(3, num_images))
        for i, img in enumerate(unique_images):
            with cols[i % len(cols)]:
                caption = img['alt'] if (show_captions and img['alt']) else None
                st.image(img['url'], caption=caption, width=IMAGE_MAX_WIDTH)


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
    if 'treatment_cache' not in st.session_state:
        st.session_state.treatment_cache = {}
    if 'random_start_done' not in st.session_state:
        st.session_state.random_start_done = False
    
    # Sidebar: search and category (so we have search term before filtering)
    with st.sidebar:
        st.markdown("## 👁️ EyeRounds Study")
        st.markdown("---")
        st.markdown("### 🔍 Keyword search")
        search_term = st.text_input(
            "Search",
            placeholder="e.g. retinitis pigmentosa",
            key="search",
            label_visibility="collapsed"
        )
        search_term = (search_term or "").strip()
        
        st.markdown("### Filter by Topic")
        
        new_category = st.selectbox(
            "Category",
            categories,
            index=categories.index(st.session_state.selected_category) if st.session_state.selected_category in categories else 0,
            key="category_select",
            label_visibility="collapsed"
        )
        
        # Handle category change (pick random card in new category)
        if new_category != st.session_state.selected_category:
            st.session_state.selected_category = new_category
            new_filtered = filter_flashcards(flashcards, new_category)
            new_filtered = filter_by_search(new_filtered, search_term) if search_term else new_filtered
            st.session_state.current_index = random.randint(0, len(new_filtered) - 1) if new_filtered else 0
            st.session_state.show_answer = False
            st.rerun()
    
    # Filter by category, then by search
    category_filtered = filter_flashcards(flashcards, st.session_state.selected_category)
    filtered_cards = filter_by_search(category_filtered, search_term) if search_term else category_filtered
    
    # Clamp current_index when filter shrinks (e.g. search) so selectbox never gets out-of-range index
    if filtered_cards and st.session_state.current_index >= len(filtered_cards):
        st.session_state.current_index = 0
    
    # Start with a random card on first load (and when changing category)
    if filtered_cards and not st.session_state.random_start_done:
        st.session_state.random_start_done = True
        st.session_state.current_index = random.randint(0, len(filtered_cards) - 1)
        st.rerun()
    
    # Keyboard shortcuts via query params (Enter/Space = reveal, ArrowRight = next)
    if "action" in st.query_params:
        action = st.query_params["action"]
        if isinstance(action, list):
            action = action[0] if action else None
        if action == "reveal":
            st.session_state.show_answer = True
        elif action == "next":
            st.session_state.current_index = (st.session_state.current_index + 1) % len(filtered_cards)
            st.session_state.show_answer = False
        elif action == "prev":
            st.session_state.current_index = (st.session_state.current_index - 1) % len(filtered_cards)
            st.session_state.show_answer = False
        # Remove param so we don't loop
        q = dict(st.query_params)
        q.pop("action", None)
        st.query_params.update(q)
        st.rerun()
    
    # Sidebar (continued): stats, navigation, card selector
    with st.sidebar:
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
    
    # Keyboard shortcuts: focusable iframe zone — click it once, then Space/Enter = reveal, ←/→ = prev/next
    st.components.v1.html("""
    <div id="kb-zone" tabindex="0" style="
      outline: none; margin: 0; padding: 6px 10px; font-size: 12px; color: #333;
      background: #e3f2fd; border-radius: 6px; border: 1px solid #90caf9;
      cursor: pointer; text-align: center; font-weight: 500;
    " title="Click here first, then use Space/Enter to reveal, arrows for prev/next">
      ⌨️ Click here first, then: <b>Space</b>/<b>Enter</b> = reveal · <b>←</b> = prev · <b>→</b> = next
    </div>
    <form id="kb-form" method="GET" target="_top" style="display:none;"></form>
    <script>
    (function() {
      var zone = document.getElementById("kb-zone");
      var form = document.getElementById("kb-form");
      function buildUrl(action) {
        var top = window.top;
        var base = (top.location.origin || "") + (top.location.pathname || "/");
        var path = base.split("?")[0];
        return path + "?action=" + action;
      }
      function submitAction(action) {
        try {
          form.action = buildUrl(action);
          form.submit();
        } catch (e) {
          try { window.top.location.href = buildUrl(action); } catch (e2) {}
        }
      }
      zone.addEventListener("click", function() { zone.focus(); });
      zone.addEventListener("keydown", function(e) {
        var k = e.key;
        var isSpace = (k === " " || k === "Spacebar");
        if (k === "Enter" || isSpace) {
          e.preventDefault();
          e.stopPropagation();
          submitAction("reveal");
        } else if (k === "ArrowRight") {
          e.preventDefault();
          e.stopPropagation();
          submitAction("next");
        } else if (k === "ArrowLeft") {
          e.preventDefault();
          e.stopPropagation();
          submitAction("prev");
        }
      });
    })();
    </script>
    """, height=36)
    
    # Header (and search caption when active)
    if search_term:
        st.caption(f"🔍 Showing {len(filtered_cards)} result(s) for \"{search_term}\"")
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
    else:
        # Show answer
        st.markdown("#### ✅ Answer")
        st.markdown(f"**{current_card.get('title', 'Unknown')}**")
        
        description = current_card.get('description') or current_card.get('answer', '')
        if description:
            st.markdown(description)
        
        # Contributor info
        st.markdown("---")
        
        contributor = current_card.get('contributor', '')
        photographer = current_card.get('photographer', '')
        source_url = current_card.get('source_url') or current_card.get('url', '')
        
        if contributor:
            st.markdown(f"**Contributor:** {contributor}")
        if photographer:
            st.markdown(f"**Photographer:** {photographer}")
        if source_url:
            st.markdown(f"**Source:** [{source_url}]({source_url})")
        
        # Oral boards: treatment & next steps (GPT-4o) — runs automatically on reveal
        st.markdown("---")
        card_id = current_card.get("id", current_card.get("title", ""))
        cached = st.session_state.treatment_cache.get(card_id)
        
        if cached:
            st.markdown(render_treatment_html(cached), unsafe_allow_html=True)
        elif OPENAI_API_KEY and OPENAI_API_KEY.strip() != "your_openai_api_key_here":
            with st.spinner("Getting treatment & next steps..."):
                text, err = get_oral_boards_treatment(current_card)
            if err:
                st.error(err)
            else:
                st.session_state.treatment_cache[card_id] = text
                st.markdown(render_treatment_html(text), unsafe_allow_html=True)
        else:
            st.caption("Oral boards treatment not loaded — if you're the app owner, add OPENAI_API_KEY in Streamlit Cloud → Settings → Secrets once; then it works for everyone.")
        
    # Floating Prev / Next buttons (always visible, no scrolling needed)
    st.markdown("""
    <a href="?action=prev" class="floating-prev-btn" title="Previous Card">⬅️ Prev</a>
    <a href="?action=next" class="floating-next-btn" title="Next Card">Next ➡️</a>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
