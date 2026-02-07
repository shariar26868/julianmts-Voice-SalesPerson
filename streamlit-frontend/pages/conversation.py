import streamlit as st
from utils.api_client import APIClient
import time
from datetime import datetime

def show():
    """Live conversation page"""
    
    st.markdown("## 🎙️ Live Conversation")
    st.markdown("Practice your sales pitch with AI representatives in real-time")
    
    api_client = APIClient(st.session_state.api_base_url)
    
    # Check prerequisites
    if not st.session_state.meeting_id:
        st.error("❌ Please create a meeting first")
        st.info("👉 Go to 'Meeting Setup' to create a new meeting")
        return
    
    # Get meeting details
    with st.spinner("Loading meeting..."):
        try:
            result = api_client.get_meeting(st.session_state.meeting_id)
            
            if not result.get("success"):
                st.error("Error loading meeting")
                return
            
            meeting = result["data"]
            
        except Exception as e:
            st.error(f"Error: {e}")
            return
    
    # Meeting header
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mode", meeting.get("meeting_mode", "N/A"))
    with col2:
        st.metric("Status", meeting.get("status", "N/A").title())
    with col3:
        st.metric("Difficulty", meeting.get("difficulty", "N/A").title())
    with col4:
        st.metric("Duration", f"{meeting.get('duration_minutes', 30)} min")
    
    # Representatives info
    st.markdown("### 👥 Meeting Participants")
    
    cols = st.columns(len(meeting.get("representatives", [])))
    
    for i, rep in enumerate(meeting.get("representatives", [])):
        with cols[i]:
            st.markdown(f"""
            **{rep['name']}**  
            {rep['role'].upper().replace('_', ' ')}
            
            Traits: {', '.join([t.replace('_', ' ').title() for t in rep.get('personality_traits', [])])}
            
            {'🎯 Decision Maker' if rep.get('is_decision_maker') else ''}
            """)
    
    st.markdown("---")
    
    # Meeting controls
    if meeting.get("status") == "pending":
        st.warning("⚠️ Meeting not started yet")
        if st.button("▶️ Start Meeting", use_container_width=True, type="primary"):
            try:
                api_client.start_meeting(st.session_state.meeting_id)
                st.session_state.meeting_active = True
                st.success("Meeting started!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        return
    
    elif meeting.get("status") == "completed":
        st.info("✅ This meeting has ended. Check 'Analytics' tab for results.")
        return
    
    # Active meeting
    st.success("🟢 Meeting is Active")
    
    # Conversation mode tabs
    tab1, tab2, tab3 = st.tabs(["💬 Text Chat", "🎤 Voice (WebSocket)", "📜 History"])
    
    with tab1:
        show_text_conversation(api_client, meeting)
    
    with tab2:
        show_voice_conversation(api_client, meeting)
    
    with tab3:
        show_conversation_history(api_client, meeting)
    
    # End meeting button
    st.markdown("---")
    if st.button("⏹️ End Meeting", use_container_width=True):
        try:
            api_client.end_meeting(st.session_state.meeting_id)
            st.session_state.meeting_active = False
            st.success("Meeting ended!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")


def show_text_conversation(api_client, meeting):
    """Text-based conversation"""
    
    st.markdown("### 💬 Text Conversation")
    st.info("Type your message and get AI responses. No voice/audio recording needed.")
    
    # Initialize conversation history in session state
    if 'conversation_turns' not in st.session_state:
        st.session_state.conversation_turns = []
    
    # Display conversation history
    if st.session_state.conversation_turns:
        st.markdown("### 📝 Conversation")
        
        for turn in st.session_state.conversation_turns:
            speaker = turn.get("speaker_name", "Unknown")
            text = turn.get("text", "")
            role = turn.get("speaker_role", "")
            
            if turn.get("speaker") == "salesperson":
                st.markdown(f"""
                <div style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>You (Salesperson):</strong><br>
                    {text}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>{speaker}</strong> ({role.upper().replace('_', ' ')}):<br>
                    {text}
                </div>
                """, unsafe_allow_html=True)
    
    # Message input
    st.markdown("---")
    
    with st.form("message_form", clear_on_submit=True):
        message = st.text_area(
            "Your Message",
            placeholder="Type your message here...",
            height=100,
            key="message_input"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submit = st.form_submit_button("Send Message", use_container_width=True, type="primary")
        
        with col2:
            clear = st.form_submit_button("Clear History", use_container_width=True)
    
    if clear:
        st.session_state.conversation_turns = []
        st.rerun()
    
    if submit and message:
        with st.spinner("🤖 AI is thinking and responding..."):
            try:
                # Add salesperson message to history
                salesperson_turn = {
                    "speaker": "salesperson",
                    "speaker_name": "You",
                    "text": message,
                    "speaker_role": "salesperson"
                }
                
                # Send message to backend
                result = api_client.send_message(
                    meeting_id=st.session_state.meeting_id,
                    speaker="salesperson",
                    message=message
                )
                
                if result.get("success"):
                    # Add to local history
                    st.session_state.conversation_turns.append(salesperson_turn)
                    
                    # Get AI response
                    ai_response = result["data"]["ai_response"]
                    
                    ai_turn = {
                        "speaker": ai_response["speaker_id"],
                        "speaker_name": ai_response["speaker_name"],
                        "speaker_role": ai_response.get("speaker_role", ""),
                        "text": ai_response["response_text"]
                    }
                    
                    st.session_state.conversation_turns.append(ai_turn)
                    
                    # Show success and rerun to display
                    st.success("✅ Response received!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
            
            except Exception as e:
                st.error(f"Error: {e}")


def show_voice_conversation(api_client, meeting):
    """Voice conversation with WebSocket"""
    
    st.markdown("### 🎤 Live Voice Conversation")
    
    st.warning("""
    ⚠️ **WebSocket Voice Feature**
    
    This feature requires:
    1. WebSocket connection to backend
    2. Browser microphone access
    3. Real-time audio streaming
    
    **Currently in Development**
    
    For now, please use the **Text Chat** tab for conversations.
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### How Voice Conversation Will Work:
    
    1. **Connect:** Click "Start Voice Session" to open WebSocket connection
    2. **Speak:** Click microphone button and speak your message
    3. **AI Responds:** AI processes speech → generates response → plays audio
    4. **Continue:** Have a natural back-and-forth conversation
    
    **Technical Flow:**
    - Your voice → Whisper STT → GPT-4 → ElevenLabs TTS → Audio playback
    - All in real-time via WebSocket
    """)
    
    st.info("""
    💡 **Alternative:** Use Text Chat for now, which provides the same AI conversation 
    experience without requiring audio hardware setup.
    """)


def show_conversation_history(api_client, meeting):
    """Show full conversation history from backend"""
    
    st.markdown("### 📜 Complete Conversation History")
    
    if st.button("🔄 Refresh History"):
        st.rerun()
    
    with st.spinner("Loading conversation history..."):
        try:
            result = api_client.get_conversation_history(st.session_state.meeting_id)
            
            if result.get("success"):
                data = result["data"]
                turns = data.get("turns", [])
                
                if turns:
                    # Stats
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Turns", data.get("total_turns", 0))
                    with col2:
                        st.metric("Your Talk Time", f"{data.get('salesperson_talk_time', 0):.1f}s")
                    with col3:
                        st.metric("AI Talk Time", f"{data.get('representatives_talk_time', 0):.1f}s")
                    
                    st.markdown("---")
                    
                    # Display turns
                    for turn in turns:
                        timestamp = turn.get("timestamp", "00:00:00")
                        speaker_name = turn.get("speaker_name", "Unknown")
                        text = turn.get("text", "")
                        
                        if turn.get("speaker") == "salesperson":
                            st.markdown(f"""
                            <div style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0;">
                                <small style="color: #666;">[{timestamp}]</small><br>
                                <strong>You (Salesperson):</strong><br>
                                {text}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
                                <small style="color: #666;">[{timestamp}]</small><br>
                                <strong>{speaker_name}:</strong><br>
                                {text}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Audio playback if available
                        if turn.get("audio_url"):
                            st.audio(turn["audio_url"])
                else:
                    st.info("No conversation history yet. Start chatting in the Text Chat tab!")
            
            else:
                st.error("Error loading history")
        
        except Exception as e:
            st.error(f"Error: {e}")