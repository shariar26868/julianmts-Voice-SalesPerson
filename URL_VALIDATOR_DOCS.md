# Company URL Validator - Documentation

## Overview

The URL Validator system automatically validates, authenticates, and safely redirects users to company websites. It provides comprehensive security checks and ensures that only legitimate, reachable websites are used.

## Features

### 1. **Automatic URL Normalization**
- Automatically adds `https://` to URLs if missing
- Converts `www.example.com` to `https://www.example.com`
- Handles various URL formats

### 2. **SSL Certificate Validation**
- Verifies SSL certificate validity
- Detects self-signed or expired certificates
- Provides warnings for security issues

### 3. **Website Reachability Check**
- Tests if the website is actually reachable
- Checks HTTP status codes (200-399 range for valid)
- Handles redirects and follow chains

### 4. **Domain Reputation Analysis**
- Detects suspicious domain patterns
- Checks for commonly abused TLDs (.tk, .ml, .ga, .cf)
- Warns about potential phishing patterns
- Identifies IDN homoglyph attacks

### 5. **Redirect Chain Verification**
- Detects suspicious redirects
- Warns if URL redirects to different domain
- Protects against phishing attempts

## API Endpoints

### 1. Validate URL Endpoint
**POST** `/api/company/validate-url`

Validates and authenticates a company URL.

**Request:**
```json
{
  "url": "google.com"
}
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "authenticated_url": "https://google.com",
    "is_reachable": true,
    "status_code": 200,
    "ssl_valid": true,
    "domain": "google.com",
    "errors": [],
    "warnings": []
  },
  "message": "URL validation completed"
}
```

**Response (Invalid URL):**
```json
{
  "success": false,
  "data": {
    "is_valid": false,
    "authenticated_url": null,
    "is_reachable": false,
    "status_code": null,
    "ssl_valid": false,
    "domain": null,
    "errors": ["URL not reachable (Status: None)"],
    "warnings": []
  },
  "message": "URL validation completed"
}
```

---

### 2. Redirect to Authenticated URL Endpoint
**GET** `/api/company/redirect?url={url}`

Validates the URL and redirects to the authenticated website if valid.

**Example:**
```
GET /api/company/redirect?url=amazon.com
```

**Response:**
- If valid: HTTP 307 redirect to the authenticated URL
- If invalid: HTTP 400 error with details

---

### 3. Create Company with URL Validation
**POST** `/api/company/create`

Creates a company profile with mandatory URL validation.

**Request:**
```json
{
  "salesperson_id": "sp_123",
  "company_url": "https://microsoft.com",
  "auto_fetch": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "company_id": "c_xyz789",
    "salesperson_id": "sp_123",
    "company_url": "https://microsoft.com",
    "company_data": { ... },
    "url_validation": {
      "is_valid": true,
      "ssl_valid": true,
      "domain": "microsoft.com",
      "warnings": []
    }
  },
  "message": "Company data created successfully with authenticated URL"
}
```

## Usage Examples

### Example 1: Using the Validation Endpoint in JavaScript

```javascript
async function validateCompanyURL(url) {
  try {
    const response = await fetch('/api/company/validate-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    const result = await response.json();

    if (result.data.is_valid) {
      console.log('✅ URL is valid:', result.data.authenticated_url);
      // Use the authenticated URL
      return result.data.authenticated_url;
    } else {
      console.error('❌ URL validation failed:');
      console.error('Errors:', result.data.errors);
      console.error('Warnings:', result.data.warnings);
      return null;
    }
  } catch (error) {
    console.error('Request failed:', error);
    return null;
  }
}

// Usage
const authenticatedURL = await validateCompanyURL('google.com');
```

### Example 2: Using the Redirect Endpoint

```javascript
function redirectToCompany(url) {
  // This will automatically validate and redirect
  window.location.href = `/api/company/redirect?url=${encodeURIComponent(url)}`;
}

// Usage
redirectToCompany('amazon.com');
```

### Example 3: Creating Company with Validation

```javascript
async function createCompanyProfile(salespersonId, companyUrl) {
  try {
    const response = await fetch('/api/company/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        salesperson_id: salespersonId,
        company_url: companyUrl,
        auto_fetch: true
      })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('Company creation failed:', error.detail);
      return null;
    }

    const result = await response.json();
    console.log('✅ Company created with authenticated URL:', 
                result.data.company_url);
    return result.data;
  } catch (error) {
    console.error('Request failed:', error);
    return null;
  }
}

// Usage
await createCompanyProfile('sp_123', 'microsoft.com');
```

