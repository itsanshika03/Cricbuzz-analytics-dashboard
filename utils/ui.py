import base64
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"


def get_logo_file():
    """Finds any image logo file saved inside the assets directory."""
    if not ASSETS_DIR.exists():
        return None

    for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
        files = list(ASSETS_DIR.glob(ext))
        if files:
            return str(files[0])
    return None


def get_base64_image(file_path):
    """Converts a local image file to a base64 string for CSS embedding."""
    if not file_path:
        return ""
    path = Path(file_path)
    if path.exists():
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            ext = path.suffix.lower().replace(".", "")
            mime_type = "image/png" if ext in ["png", "webp"] else "image/jpeg"
            return f"data:{mime_type};base64,{encoded}"
    return ""


def apply_global_cricbuzz_theme():
    """Applies global dark theme styling along with watermark background."""
    # Auto-detect logo from assets directory
    logo_path = get_logo_file()
    logo_base64 = get_base64_image(logo_path)

    bg_css = f"url('{logo_base64}')" if logo_base64 else "none"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* Force background onto Streamlit's true main view container */
        [data-testid="stAppViewContainer"] {{
            background-color: #121316 !important;
            background-image: 
                linear-gradient(rgba(18, 19, 22, 0.83), rgba(18, 19, 22, 0.83)), 
                {bg_css} !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-attachment: fixed !important;
            background-size: auto, 450px !important; /* Slightly enlarged for better presence */
            font-family: 'Inter', sans-serif !important;
            color: #E2E8F0 !important;
        }}

        header[data-testid="stHeader"] {{
            background-color: transparent !important;
        }}

        /* Sidebar Container Styling */
        [data-testid="stSidebar"] {{
            background-color: #16181D !important;
            border-right: 1px solid #282C37 !important;
        }}

        /* --- SIDEBAR HOVER & CLICK / ACTIVE STATES --- */

        /* Targets standard Streamlit sidebar page links */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a,
        [data-testid="stSidebarNav"] a {{
            border-radius: 8px !important;
            margin: 3px 8px !important;
            padding: 8px 12px !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
            color: #94A3B8 !important;
            transition: all 0.25s ease-in-out !important;
            display: flex !important;
            align-items: center !important;
            text-decoration: none !important;
        }}

        /* Smooth Hover state when mouse moves over any page link */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
        [data-testid="stSidebarNav"] a:hover {{
            background-color: #232733 !important;
            color: #00D2C4 !important;
            transform: translateX(4px); /* Subtle slide effect on hover */
            box-shadow: 0 2px 8px rgba(0, 210, 196, 0.15) !important;
        }}

        /* Clicked / Active page highlight */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: linear-gradient(90deg, rgba(0, 210, 196, 0.2) 0%, rgba(0, 210, 196, 0.02) 100%) !important;
            border-left: 4px solid #00D2C4 !important;
            color: #00D2C4 !important;
            font-weight: 700 !important;
        }}

        /* Active click effect (When button is being clicked down) */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:active,
        [data-testid="stSidebarNav"] a:active {{
            background-color: rgba(0, 210, 196, 0.25) !important;
            transform: scale(0.98) !important;
        }}

        /* Streamlit Native Navigation Menu */
        [data-testid="stSidebarNav"] {{
            padding-top: 0.5rem !important;
        }}

        [data-testid="stSidebarNav"] a {{
            border-radius: 8px !important;
            margin: 2px 8px !important;
            padding: 10px 14px !important;
            font-size: 0.95rem !important;
            color: #94A3B8 !important;
            transition: all 0.2s ease-in-out;
        }}

        [data-testid="stSidebarNav"] a:hover {{
            background-color: #252833 !important;
            color: #00D2C4 !important;
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: linear-gradient(90deg, rgba(0, 210, 196, 0.15) 0%, rgba(0, 210, 196, 0) 100%) !important;
            border-left: 4px solid #00D2C4 !important;
            color: #00D2C4 !important;
            font-weight: 700 !important;
        }}

        /* Custom Sidebar Page Links Font Size */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {{
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            padding: 6px 10px !important;
            border-radius: 6px !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
            background-color: rgba(255, 255, 255, 0.08) !important;
        }}

        /* Live Badge */
        .live-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: rgba(0, 229, 153, 0.12);
            color: #00E599;
            border: 1px solid rgba(0, 229, 153, 0.3);
            border-radius: 12px;
            padding: 5px 14px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.04em;
        }}

        .live-dot {{
            width: 8px;
            height: 8px;
            background-color: #00E599;
            border-radius: 50%;
            box-shadow: 0 0 8px #00E599;
        }}

        /* Dashboard Cards */
        .dashboard-card {{
            background-color: rgba(28, 30, 36, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid #2B2F3A;
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }}

        .kpi-title {{
            color: #94A3B8;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.2rem;
        }}

        .kpi-value-cyan {{
            color: #00D2C4;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
        }}

        .kpi-value-green {{
            color: #00E599;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
        }}

        /* Search Input */
        div[data-baseweb="input"] > div {{
            background-color: #1C1E24 !important;
            border: 1px solid #2B2F3A !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
        }}

        /* Transparent Logo Filter */
        [data-testid="stSidebar"] [data-testid="stImage"] img {{
            background-color: transparent !important;
            border-radius: 0px !important;
            padding: 0px !important;
            filter: drop-shadow(0px 0px 6px rgba(0, 210, 196, 0.3));
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_header():
    """Renders logo and API status inside sidebar strictly without page_link calls."""
    logo_path = get_logo_file()

    with st.sidebar:
        col1, col2 = st.columns([1.1, 2.0], gap="small")

        with col1:
            if logo_path:
                st.image(logo_path, use_container_width=True)
            else:
                st.markdown("🏏")

        with col2:
            st.markdown(
                """
                <div style="line-height: 1.15; padding-top: 4px;">
                    <div style="color: #FFFFFF; font-weight: 900; font-size: 1.55rem; letter-spacing: -0.03em;">
                        CRICBUZZ <span style="color: #00D2C4;">PRO</span>
                    </div>
                    <div style="color: #94A3B8; font-size: 0.8rem; font-weight: 500; margin-top: 3px;">
                        Live Analytics Console
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div style="margin-top: 10px; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid #282C37;">
                <span class="live-badge"><span class="live-dot"></span> API CONNECTED</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar_footer():
    """Renders metadata at the bottom of the sidebar."""
    st.sidebar.markdown(
        """
        <div style="padding: 1rem 0.5rem; border-top: 1px solid #282C37; margin-top: 2rem;">
            <p style="color: #64748B; font-size: 0.72rem; margin: 0; line-height: 1.5;">
                <strong>Database Context:</strong> SQLite LiveStats<br>
                <strong>Engine:</strong> Streamlit v1.x
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )