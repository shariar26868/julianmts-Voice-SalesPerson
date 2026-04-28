# 🚀 URL Validator - Quick Start Guide

## What This Does

When a user enters a company URL (with or without `https://`), the system:
1. ✅ Normalizes it (adds `https://` if missing)
2. 🔒 Verifies SSL certificate
3. 📡 Checks if the website is reachable
4. ⚠️ Detects suspicious patterns
5. 🔄 Verifies redirect chains
6. ✔️ Returns the authenticated, safe URL

## Installation

### 1. No Additional Dependencies Needed
The URL validator uses `httpx` which should already be in your project. If not, add it:

```bash
pip install httpx
```

### 2. Files Added to Your Project

- `app/services/url_validator_service.py` - Core validation service
- `app/utils/url_validation_helper.py` - Helper functions and decorators
- `url-validator-client.html` - Frontend UI component
- `URL_VALIDATOR_DOCS.md` - Complete documentation

## Quick Usage Examples

### Example 1: Frontend HTML Form
Open `url-validator-client.html` in your browser and test the validation UI:
- Enter any company URL
- Click "Validate URL" to check it
- Click "Go to Website" to redirect to the authenticated URL

### Example 2: Backend - Simple Validation

```python
from app.services.url_validator_service import url_validator

# In your route handler
result = await url_validator.validate_and_authenticate_url("google.com")

if result["is_valid"]:
    print(f"✅ Use this URL: {result['authenticated_url']}")
else:
    print(f"❌ Error: {result['errors']}")
```

### Example 3: Backend - Using Helper Functions

```python
from app.utils.url_validation_helper import URLValidationHelper

# Simple validation
authenticated_url = await URLValidationHelper.validate_and_get_url("amazon.com")

# Batch validation
results = await URLValidationHelper.validate_batch_urls([
    "google.com",
    "microsoft.com",
    "apple.com"
])

# Check if safe
is_safe = await URLValidationHelper.is_url_safe("company.com")

# Get warnings
warnings = await URLValidationHelper.check_suspicious_patterns("bit.ly/short")
```

### Example 4: Frontend - JavaScript

```javascript
// Validate URL
async function validateURL(url) {
  const response = await fetch('/api/company/validate-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  
  const data = await response.json();
  
  if (data.data.is_valid) {
    console.log('✅ Valid:', data.data.authenticated_url);
  } else {
    console.error('❌ Invalid:', data.data.errors);
  }
}

// Use in your code
await validateURL("google.com");
```

### Example 5: Create Company with Validation

```python
# This is already integrated in the POST /api/company/create endpoint
# The URL is automatically validated before creating the company

POST /api/company/create
{
  "salesperson_id": "sp_123",
  "company_url": "google.com",  # Can be with or without https://
  "auto_fetch": true
}

# Response will include validation details:
{
  "success": true,
  "data": {
    "company_id": "c_xyz",
    "company_url": "https://google.com",  # Authenticated URL
    "url_validation": {
      "is_valid": true,
      "ssl_valid": true,
      "domain": "google.com"
    }
  }
}
```

## API Endpoints Summary

### 1. **Validate URL**
```
POST /api/company/validate-url
Body: { "url": "google.com" }
Returns: Complete validation details
```

### 2. **Redirect to Authenticated URL**
```
GET /api/company/redirect?url=google.com
Returns: HTTP 307 redirect to https://google.com
```

### 3. **Create Company** (with validation)
```
POST /api/company/create
Body: { "company_url": "google.com", ... }
Returns: Company created with authenticated URL
```

## What Gets Checked?

| Check | What It Does | Example |
|-------|-------------|---------|
| **Format Validation** | Ensures URL is properly formatted | ✅ `google.com` → ✅ `https://google.com` |
| **SSL Certificate** | Verifies HTTPS certificate is valid | ✅ Google (valid) vs ⚠️ Self-signed cert |
| **Reachability** | Checks if website responds | ✅ Working website vs ❌ Offline website |
| **HTTP Status** | Verifies 200-399 status codes | ✅ 200 OK vs ❌ 404 Not Found |
| **Domain Reputation** | Detects suspicious domains | ✅ amazon.com vs ⚠️ amazon-phishing.tk |
| **Redirect Chains** | Checks for suspicious redirects | ✅ Same domain vs ⚠️ Redirect to other domain |
| **Phishing Patterns** | Detects common phishing techniques | ✅ Real domain vs ⚠️ IDN homoglyph attack |

