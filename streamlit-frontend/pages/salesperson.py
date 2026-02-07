import streamlit as st
import requests
from utils.api_client import APIClient

def show():
    """Salesperson setup page - FIXED VERSION"""
    
    st.markdown("## 👤 Salesperson Setup")
    st.markdown("Configure your product/service details for the sales conversation")
    
    api_client = APIClient(st.session_state.api_base_url)
    
    # Tabs for create and view
    tab1, tab2 = st.tabs(["➕ Create New", "📋 View Existing"])
    
    with tab1:
        st.markdown("### Create Salesperson Profile")
        
        # Use a unique form key with a timestamp or counter to prevent caching issues
        if 'form_counter' not in st.session_state:
            st.session_state.form_counter = 0
        
        with st.form(key=f"salesperson_form_{st.session_state.form_counter}", clear_on_submit=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                product_name = st.text_input(
                    "Product/Service Name *",
                    placeholder="e.g., CloudSync CRM Software",
                    help="Name of the product or service you're selling",
                    key=f"product_name_{st.session_state.form_counter}"
                )
            
            with col2:
                product_url = st.text_input(
                    "Product URL (Optional)",
                    placeholder="https://yourproduct.com",
                    help="Website or landing page URL",
                    key=f"product_url_{st.session_state.form_counter}"
                )
            
            description = st.text_area(
                "Product Description *",
                placeholder="Describe your product, key features, benefits, pricing, target audience, etc.",
                height=150,
                help="Detailed description helps AI understand your offering better",
                key=f"description_{st.session_state.form_counter}"
            )
            
            st.markdown("---")
            st.markdown("#### 📎 Product Materials (Optional)")
            st.info("Upload PDFs, PowerPoints, Word docs, or images about your product")
            
            uploaded_files = st.file_uploader(
                "Choose files",
                type=['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif'],
                accept_multiple_files=True,
                help="These materials help AI understand your product better",
                key=f"files_{st.session_state.form_counter}"
            )
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit_simple = st.form_submit_button(
                    "Create (Without Files)",
                    use_container_width=True,
                    type="primary"
                )
            
            with col2:
                submit_with_files = st.form_submit_button(
                    "Create (With Files)",
                    use_container_width=True,
                    type="secondary"
                )
        
        # Handle form submission - OUTSIDE THE FORM
        if submit_simple or submit_with_files:
            # Input validation
            if not product_name or product_name.strip() == "":
                st.error("❌ Please enter Product/Service Name")
            elif not description or description.strip() == "":
                st.error("❌ Please enter Product Description")
            else:
                # Show what we're about to send
                with st.expander("🔍 Debug: Data being sent"):
                    st.write("Product Name:", product_name)
                    st.write("Product URL:", product_url if product_url else "None")
                    st.write("Description:", description[:100] + "..." if len(description) > 100 else description)
                    st.write("Files:", len(uploaded_files) if uploaded_files else 0)
                    st.write("API URL:", st.session_state.api_base_url)
                
                with st.spinner("🔄 Creating salesperson profile..."):
                    try:
                        # Decide which method to use
                        use_files = submit_with_files and uploaded_files and len(uploaded_files) > 0
                        
                        if use_files:
                            st.info(f"📤 Uploading {len(uploaded_files)} file(s)...")
                            result = api_client.create_salesperson_with_files(
                                product_name=product_name.strip(),
                                description=description.strip(),
                                product_url=product_url.strip() if product_url else None,
                                files=uploaded_files
                            )
                        else:
                            st.info("📤 Creating profile without files...")
                            result = api_client.create_salesperson_simple(
                                product_name=product_name.strip(),
                                description=description.strip(),
                                product_url=product_url.strip() if product_url else None
                            )
                        
                        # Debug: Show API response
                        with st.expander("🔍 Debug: API Response"):
                            st.json(result)
                        
                        # Handle response
                        if result and result.get("success"):
                            salesperson_id = result["data"]["salesperson_id"]
                            st.session_state.salesperson_id = salesperson_id
                            
                            # Increment form counter to reset form
                            st.session_state.form_counter += 1
                            
                            st.success(f"✅ Salesperson profile created successfully!")
                            st.balloons()
                            
                            st.markdown(f"""
                            <div class="success-box">
                                <strong>📋 Salesperson ID:</strong> <code>{salesperson_id}</code><br>
                                <strong>📦 Product:</strong> {product_name}<br>
                                <strong>📄 Materials:</strong> {result['data'].get('materials_uploaded', 0)} files uploaded
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.info("👉 **Next Step:** Go to 'Company Setup' to configure your target company")
                            
                            # Add a refresh button
                            if st.button("🔄 Create Another Profile"):
                                st.rerun()
                        
                        elif result and not result.get("success"):
                            error_msg = result.get('error', 'Unknown error')
                            st.error(f"❌ Error from API: {error_msg}")
                            
                            if 'details' in result:
                                st.error(f"Details: {result['details']}")
                        
                        else:
                            st.error("❌ No response from API or invalid response format")
                            st.error("Please check if the backend is running and the API URL is correct")
                    
                    except requests.exceptions.ConnectionError as e:
                        st.error(f"❌ Cannot connect to API at {st.session_state.api_base_url}")
                        st.error("Please ensure the backend server is running")
                        st.code(str(e))
                    
                    except requests.exceptions.Timeout as e:
                        st.error("❌ Request timeout - the server took too long to respond")
                        st.code(str(e))
                    
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {type(e).__name__}")
                        st.error(f"Message: {str(e)}")
                        
                        import traceback
                        with st.expander("🔍 Full Error Traceback"):
                            st.code(traceback.format_exc())
    
    with tab2:
        st.markdown("### View Salesperson Profile")
        
        if st.session_state.salesperson_id:
            with st.spinner("Loading profile..."):
                try:
                    result = api_client.get_salesperson(st.session_state.salesperson_id)
                    
                    # Debug API response
                    with st.expander("🔍 Debug: API Response"):
                        st.json(result)
                    
                    if result and result.get("success"):
                        data = result["data"]
                        
                        # Display profile
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"### {data.get('product_name', 'N/A')}")
                        
                        with col2:
                            # Use a regular button instead of in a form
                            if st.button("🗑️ Delete", key="delete_btn", use_container_width=True):
                                if st.session_state.get('confirm_delete'):
                                    try:
                                        delete_result = api_client.delete_salesperson(st.session_state.salesperson_id)
                                        if delete_result.get("success"):
                                            st.session_state.salesperson_id = None
                                            st.session_state.confirm_delete = False
                                            st.success("✅ Profile deleted!")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Delete failed: {delete_result.get('error')}")
                                    except Exception as e:
                                        st.error(f"❌ Error deleting: {e}")
                                else:
                                    st.session_state.confirm_delete = True
                                    st.warning("⚠️ Click again to confirm deletion")
                                    st.rerun()
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Product URL:**")
                            if data.get('product_url'):
                                st.markdown(f"[{data['product_url']}]({data['product_url']})")
                            else:
                                st.text("Not provided")
                        
                        with col2:
                            st.markdown("**Created:**")
                            st.text(data.get('created_at', 'N/A')[:10] if 'created_at' in data else "N/A")
                        
                        st.markdown("**Description:**")
                        st.info(data.get('description', 'No description'))
                        
                        st.markdown("**Materials:**")
                        materials = data.get('materials', [])
                        if materials and len(materials) > 0:
                            for i, material in enumerate(materials, 1):
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    st.text(f"{i}. {material.get('file_name', 'Unknown')}")
                                with col2:
                                    st.text(material.get('file_type', 'N/A').upper())
                                with col3:
                                    if material.get('file_url'):
                                        st.markdown(f"[📥 View]({material['file_url']})")
                        else:
                            st.text("No materials uploaded")
                    
                    elif result and not result.get("success"):
                        st.error(f"❌ Error loading profile: {result.get('error', 'Unknown error')}")
                    
                    else:
                        st.error("❌ Invalid response from API")
                
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Cannot connect to API at {st.session_state.api_base_url}")
                    st.error("Please ensure the backend server is running")
                
                except Exception as e:
                    st.error(f"❌ Error: {type(e).__name__}: {str(e)}")
                    
                    with st.expander("🔍 Full Error Details"):
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.info("ℹ️ No salesperson profile created yet. Use the 'Create New' tab to get started.")
            
            # Add option to manually enter ID for debugging
            with st.expander("🔧 Debug: Manually Load Profile"):
                manual_id = st.text_input("Enter Salesperson ID:")
                if st.button("Load Profile"):
                    if manual_id:
                        st.session_state.salesperson_id = manual_id
                        st.rerun()
    
    st.markdown("---")
    
    # Tips
    with st.expander("💡 Tips for Better Results"):
        st.markdown("""
        **Product Description Best Practices:**
        
        1. **Be Specific:** Include exact features, benefits, and use cases
        2. **Mention Pricing:** If applicable, include pricing tiers or ranges  
        3. **Target Audience:** Describe who this product is for
        4. **Competitive Edge:** What makes your product unique?
        5. **Common Objections:** Note typical concerns customers have
        
        **Example Good Description:**
        ```
        CloudSync CRM is a cloud-based customer relationship management 
        platform designed for small to medium B2B companies (10-500 employees).
        
        Key Features:
        - AI-powered lead scoring
        - Email automation
        - Sales pipeline visualization
        - Integration with 100+ tools
        
        Pricing: $49/user/month (starts at $249/month for 5 users)
        
        Target: Sales teams looking to increase conversion rates and 
        reduce manual data entry. Common use case: B2B SaaS companies 
        with complex sales cycles.
        ```
        
        **Materials to Upload:**
        - Product brochures
        - Case studies
        - Feature comparison sheets
        - Pricing sheets
        - Demo slides
        """)
    
    # Debugging section
    with st.expander("🔧 Debug Information"):
        st.write("**Session State:**")
        st.json({
            "api_base_url": st.session_state.api_base_url,
            "salesperson_id": st.session_state.salesperson_id,
            "company_id": st.session_state.company_id,
            "form_counter": st.session_state.get('form_counter', 0)
        })
        
        # Test API connection
        if st.button("🔌 Test API Connection"):
            try:
                response = requests.get(f"{st.session_state.api_base_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ API is reachable!")
                    st.json(response.json())
                else:
                    st.error(f"❌ API returned status {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API")
            except Exception as e:
                st.error(f"❌ Error: {e}")