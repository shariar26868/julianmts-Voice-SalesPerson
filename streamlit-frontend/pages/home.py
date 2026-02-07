import streamlit as st

def show():
    """Home page with platform overview and quick start guide"""
    
    st.markdown('<h1 class="main-header">🎯 AI Sales Training Platform</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to the Multi-Agent AI Sales Training Platform
    
    Practice your sales conversations with realistic AI-powered company representatives. 
    Get real-time feedback and improve your sales skills!
    """)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Setup Stage", "🚀 Ready", delta="Start Here")
    
    with col2:
        salesperson_status = "✅ Done" if st.session_state.salesperson_id else "⏳ Pending"
        st.metric("Salesperson", salesperson_status)
    
    with col3:
        company_status = "✅ Done" if st.session_state.company_id else "⏳ Pending"
        st.metric("Company", company_status)
    
    with col4:
        meeting_status = "✅ Ready" if st.session_state.meeting_id else "⏳ Pending"
        st.metric("Meeting", meeting_status)
    
    st.markdown("---")
    
    # Quick Start Guide
    st.markdown("### 📚 Quick Start Guide")
    
    with st.expander("🔍 How It Works", expanded=True):
        st.markdown("""
        #### Step 1: Salesperson Setup
        - Enter your product/service details
        - Upload product materials (optional)
        - This helps AI understand what you're selling
        
        #### Step 2: Company Setup  
        - Add target company URL
        - AI automatically scrapes company data
        - Add company representatives with personalities
        
        #### Step 3: Meeting Setup
        - Choose meeting mode (1-on-1, 1-on-2, 1-on-3)
        - Set meeting goals and difficulty
        - AI generates top 5 strategic questions
        
        #### Step 4: Live Conversation
        - Real-time voice or text conversation
        - Multiple AI representatives respond based on context
        - Each rep has unique personality and role
        
        #### Step 5: Review Analytics
        - Conversation analysis
        - Talk time ratios
        - Performance metrics
        """)
    
    with st.expander("✨ Key Features"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🤖 Multi-Agent AI**
            - Multiple representatives in one meeting
            - Realistic personality traits
            - Context-aware responses
            
            **🎙️ Real-time Voice**
            - Live voice conversations
            - Speech-to-text with Whisper
            - Text-to-speech with ElevenLabs
            
            **📊 Smart Analytics**
            - Talk time tracking
            - Question analysis
            - Performance scoring
            """)
        
        with col2:
            st.markdown("""
            **🌐 AI-Powered Research**
            - Automatic company data scraping
            - Tech stack detection
            - Industry analysis
            
            **🎯 Personalization**
            - Custom meeting goals
            - Difficulty levels
            - Role-based interactions
            
            **💾 Complete History**
            - Conversation recordings
            - Turn-by-turn transcripts
            - Audio playback
            """)
    
    st.markdown("---")
    
    # Getting Started
    st.markdown("### 🚀 Getting Started")
    
    if not st.session_state.salesperson_id:
        st.info("👉 **Next Step:** Go to 'Salesperson Setup' to configure your product details")
    elif not st.session_state.company_id:
        st.info("👉 **Next Step:** Go to 'Company Setup' to add your target company")
    elif not st.session_state.meeting_id:
        st.info("👉 **Next Step:** Go to 'Meeting Setup' to create a new meeting")
    else:
        st.success("✅ **All Set!** Go to 'Live Conversation' to start practicing")
    
    st.markdown("---")
    
    # System Status
    st.markdown("### 🔧 System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Backend API**")
        import requests
        try:
            response = requests.get(f"{st.session_state.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("🟢 Connected")
            else:
                st.error("🔴 Error")
        except:
            st.error("🔴 Offline")
    
    with col2:
        st.markdown("**MongoDB**")
        try:
            response = requests.get(f"{st.session_state.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("database") == "connected":
                    st.success("🟢 Connected")
                else:
                    st.error("🔴 Disconnected")
            else:
                st.error("🔴 Error")
        except:
            st.error("🔴 Offline")
    
    with col3:
        st.markdown("**WebSocket**")
        st.info("⚪ Not Connected")
    
    st.markdown("---")
    
    # Help & Support
    with st.expander("❓ Help & Support"):
        st.markdown("""
        **Common Issues:**
        
        1. **Backend Not Connected**
           - Make sure FastAPI backend is running on port 8000
           - Check API URL in sidebar settings
           - Run: `uvicorn app.main:app --reload`
        
        2. **WebSocket Connection Failed**
           - Backend must be running
           - Check firewall settings
           - Use localhost or proper IP address
        
        3. **Audio Not Working**
           - Check browser microphone permissions
           - Ensure ElevenLabs API key is configured
           - Test with text mode first
        
        4. **Company Data Not Loading**
           - Verify company URL is accessible
           - Check API keys (Google, PageSpeed)
           - May take 30-60 seconds to scrape
        
        **Need Help?**
        - Check backend logs for errors
        - Verify all API keys in `.env` file
        - Contact support for assistance
        """)
    
    st.markdown("---")
    st.markdown("**💡 Tip:** Start with a simple 1-on-1 meeting on beginner difficulty to get familiar with the platform!")