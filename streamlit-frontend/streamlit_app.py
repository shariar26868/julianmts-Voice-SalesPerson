import streamlit as st
from streamlit_option_menu import option_menu
import sys
from pathlib import Path

# Add pages to path
sys.path.append(str(Path(__file__).parent))

# Page config
st.set_page_config(
    page_title="AI Sales Training Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #155a8a;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_base_url' not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8000"

if 'salesperson_id' not in st.session_state:
    st.session_state.salesperson_id = None

if 'company_id' not in st.session_state:
    st.session_state.company_id = None

if 'meeting_id' not in st.session_state:
    st.session_state.meeting_id = None

if 'meeting_active' not in st.session_state:
    st.session_state.meeting_active = False

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🎯 AI Sales Training")
    st.markdown("---")
    
    selected = option_menu(
        menu_title=None,
        options=[
            "Home",
            "Salesperson Setup",
            "Company Setup", 
            "Meeting Setup",
            "Live Conversation",
            "Analytics"
        ],
        icons=[
            "house",
            "person-badge",
            "building",
            "calendar-event",
            "mic",
            "graph-up"
        ],
        menu_icon="cast",
        default_index=0,
    )
    
    st.markdown("---")
    
    # API Configuration
    with st.expander("⚙️ API Settings"):
        api_url = st.text_input(
            "Backend API URL",
            value=st.session_state.api_base_url,
            help="FastAPI backend URL"
        )
        if st.button("Update API URL"):
            st.session_state.api_base_url = api_url
            st.success("API URL updated!")
    
    # Session Info
    st.markdown("---")
    st.markdown("### 📊 Session Info")
    
    if st.session_state.salesperson_id:
        st.success(f"✅ Salesperson: {st.session_state.salesperson_id[:8]}...")
    else:
        st.info("ℹ️ No salesperson setup")
    
    if st.session_state.company_id:
        st.success(f"✅ Company: {st.session_state.company_id[:8]}...")
    else:
        st.info("ℹ️ No company setup")
    
    if st.session_state.meeting_id:
        st.success(f"✅ Meeting: {st.session_state.meeting_id[:8]}...")
        if st.session_state.meeting_active:
            st.success("🟢 Meeting Active")
        else:
            st.warning("🟡 Meeting Pending")
    else:
        st.info("ℹ️ No meeting setup")

# Main content area
if selected == "Home":
    from pages import home
    home.show()

elif selected == "Salesperson Setup":
    from pages import salesperson
    salesperson.show()

elif selected == "Company Setup":
    from pages import company
    company.show()

elif selected == "Meeting Setup":
    from pages import meeting
    meeting.show()

elif selected == "Live Conversation":
    from pages import conversation
    conversation.show()

elif selected == "Analytics":
    from pages import analytics
    analytics.show()