## Common Scenarios

### Scenario 1: User Enters "google.com"
```
Input: "google.com"
↓ Validation
✅ Normalized to: "https://google.com"
✅ SSL Certificate: Valid
✅ Website: Reachable (HTTP 200)
✅ Domain: Legitimate
Result: ✅ VALID & AUTHENTICATED
Output: "https://google.com"
```

### Scenario 2: User Enters "unreachable-company.com"
```
Input: "unreachable-company.com"
↓ Validation
✅ Normalized to: "https://unreachable-company.com"
❌ Website: Not reachable (timeout)
Result: ❌ INVALID
Errors: ["URL not reachable"]
Output: null
```

### Scenario 3: User Enters "amazon-store.tk"
```
Input: "amazon-store.tk"
↓ Validation
✅ Normalized to: "https://amazon-store.tk"
✅ Website: Reachable
⚠️ SSL: Self-signed
⚠️ Domain: Suspicious TLD (.tk)
Result: ⚠️ VALID BUT WITH WARNINGS
Warnings: ["Domain uses commonly abused TLD: .tk"]
Output: Can still use but flagged
```

## Integration Checklist

- [ ] Copy `url_validator_service.py` to `app/services/`
- [ ] Copy `url_validation_helper.py` to `app/utils/`
- [ ] Copy `url-validator-client.html` to project root
- [ ] Check that `httpx` is in `requirements.txt`
- [ ] Verify company route imports `url_validator`
- [ ] Test the validation endpoint: `POST /api/company/validate-url`
- [ ] Test the redirect endpoint: `GET /api/company/redirect?url=google.com`
- [ ] Test company creation: `POST /api/company/create`
- [ ] Update frontend to use new endpoints

## Testing

### Test 1: Validate Valid URL
```bash
curl -X POST http://localhost:8000/api/company/validate-url \
  -H "Content-Type: application/json" \
  -d '{"url":"google.com"}'
```

### Test 2: Validate Invalid URL
```bash
curl -X POST http://localhost:8000/api/company/validate-url \
  -H "Content-Type: application/json" \
  -d '{"url":"unreachable-site-xyz.com"}'
```

### Test 3: Redirect to URL
```bash
curl -X GET "http://localhost:8000/api/company/redirect?url=google.com"
# Should redirect to https://google.com
```

### Test 4: Create Company
```bash
curl -X POST http://localhost:8000/api/company/create \
  -H "Content-Type: application/json" \
  -d '{
    "salesperson_id":"sp_123",
    "company_url":"google.com",
    "auto_fetch":true
  }'
```

## Troubleshooting

### Issue: "URL not reachable" for valid sites
**Solution:** 
- Check network connectivity
- Verify firewall isn't blocking
- Try the URL in browser first
- Check for rate limiting

### Issue: SSL certificate warnings
**Solution:**
- Some companies use self-signed certs (legitimate)
- Check warnings - they're flagged but don't block access
- Review security policy for your use case

### Issue: Slow validation
**Solution:**
- SSL checking can take time
- Consider caching results
- Use batch validation for multiple URLs
- Run validation asynchronously

## Next Steps

1. **Test the UI**: Open `url-validator-client.html` in your browser
2. **Test the API**: Use the curl commands above
3. **Integrate into your form**: Use the validation endpoint before form submission
4. **Monitor logs**: Track which URLs are validated
5. **Customize warnings**: Adjust suspicious patterns for your use case

## Support

For detailed documentation, see: `URL_VALIDATOR_DOCS.md`
For helper functions, see: `app/utils/url_validation_helper.py`
For core logic, see: `app/services/url_validator_service.py`

---

**Ready to use!** 🎉

Your system now automatically validates company URLs and redirects users to authenticated websites. Users can enter URLs in any format, and the system will handle validation and normalization automatically.
