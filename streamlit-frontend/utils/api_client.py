"""
API Client for AI Sales Training Platform
Updated to match backend endpoints correctly
"""

import requests
import json
from typing import Dict, List, Optional, Any
import streamlit as st


class APIClient:
    """Client for communicating with FastAPI backend"""
    
    def __init__(self, base_url: str):
        """Initialize API client with base URL"""
        self.base_url = base_url.rstrip('/')
        self.timeout = 30  # 30 seconds timeout
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/api/salesperson/simple')
            data: Form data (for multipart/form-data)
            files: Files to upload
            json_data: JSON data (for application/json)
        
        Returns:
            Response dictionary with 'success' key and data/error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Prepare request
            kwargs = {
                'timeout': self.timeout
            }
            
            if files:
                kwargs['files'] = files
            
            if data:
                kwargs['data'] = data
            
            if json_data:
                kwargs['json'] = json_data
                kwargs['headers'] = {'Content-Type': 'application/json'}
            
            # Make request
            if method.upper() == 'GET':
                response = requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, **kwargs)
            elif method.upper() == 'PUT':
                response = requests.put(url, **kwargs)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}"
                }
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {
                    "success": False,
                    "error": "Invalid JSON response from server",
                    "raw_response": response.text
                }
            
            # Check status code
            if response.status_code in [200, 201]:
                # Backend already returns response in the format we need
                if isinstance(response_data, dict) and "success" in response_data:
                    return response_data
                else:
                    # Wrap in standard format
                    return {
                        "success": True,
                        "data": response_data,
                        "status_code": response.status_code
                    }
            else:
                # Error response
                if isinstance(response_data, dict):
                    return {
                        "success": False,
                        "error": response_data.get("detail", f"HTTP {response.status_code}"),
                        "details": response_data.get("message", response.text),
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text,
                        "status_code": response.status_code
                    }
        
        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "error": "Cannot connect to backend server",
                "details": f"Please ensure backend is running at {self.base_url}",
                "exception": str(e)
            }
        
        except requests.exceptions.Timeout as e:
            return {
                "success": False,
                "error": "Request timeout",
                "details": f"Server did not respond within {self.timeout} seconds",
                "exception": str(e)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {type(e).__name__}",
                "details": str(e)
            }
    
    # ==================== SALESPERSON ENDPOINTS ====================
    
    def create_salesperson_simple(
        self,
        product_name: str,
        description: str,
        product_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create salesperson profile without files
        
        Endpoint: POST /api/salesperson/simple
        
        Args:
            product_name: Name of product/service
            description: Detailed product description
            product_url: Optional product website URL
        
        Returns:
            API response with salesperson_id
        """
        json_data = {
            "product_name": product_name,
            "description": description
        }
        
        if product_url:
            json_data["product_url"] = product_url
        
        return self._make_request(
            method='POST',
            endpoint='/api/salesperson/simple',
            json_data=json_data
        )
    
    def create_salesperson_with_files(
        self,
        product_name: str,
        description: str,
        files: List[Any],
        product_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create salesperson profile with uploaded files
        
        Endpoint: POST /api/salesperson/with-files
        
        Args:
            product_name: Name of product/service
            description: Detailed product description
            files: List of uploaded file objects
            product_url: Optional product website URL
        
        Returns:
            API response with salesperson_id and materials info
        """
        # Prepare form data
        data = {
            "product_name": product_name,
            "description": description
        }
        
        if product_url:
            data["product_url"] = product_url
        
        # Prepare files - IMPORTANT: Use 'materials' as key name
        file_list = []
        for file_obj in files:
            # Reset file pointer to beginning
            file_obj.seek(0)
            
            # Create tuple: (filename, file_object, content_type)
            file_list.append(
                ('materials', (file_obj.name, file_obj, file_obj.type))
            )
        
        return self._make_request(
            method='POST',
            endpoint='/api/salesperson/with-files',
            data=data,
            files=file_list
        )
    
    def get_salesperson(self, salesperson_id: str) -> Dict[str, Any]:
        """
        Get salesperson profile by ID
        
        Endpoint: GET /api/salesperson/{salesperson_id}
        
        Args:
            salesperson_id: Unique salesperson identifier
        
        Returns:
            Salesperson profile data
        """
        return self._make_request(
            method='GET',
            endpoint=f'/api/salesperson/{salesperson_id}'
        )
    
    def delete_salesperson(self, salesperson_id: str) -> Dict[str, Any]:
        """
        Delete salesperson profile
        
        Endpoint: DELETE /api/salesperson/{salesperson_id}
        
        Args:
            salesperson_id: Unique salesperson identifier
        
        Returns:
            Success/failure response
        """
        return self._make_request(
            method='DELETE',
            endpoint=f'/api/salesperson/{salesperson_id}'
        )
    
    # ==================== COMPANY ENDPOINTS ====================
    
    def create_company_simple(
        self,
        company_name: str,
        industry: str,
        description: str,
        website_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create company profile without files"""
        json_data = {
            "company_name": company_name,
            "industry": industry,
            "description": description
        }
        
        if website_url:
            json_data["website_url"] = website_url
        
        return self._make_request(
            method='POST',
            endpoint='/api/company/simple',
            json_data=json_data
        )
    
    def create_company_with_files(
        self,
        company_name: str,
        industry: str,
        description: str,
        files: List[Any],
        website_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create company profile with uploaded files"""
        data = {
            "company_name": company_name,
            "industry": industry,
            "description": description
        }
        
        if website_url:
            data["website_url"] = website_url
        
        # Prepare files
        file_list = []
        for file_obj in files:
            file_obj.seek(0)
            file_list.append(
                ('materials', (file_obj.name, file_obj, file_obj.type))
            )
        
        return self._make_request(
            method='POST',
            endpoint='/api/company/with-files',
            data=data,
            files=file_list
        )
    
    def get_company(self, company_id: str) -> Dict[str, Any]:
        """Get company profile by ID"""
        return self._make_request(
            method='GET',
            endpoint=f'/api/company/{company_id}'
        )
    
    def delete_company(self, company_id: str) -> Dict[str, Any]:
        """Delete company profile"""
        return self._make_request(
            method='DELETE',
            endpoint=f'/api/company/{company_id}'
        )
    
    # ==================== MEETING ENDPOINTS ====================
    
    def create_meeting(
        self,
        salesperson_id: str,
        company_id: str,
        meeting_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a sales meeting"""
        json_data = {
            "salesperson_id": salesperson_id,
            "company_id": company_id
        }
        
        if meeting_context:
            json_data["meeting_context"] = meeting_context
        
        return self._make_request(
            method='POST',
            endpoint='/api/meeting',
            json_data=json_data
        )
    
    def get_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """Get meeting details"""
        return self._make_request(
            method='GET',
            endpoint=f'/api/meeting/{meeting_id}'
        )
    
    def start_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """Start a meeting"""
        return self._make_request(
            method='POST',
            endpoint=f'/api/meeting/{meeting_id}/start'
        )
    
    def end_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """End a meeting"""
        return self._make_request(
            method='POST',
            endpoint=f'/api/meeting/{meeting_id}/end'
        )
    
    # ==================== CONVERSATION ENDPOINTS ====================
    
    def send_message(
        self,
        meeting_id: str,
        message: str,
        speaker: str = "user"
    ) -> Dict[str, Any]:
        """Send a message in the conversation"""
        json_data = {
            "meeting_id": meeting_id,
            "message": message,
            "speaker": speaker
        }
        
        return self._make_request(
            method='POST',
            endpoint='/api/conversation/message',
            json_data=json_data
        )
    
    def get_conversation_history(self, meeting_id: str) -> Dict[str, Any]:
        """Get full conversation history for a meeting"""
        return self._make_request(
            method='GET',
            endpoint=f'/api/conversation/{meeting_id}'
        )
    
    # ==================== ANALYTICS ENDPOINTS ====================
    
    def get_analytics(self, meeting_id: str) -> Dict[str, Any]:
        """Get analytics for a meeting"""
        return self._make_request(
            method='GET',
            endpoint=f'/api/analytics/{meeting_id}'
        )
    
    def get_feedback(self, meeting_id: str) -> Dict[str, Any]:
        """Get AI feedback on sales performance"""
        return self._make_request(
            method='GET',
            endpoint=f'/api/analytics/{meeting_id}/feedback'
        )
    
    # ==================== HEALTH CHECK ====================
    
    def health_check(self) -> Dict[str, Any]:
        """Check if API is healthy"""
        return self._make_request(
            method='GET',
            endpoint='/health'
        )


# ==================== HELPER FUNCTIONS ====================

def test_api_connection(base_url: str) -> bool:
    """Test if API is reachable"""
    try:
        client = APIClient(base_url)
        result = client.health_check()
        return result.get("success", False)
    except:
        return False