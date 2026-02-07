import streamlit as st
from utils.api_client import APIClient

def show():
    """Meeting setup page"""
    
    st.markdown("## 📅 Meeting Setup")
    st.markdown("Configure your sales meeting with AI representatives")
    
    api_client = APIClient(st.session_state.api_base_url)
    
    # Check prerequisites
    if not st.session_state.salesperson_id:
        st.error("❌ Please create a salesperson profile first")
        return
    
    if not st.session_state.company_id:
        st.error("❌ Please create a company profile first")
        return
    
    # Tabs
    tab1, tab2 = st.tabs(["➕ Create Meeting", "📋 View Meetings"])
    
    with tab1:
        st.markdown("### Create New Meeting")
        
        # Get company representatives
        with st.spinner("Loading representatives..."):
            try:
                reps_result = api_client.get_company_representatives(st.session_state.company_id)
                
                if not reps_result.get("success"):
                    st.error("Error loading representatives")
                    return
                
                representatives = reps_result["data"].get("representatives", [])
                
                if not representatives:
                    st.error("❌ No representatives found. Please add representatives to the company first.")
                    return
                
            except Exception as e:
                st.error(f"Error: {e}")
                return
        
        with st.form("meeting_form"):
            # Meeting Mode
            meeting_mode = st.selectbox(
                "Meeting Mode *",
                options=["1-on-1", "1-on-2", "1-on-3"],
                help="How many company representatives will be in the meeting?"
            )
            
            # Select representatives
            mode_count = int(meeting_mode.split("-")[1])
            
            st.markdown(f"**Select {mode_count} Representative(s) ***")
            
            rep_options = {f"{rep['name']} ({rep['role'].upper().replace('_', ' ')})": rep['id'] 
                          for rep in representatives}
            
            selected_reps = st.multiselect(
                "Representatives",
                options=list(rep_options.keys()),
                max_selections=mode_count,
                help=f"Select exactly {mode_count} representative(s) for this meeting"
            )
            
            # Meeting details
            col1, col2 = st.columns(2)
            
            with col1:
                difficulty = st.selectbox(
                    "Difficulty Level *",
                    options=["beginner", "intermediate", "advanced"],
                    format_func=lambda x: x.title(),
                    help="Beginner: Friendly, cooperative. Advanced: Challenging, skeptical"
                )
                
                duration = st.number_input(
                    "Duration (minutes) *",
                    min_value=5,
                    max_value=120,
                    value=30,
                    step=5
                )
            
            with col2:
                personality = st.selectbox(
                    "Overall Meeting Tone *",
                    options=["nice", "analytical", "arrogant", "cold_hearted", "soft", "cool"],
                    format_func=lambda x: x.replace("_", " ").title(),
                    help="General tone/atmosphere of the meeting"
                )
            
            meeting_goal = st.text_area(
                "Meeting Goal *",
                placeholder="e.g., Book a product demo, Get commitment for pilot program, Close deal, etc.",
                height=100,
                help="What are you trying to achieve in this meeting?"
            )
            
            submit = st.form_submit_button("Create Meeting", use_container_width=True, type="primary")
        
        if submit:
            if not selected_reps:
                st.error(f"❌ Please select {mode_count} representative(s)")
            elif len(selected_reps) != mode_count:
                st.error(f"❌ Please select exactly {mode_count} representative(s) for {meeting_mode} mode")
            elif not meeting_goal:
                st.error("❌ Please enter a meeting goal")
            else:
                with st.spinner("🔄 Creating meeting and generating strategic questions..."):
                    try:
                        # Get representative IDs
                        rep_ids = [rep_options[name] for name in selected_reps]
                        
                        result = api_client.create_meeting(
                            salesperson_id=st.session_state.salesperson_id,
                            company_id=st.session_state.company_id,
                            meeting_mode=meeting_mode,
                            representatives=rep_ids,
                            meeting_goal=meeting_goal,
                            personality=personality,
                            duration_minutes=duration,
                            difficulty=difficulty
                        )
                        
                        if result.get("success"):
                            meeting_id = result["data"]["meeting_id"]
                            st.session_state.meeting_id = meeting_id
                            st.session_state.meeting_active = False
                            
                            st.success("✅ Meeting created successfully!")
                            st.balloons()
                            
                            # Display meeting details
                            st.markdown("### 📋 Meeting Details")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Mode", meeting_mode)
                            with col2:
                                st.metric("Duration", f"{duration} min")
                            with col3:
                                st.metric("Difficulty", difficulty.title())
                            
                            st.markdown("**Representatives:**")
                            for rep in result["data"]["representatives"]:
                                traits = ", ".join([t.replace("_", " ").title() for t in rep.get("personality_traits", [])])
                                st.write(f"- **{rep['name']}** ({rep['role'].upper().replace('_', ' ')}) - {traits}")
                            
                            st.markdown("---")
                            st.markdown("### 🎯 AI-Generated Top 5 Strategic Questions")
                            st.info("These questions are designed to help you navigate this specific sales conversation effectively")
                            
                            for i, question in enumerate(result["data"]["top_5_questions"], 1):
                                st.markdown(f"**{i}.** {question}")
                            
                            st.markdown("---")
                            st.success("👉 **Next Step:** Go to 'Live Conversation' to start the meeting!")
                        
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.markdown("### Your Meetings")
        
        if st.session_state.salesperson_id:
            with st.spinner("Loading meetings..."):
                try:
                    result = api_client.get_salesperson_meetings(st.session_state.salesperson_id)
                    
                    if result.get("success"):
                        meetings = result["data"].get("meetings", [])
                        
                        if meetings:
                            for meeting in meetings:
                                status_emoji = {
                                    "pending": "🟡",
                                    "active": "🟢",
                                    "completed": "✅"
                                }.get(meeting.get("status", "pending"), "⚪")
                                
                                with st.expander(
                                    f"{status_emoji} {meeting.get('meeting_mode', 'N/A')} - "
                                    f"{meeting.get('status', 'N/A').title()} - "
                                    f"{meeting.get('created_at', '')[:10]}"
                                ):
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.markdown(f"**Mode:** {meeting.get('meeting_mode', 'N/A')}")
                                        st.markdown(f"**Status:** {meeting.get('status', 'N/A').title()}")
                                    
                                    with col2:
                                        st.markdown(f"**Difficulty:** {meeting.get('difficulty', 'N/A').title()}")
                                        st.markdown(f"**Duration:** {meeting.get('duration_minutes', 'N/A')} min")
                                    
                                    with col3:
                                        st.markdown(f"**Personality:** {meeting.get('personality', 'N/A').title()}")
                                    
                                    st.markdown(f"**Goal:** {meeting.get('meeting_goal', 'N/A')}")
                                    
                                    if meeting.get("top_5_questions"):
                                        st.markdown("**Top 5 Questions:**")
                                        for i, q in enumerate(meeting["top_5_questions"], 1):
                                            st.write(f"{i}. {q}")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        if meeting.get("status") == "pending":
                                            if st.button("▶️ Start Meeting", key=f"start_{meeting['id']}"):
                                                try:
                                                    api_client.start_meeting(meeting["id"])
                                                    st.session_state.meeting_id = meeting["id"]
                                                    st.session_state.meeting_active = True
                                                    st.success("Meeting started!")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Error: {e}")
                                    
                                    with col2:
                                        if meeting.get("status") == "active":
                                            if st.button("⏹️ End Meeting", key=f"end_{meeting['id']}"):
                                                try:
                                                    api_client.end_meeting(meeting["id"])
                                                    st.session_state.meeting_active = False
                                                    st.success("Meeting ended!")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Error: {e}")
                                    
                                    with col3:
                                        if st.button("🗑️ Delete", key=f"del_{meeting['id']}"):
                                            try:
                                                api_client.delete_meeting(meeting["id"])
                                                if st.session_state.meeting_id == meeting["id"]:
                                                    st.session_state.meeting_id = None
                                                    st.session_state.meeting_active = False
                                                st.success("Meeting deleted!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                        else:
                            st.info("No meetings created yet")
                    
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("Create a salesperson profile first")
    
    st.markdown("---")
    
    # Tips
    with st.expander("💡 Meeting Setup Tips"):
        st.markdown("""
        **Choosing Meeting Mode:**
        
        **1-on-1 (Best for beginners)**
        - Single representative, easier to manage
        - Good for: Discovery calls, follow-ups, technical demos
        - Example: Meeting with just the CTO to discuss technical requirements
        
        **1-on-2 (Intermediate)**
        - Two representatives with different perspectives
        - Good for: Evaluation meetings, proposal presentations
        - Example: Meeting with CEO + CFO to discuss business case
        
        **1-on-3 (Advanced)**
        - Three representatives, more complex dynamics
        - Good for: Final decision meetings, stakeholder alignment
        - Example: Meeting with CEO + CTO + CFO for final approval
        
        **Difficulty Levels:**
        
        - **Beginner:** Representatives are friendly, ask clarifying questions, show interest
        - **Intermediate:** Mix of supportive and challenging, some objections
        - **Advanced:** Tough questions, skeptical, need strong convincing
        
        **Setting Meeting Goals:**
        
        Good goals are specific and measurable:
        - ✅ "Book a product demo for next week"
        - ✅ "Get commitment for 30-day pilot program"
        - ✅ "Close deal and get contract signed"
        - ✅ "Identify top 3 pain points and confirm budget"
        - ❌ "Have a good conversation" (too vague)
        
        **Representative Selection:**
        
        Choose based on your goal:
        - **Product Demo:** CTO + VP Engineering
        - **Business Case:** CEO + CFO
        - **Sales Process:** VP Sales + CMO
        - **Final Decision:** CEO + CFO + relevant VP
        
        **Strategic Questions:**
        
        The AI generates questions based on:
        - Your product/service details
        - Target company information
        - Meeting goal
        - Representative roles
        
        Use these questions to:
        - Prepare your approach
        - Anticipate objections
        - Structure the conversation
        - Handle different personalities
        """)