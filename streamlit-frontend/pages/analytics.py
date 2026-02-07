import streamlit as st
from utils.api_client import APIClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show():
    """Analytics and performance page"""
    
    st.markdown("## 📊 Conversation Analytics")
    st.markdown("Analyze your sales conversation performance and get insights")
    
    api_client = APIClient(st.session_state.api_base_url)
    
    # Check if meeting exists
    if not st.session_state.meeting_id:
        st.error("❌ No active meeting. Please create and complete a meeting first.")
        return
    
    # Load meeting and conversation data
    with st.spinner("Loading analytics..."):
        try:
            # Get meeting details
            meeting_result = api_client.get_meeting(st.session_state.meeting_id)
            
            if not meeting_result.get("success"):
                st.error("Error loading meeting")
                return
            
            meeting = meeting_result["data"]
            
            # Get conversation analytics
            analytics_result = api_client.get_conversation_analytics(st.session_state.meeting_id)
            
            if not analytics_result.get("success"):
                st.info("No conversation data available yet")
                return
            
            analytics = analytics_result["data"]
            
        except Exception as e:
            st.error(f"Error: {e}")
            return
    
    # Meeting Overview
    st.markdown("### 📋 Meeting Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Meeting Mode", meeting.get("meeting_mode", "N/A"))
    with col2:
        st.metric("Status", meeting.get("status", "N/A").title())
    with col3:
        st.metric("Difficulty", meeting.get("difficulty", "N/A").title())
    with col4:
        st.metric("Duration", f"{meeting.get('duration_minutes', 'N/A')} min")
    
    st.markdown("---")
    
    # Key Metrics
    st.markdown("### 📈 Key Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Turns",
            analytics.get("total_turns", 0),
            help="Total number of conversation exchanges"
        )
    
    with col2:
        st.metric(
            "Your Turns",
            analytics.get("salesperson_turns", 0),
            help="Number of times you spoke"
        )
    
    with col3:
        st.metric(
            "AI Turns",
            analytics.get("ai_turns", 0),
            help="Number of times AI representatives responded"
        )
    
    with col4:
        st.metric(
            "Questions Asked",
            analytics.get("questions_asked", 0),
            help="Number of questions you asked"
        )
    
    st.markdown("---")
    
    # Talk Time Analysis
    st.markdown("### ⏱️ Talk Time Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Talk time metrics
        your_time = analytics.get("salesperson_talk_time", 0)
        ai_time = analytics.get("representatives_talk_time", 0)
        total_time = analytics.get("total_duration", 0)
        
        st.metric("Your Talk Time", f"{your_time:.1f}s")
        st.metric("AI Talk Time", f"{ai_time:.1f}s")
        st.metric("Total Duration", f"{total_time:.1f}s")
        
        # Talk ratio analysis
        your_ratio = analytics.get("salesperson_talk_ratio", 0)
        ai_ratio = analytics.get("representatives_talk_ratio", 0)
        
        st.markdown("**Talk Time Distribution:**")
        st.progress(your_ratio / 100, text=f"You: {your_ratio:.1f}%")
        st.progress(ai_ratio / 100, text=f"AI: {ai_ratio:.1f}%")
        
        # Recommendations
        st.markdown("---")
        st.markdown("**💡 Recommendations:**")
        
        if your_ratio > 70:
            st.warning("⚠️ You're talking too much! Best practice is 40-60%. Try asking more open-ended questions.")
        elif your_ratio < 30:
            st.warning("⚠️ You're not talking enough! Engage more actively. Share value propositions and ask questions.")
        else:
            st.success("✅ Good balance! You're maintaining healthy conversation flow.")
    
    with col2:
        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['Your Talk Time', 'AI Talk Time'],
            values=[your_time, ai_time],
            hole=.3,
            marker_colors=['#1f77b4', '#ff7f0e']
        )])
        
        fig.update_layout(
            title="Talk Time Distribution",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Conversation Flow
    st.markdown("### 💬 Conversation Flow")
    
    # Get full conversation history
    history_result = api_client.get_conversation_history(st.session_state.meeting_id)
    
    if history_result.get("success"):
        turns = history_result["data"].get("turns", [])
        
        if turns:
            # Create conversation flow visualization
            turn_numbers = []
            speakers = []
            durations = []
            
            for turn in turns:
                turn_numbers.append(turn.get("turn_number", 0))
                speakers.append(turn.get("speaker_name", "Unknown"))
                durations.append(turn.get("duration_seconds", 0))
            
            # Bar chart of turn durations
            df = pd.DataFrame({
                'Turn': turn_numbers,
                'Speaker': speakers,
                'Duration (s)': durations
            })
            
            fig = px.bar(
                df,
                x='Turn',
                y='Duration (s)',
                color='Speaker',
                title='Turn Duration by Speaker',
                labels={'Turn': 'Turn Number', 'Duration (s)': 'Duration (seconds)'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Turn-by-turn analysis
            st.markdown("### 📝 Turn-by-Turn Analysis")
            
            for turn in turns:
                with st.expander(
                    f"Turn {turn.get('turn_number', 0)}: {turn.get('speaker_name', 'Unknown')} "
                    f"({turn.get('duration_seconds', 0):.1f}s)"
                ):
                    st.markdown(f"**Speaker:** {turn.get('speaker_name', 'Unknown')}")
                    st.markdown(f"**Time:** {turn.get('timestamp', 'N/A')}")
                    st.markdown(f"**Duration:** {turn.get('duration_seconds', 0):.1f} seconds")
                    st.markdown("**Message:**")
                    st.info(turn.get("text", ""))
                    
                    if turn.get("audio_url"):
                        st.audio(turn["audio_url"])
        else:
            st.info("No conversation turns recorded yet")
    
    st.markdown("---")
    
    # Performance Scoring
    st.markdown("### 🎯 Performance Score")
    
    # Calculate performance score
    score = calculate_performance_score(analytics)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Overall Score", f"{score}/100")
        
        if score >= 80:
            st.success("🌟 Excellent Performance!")
        elif score >= 60:
            st.info("👍 Good Performance!")
        elif score >= 40:
            st.warning("📈 Needs Improvement")
        else:
            st.error("❌ Needs Significant Improvement")
    
    with col2:
        st.markdown("**Score Breakdown:**")
        
        # Talk ratio score
        talk_ratio_score = calculate_talk_ratio_score(analytics.get("salesperson_talk_ratio", 0))
        st.progress(talk_ratio_score / 100, text=f"Talk Ratio: {talk_ratio_score}/100")
        
        # Engagement score
        engagement_score = calculate_engagement_score(analytics)
        st.progress(engagement_score / 100, text=f"Engagement: {engagement_score}/100")
        
        # Question score
        question_score = calculate_question_score(analytics)
        st.progress(question_score / 100, text=f"Questions Asked: {question_score}/100")
    
    st.markdown("---")
    
    # Strategic Questions Review
    st.markdown("### 🎯 Strategic Questions Review")
    
    if meeting.get("top_5_questions"):
        st.info("These were the AI-generated strategic questions for this meeting:")
        
        for i, question in enumerate(meeting["top_5_questions"], 1):
            st.markdown(f"**{i}.** {question}")
        
        st.markdown("**💡 Reflection:**")
        st.text_area(
            "Did you cover these questions? What would you do differently?",
            height=100,
            key="reflection"
        )
    
    st.markdown("---")
    
    # Export Options
    st.markdown("### 📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export Transcript", use_container_width=True):
            st.info("Feature coming soon!")
    
    with col2:
        if st.button("📊 Export Analytics", use_container_width=True):
            st.info("Feature coming soon!")
    
    with col3:
        if st.button("🎧 Download Audio", use_container_width=True):
            st.info("Feature coming soon!")


def calculate_performance_score(analytics):
    """Calculate overall performance score"""
    
    # Talk ratio score (40% of total)
    talk_ratio_score = calculate_talk_ratio_score(analytics.get("salesperson_talk_ratio", 0))
    
    # Engagement score (30% of total)
    engagement_score = calculate_engagement_score(analytics)
    
    # Question score (30% of total)
    question_score = calculate_question_score(analytics)
    
    # Weighted average
    total_score = (talk_ratio_score * 0.4) + (engagement_score * 0.3) + (question_score * 0.3)
    
    return round(total_score)


def calculate_talk_ratio_score(talk_ratio):
    """Score based on talk time ratio (ideal: 40-60%)"""
    
    if 40 <= talk_ratio <= 60:
        return 100
    elif 30 <= talk_ratio < 40 or 60 < talk_ratio <= 70:
        return 80
    elif 20 <= talk_ratio < 30 or 70 < talk_ratio <= 80:
        return 60
    else:
        return 40


def calculate_engagement_score(analytics):
    """Score based on conversation engagement"""
    
    total_turns = analytics.get("total_turns", 0)
    
    if total_turns >= 20:
        return 100
    elif total_turns >= 15:
        return 90
    elif total_turns >= 10:
        return 75
    elif total_turns >= 5:
        return 60
    else:
        return 40


def calculate_question_score(analytics):
    """Score based on questions asked"""
    
    questions = analytics.get("questions_asked", 0)
    total_turns = analytics.get("salesperson_turns", 1)
    
    question_ratio = (questions / total_turns) * 100
    
    if question_ratio >= 40:  # Asking questions in 40%+ of turns
        return 100
    elif question_ratio >= 30:
        return 85
    elif question_ratio >= 20:
        return 70
    elif question_ratio >= 10:
        return 55
    else:
        return 40