import streamlit as st
from utils.api_client import APIClient
import time

def show():
    """Company setup page"""
    
    st.markdown("## 🏢 Company Setup")
    st.markdown("Configure target company and add representatives with realistic personalities")
    
    api_client = APIClient(st.session_state.api_base_url)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["➕ Create Company", "👥 Add Representatives", "📋 View Details"])
    
    with tab1:
        st.markdown("### Add Target Company")
        
        with st.form("company_form"):
            company_url = st.text_input(
                "Company Website URL *",
                placeholder="https://www.company.com",
                help="AI will automatically scrape company data from this URL"
            )
            
            auto_fetch = st.checkbox(
                "Auto-fetch company data using AI",
                value=True,
                help="Uses web scraping + AI to extract company details (takes 30-60 seconds)"
            )
            
            st.info("ℹ️ AI will extract: company size, headquarters, revenue, industry, tech stack, and more")
            
            submit = st.form_submit_button("Create Company Profile", use_container_width=True, type="primary")
        
        if submit:
            if not company_url:
                st.error("❌ Please enter a company URL")
            elif not company_url.startswith("http"):
                st.error("❌ URL must start with http:// or https://")
            else:
                with st.spinner("🔄 Creating company profile and scraping data... This may take 30-60 seconds..."):
                    try:
                        result = api_client.create_company(
                            company_url=company_url,
                            auto_fetch=auto_fetch
                        )
                        
                        if result.get("success"):
                            company_id = result["data"]["company_id"]
                            st.session_state.company_id = company_id
                            
                            st.success("✅ Company profile created successfully!")
                            st.balloons()
                            
                            # Display scraped data
                            company_data = result["data"].get("company_data", {})
                            
                            if company_data:
                                st.markdown("### 📊 Extracted Company Data")
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Industry", company_data.get("industry", "N/A"))
                                    st.metric("Company Size", company_data.get("company_size", "N/A"))
                                
                                with col2:
                                    st.metric("Headquarters", company_data.get("headquarters", "N/A"))
                                    st.metric("Revenue", company_data.get("revenue", "N/A"))
                                
                                with col3:
                                    st.metric("Founded", company_data.get("founded_year", "N/A"))
                                    tech_count = len(company_data.get("tech_stack", []))
                                    st.metric("Tech Stack", f"{tech_count} technologies")
                                
                                if company_data.get("description"):
                                    st.markdown("**Description:**")
                                    st.info(company_data["description"])
                                
                                if company_data.get("tech_stack"):
                                    st.markdown("**Tech Stack:**")
                                    st.write(", ".join(company_data["tech_stack"]))
                            
                            st.info("👉 **Next Step:** Go to 'Add Representatives' tab to add company representatives")
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.markdown("### Add Company Representatives")
        
        if not st.session_state.company_id:
            st.warning("⚠️ Please create a company profile first")
        else:
            st.info(f"Company ID: {st.session_state.company_id}")
            
            with st.form("representative_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Name *", placeholder="e.g., John Smith")
                    
                    role = st.selectbox(
                        "Role *",
                        options=[
                            "ceo", "cmo", "cfo", "coo", "cto",
                            "vp_sales", "director", "manager"
                        ],
                        format_func=lambda x: x.upper().replace("_", " ")
                    )
                    
                    tenure_months = st.number_input(
                        "Tenure (months) *",
                        min_value=1,
                        max_value=600,
                        value=24,
                        help="How long they've been in this role"
                    )
                
                with col2:
                    personality_traits = st.multiselect(
                        "Personality Traits *",
                        options=[
                            "angry", "arrogant", "soft", "cold_hearted",
                            "nice", "cool", "not_well", "analytical"
                        ],
                        default=["nice"],
                        format_func=lambda x: x.replace("_", " ").title(),
                        help="Select 1-3 personality traits"
                    )
                    
                    is_decision_maker = st.checkbox(
                        "Decision Maker",
                        help="Can this person make final purchasing decisions?"
                    )
                    
                    linkedin_profile = st.text_input(
                        "LinkedIn Profile (Optional)",
                        placeholder="https://linkedin.com/in/..."
                    )
                
                notes = st.text_area(
                    "Additional Notes (Optional)",
                    placeholder="e.g., Focus areas, concerns, specific interests...",
                    height=100
                )
                
                voice_id = st.selectbox(
                    "Voice ID (Optional)",
                    options=["None", "voice_0", "voice_1", "voice_2", "voice_3", "voice_4", "voice_5"],
                    help="Select a voice for this representative"
                )
                
                submit = st.form_submit_button("Add Representative", use_container_width=True, type="primary")
            
            if submit:
                if not name or not role or not personality_traits:
                    st.error("❌ Please fill in all required fields")
                elif len(personality_traits) > 3:
                    st.error("❌ Please select maximum 3 personality traits")
                else:
                    with st.spinner("Adding representative..."):
                        try:
                            result = api_client.add_representative(
                                company_id=st.session_state.company_id,
                                name=name,
                                role=role,
                                tenure_months=tenure_months,
                                personality_traits=personality_traits,
                                is_decision_maker=is_decision_maker,
                                linkedin_profile=linkedin_profile if linkedin_profile else None,
                                notes=notes if notes else None,
                                voice_id=voice_id if voice_id != "None" else None
                            )
                            
                            if result.get("success"):
                                st.success(f"✅ Representative '{name}' added successfully!")
                                st.balloons()
                                st.info("You can add more representatives or go to 'Meeting Setup' to create a meeting")
                            else:
                                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                        
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
    
    with tab3:
        st.markdown("### Company Details")
        
        if not st.session_state.company_id:
            st.info("ℹ️ No company created yet")
        else:
            # Company Info
            with st.spinner("Loading company details..."):
                try:
                    result = api_client.get_company(st.session_state.company_id)
                    
                    if result.get("success"):
                        data = result["data"]
                        
                        st.markdown(f"### 🏢 {data.get('company_url', 'Company')}")
                        
                        company_data = data.get("company_data", {})
                        
                        if company_data:
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Industry", company_data.get("industry", "N/A"))
                            with col2:
                                st.metric("Size", company_data.get("company_size", "N/A"))
                            with col3:
                                st.metric("Revenue", company_data.get("revenue", "N/A"))
                            with col4:
                                st.metric("Founded", company_data.get("founded_year", "N/A"))
                            
                            if company_data.get("description"):
                                st.markdown("**Description:**")
                                st.info(company_data["description"])
                            
                            if company_data.get("tech_stack"):
                                st.markdown("**Tech Stack:**")
                                st.write(", ".join(company_data["tech_stack"]))
                        
                        st.markdown("---")
                        
                        # Representatives
                        st.markdown("### 👥 Company Representatives")
                        
                        reps_result = api_client.get_company_representatives(st.session_state.company_id)
                        
                        if reps_result.get("success"):
                            representatives = reps_result["data"].get("representatives", [])
                            
                            if representatives:
                                for rep in representatives:
                                    with st.expander(f"👤 {rep['name']} - {rep['role'].upper().replace('_', ' ')}"):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown(f"**Role:** {rep['role'].upper().replace('_', ' ')}")
                                            st.markdown(f"**Tenure:** {rep['tenure_months']} months")
                                            st.markdown(f"**Decision Maker:** {'✅ Yes' if rep.get('is_decision_maker') else '❌ No'}")
                                        
                                        with col2:
                                            traits = ", ".join([t.replace("_", " ").title() for t in rep.get('personality_traits', [])])
                                            st.markdown(f"**Personality:** {traits}")
                                            
                                            if rep.get('voice_id'):
                                                st.markdown(f"**Voice:** {rep['voice_id']}")
                                            
                                            if rep.get('linkedin_profile'):
                                                st.markdown(f"**LinkedIn:** [{rep['linkedin_profile']}]({rep['linkedin_profile']})")
                                        
                                        if rep.get('notes'):
                                            st.markdown(f"**Notes:** {rep['notes']}")
                                        
                                        if st.button(f"🗑️ Delete {rep['name']}", key=f"del_{rep['id']}"):
                                            try:
                                                api_client.delete_representative(rep['id'])
                                                st.success(f"Deleted {rep['name']}")
                                                time.sleep(1)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                            else:
                                st.info("No representatives added yet")
                        
                except Exception as e:
                    st.error(f"Error loading company: {e}")
    
    st.markdown("---")
    
    # Tips
    with st.expander("💡 Representative Setup Tips"):
        st.markdown("""
        **Creating Realistic Representatives:**
        
        **Role Selection:**
        - **CEO:** Strategic discussions, high-level vision, final decision maker
        - **CFO:** Budget, ROI, financial justification
        - **CTO:** Technical requirements, integrations, security
        - **CMO:** Marketing impact, brand alignment, customer data
        - **VP Sales:** Sales team adoption, productivity gains
        
        **Personality Combinations:**
        - **Analytical + Cold Hearted:** Data-driven, skeptical, needs proof
        - **Nice + Soft:** Friendly, easy to talk to, cooperative
        - **Arrogant + Angry:** Challenging, dismissive, tough questions
        - **Cool + Analytical:** Professional, logical, calm evaluation
        
        **Tenure Considerations:**
        - Short tenure (1-12 months): Less authority, more cautious
        - Medium tenure (12-36 months): Confident, established
        - Long tenure (36+ months): Highly influential, set in ways
        
        **Decision Maker Status:**
        - Usually CEO, CFO, or VPs are decision makers
        - Directors/Managers typically influencers, not final deciders
        - In small companies, any C-level might be decision maker
        
        **Example Setup for Software Sale:**
        ```
        1. Sarah Chen (CEO)
           - Analytical, Nice
           - 48 months tenure
           - Decision Maker: Yes
           - Focus: Strategic fit, long-term vision
        
        2. David Kim (CTO)
           - Analytical, Cool
           - 24 months tenure
           - Decision Maker: No
           - Focus: Technical integration, security
        
        3. Maria Garcia (CFO)
           - Cold Hearted, Analytical
           - 36 months tenure
           - Decision Maker: Yes
           - Focus: ROI, budget, cost justification
        ```
        """)