### Example 4: Python/Backend Usage

```python
import httpx
import asyncio
from app.services.url_validator_service import url_validator

async def validate_multiple_urls(urls):
    """Validate multiple company URLs"""
    results = {}
    
    for url in urls:
        result = await url_validator.validate_and_authenticate_url(url)
        results[url] = {
            'is_valid': result['is_valid'],
            'authenticated_url': result['authenticated_url'],
            'errors': result['errors'],
            'warnings': result['warnings']
        }
    
    return results

# Usage
urls = ['google.com', 'invalid-company-xyz.tk', 'amazon.com']
results = asyncio.run(validate_multiple_urls(urls))
```

## URL Validation Rules

### Valid URL Examples
✅ `google.com` → `https://google.com`
✅ `www.amazon.com` → `https://www.amazon.com`
✅ `https://apple.com` → `https://apple.com` (unchanged)
✅ `microsoft.com` → `https://microsoft.com`

### Invalid URL Examples
❌ `invalid company` (invalid format)
❌ `not-a-url` (no domain extension)
❌ `http://unreachable-domain-xyz.com` (not reachable)
❌ `phishing-site.tk` (suspicious TLD)

## Response Fields Explanation

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | boolean | Overall URL validity (reachable + SSL valid) |
| `authenticated_url` | string | Normalized, validated URL ready to use |
| `is_reachable` | boolean | Website responds and is accessible |
| `status_code` | integer | HTTP status code from the server |
| `ssl_valid` | boolean | SSL certificate is valid and trusted |
| `domain` | string | Extracted domain name |
| `errors` | array | Critical issues preventing URL use |
| `warnings` | array | Non-critical issues to be aware of |

## Error Handling

### Common Errors and Solutions

**Error: "Invalid URL format"**
- Solution: Ensure URL has proper format (e.g., `google.com` or `https://google.com`)

**Error: "URL not reachable"**
- Solution: Check if website is online and accessible from your location

**Error: "SSL certificate invalid"**
- Solution: The website's SSL certificate is expired or self-signed. Contact the company to fix it.

**Error: "Redirects to different domain"**
- Solution: Verify the redirect destination is legitimate

## Integration Steps

### Step 1: Add URL Validator to Requirements
The URL validator uses `httpx` for async HTTP requests. Ensure it's in your `requirements.txt`:
```
httpx==0.24.0
```

### Step 2: Use in Your Application
```python
from app.services.url_validator_service import url_validator

# Validate a URL
result = await url_validator.validate_and_authenticate_url("google.com")

# Get just the authenticated URL
safe_url = await url_validator.get_authenticated_url("google.com")
```

### Step 3: Frontend Integration
Use the provided `url-validator-client.html` as a reference UI component or integrate the validation logic into your existing interface.

## Security Considerations

1. **Always Validate Before Use**: Never use user-provided URLs without validation
2. **Check Warnings**: Even if a URL is valid, check warnings for potential issues
3. **Monitor Redirects**: Be aware of redirect patterns
4. **Update Regularly**: Keep the validator updated with new suspicious patterns
5. **Log Validations**: Track which URLs have been validated for audit purposes

## Performance Notes

- SSL checking: ~5-10 seconds per URL (cached)
- Reachability check: ~2-5 seconds per URL
- Total validation time: ~10-15 seconds per URL (typical)
- Async execution: Non-blocking, handles multiple requests concurrently

## Troubleshooting

### Validation Always Fails
- Check network connectivity
- Verify the URL is actually accessible
- Check for firewall/proxy blocking

### SSL Certificate Warnings on Valid Sites
- Some companies use self-signed certificates
- This is flagged but doesn't prevent access
- Check if the certificate is trusted in your security policy

### Slow Validation
- SSL checking can be slow for some domains
- Consider caching validation results
- Use connection pooling for multiple validations

## Future Enhancements

- [ ] DNS resolution validation
- [ ] WHOIS lookup for company information
- [ ] Geolocation verification
- [ ] Cached validation results
- [ ] Reputation scoring from multiple sources
- [ ] Rate limiting and throttling
- [ ] Webhook notifications for suspicious URLs

---

**Last Updated:** April 2026
**Version:** 1.0
