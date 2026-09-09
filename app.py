from pathlib import Path
import streamlit as st
from home_view import render_overview_page
from utils.ui import render_sidebar_header, render_sidebar_footer
from seed_data import seed_database

# 1. Page Config
st.set_page_config(
    page_title="Cricbuzz Analytics Hub",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Icon Map
ICON_MAP = {
    "visual": "📊",
    "match": "🔴",
    "leaderboards": "🏆",
    "SQL": "🔍",
    "data": "🛠️"
}

# 3. Define Overview Page
Overview_page = st.Page(render_overview_page, title="Overview", icon="🏠", default=True)

# Build Navigation List containing tuples: (st_page_object, icon, display_title)
nav_items = [(Overview_page, "🏠", "Overview")]

# 4. Automatically scan pages/ directory
pages_dir = Path("pages")
if pages_dir.exists():
    for file in sorted(pages_dir.glob("*.py")):
        clean_name = file.stem
        title_words = [w for w in clean_name.split("_") if not w.isdigit()]
        display_title = " ".join(title_words).title() if title_words else clean_name

        icon = "📄"
        for key, ico in ICON_MAP.items():
            if key in clean_name.lower():
                icon = ico
                break

        # Pass icon into st.Page
        page_obj = st.Page(str(file), title=display_title, icon=icon)
        nav_items.append((page_obj, icon, display_title))

# 5. Hide Default Streamlit Navigation Bar
nav_pages = [item[0] for item in nav_items]
pg = st.navigation(nav_pages, position="hidden")

# 6. Global Sidebar Header
render_sidebar_header()

# 7. Sidebar Navigation Links (Renders EXACTLY one icon)
with st.sidebar:
    st.caption("DASHBOARD NAVIGATION")
    for page_obj, icon, title in nav_items:
        st.page_link(page_obj, label=title, icon=icon)

# 8. Global Sidebar Footer
render_sidebar_footer()

# Cache the seed function so it runs ONCE when the app launches, not on every page refresh
@st.cache_resource
def initialize_database():
    seed_database()

initialize_database()

# 9. Execute Selected Page View
pg.run()