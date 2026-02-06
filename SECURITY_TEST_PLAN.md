# Security Test Plan for OpenSlides Backend

This document outlines specific security tests that should be performed on the OpenSlides backend to validate the security analysis findings.

## 1. SQL Injection Testing

### 1.1 Filter Parameter Injection Tests

**Objective:** Verify that filter parameters are properly sanitized

**Test Cases:**
```python
# Test Case 1: Single quote injection in filter
test_filter = {
    "field": "name",
    "operator": "=",
    "value": "test' OR '1'='1"
}

# Test Case 2: UNION-based injection
test_filter = {
    "field": "name",
    "operator": "=",
    "value": "test' UNION SELECT * FROM user--"
}

# Test Case 3: Time-based blind injection
test_filter = {
    "field": "name", 
    "operator": "=",
    "value": "test' OR SLEEP(5)--"
}

# Test Case 4: Boolean-based blind injection
test_filter = {
    "field": "id",
    "operator": "=",
    "value": "1 OR 1=1"
}
```

**Expected Result:** All injection attempts should be properly escaped or rejected by the datastore service.

**Implementation:**
```python
# tests/security/test_sql_injection.py
import pytest
from openslides_backend.services.datastore.commands import FilterRequest
from openslides_backend.shared.filters import FilterOperator

class TestSQLInjection:
    def test_filter_single_quote_injection(self, datastore):
        """Test that single quotes in filter values don't cause SQL injection"""
        filter_obj = FilterOperator("name", "=", "test' OR '1'='1")
        # Should not raise exception or return unauthorized data
        result = datastore.filter("user", filter_obj, ["id", "name"])
        # Verify only legitimate results returned
        assert all("'" not in str(user.get("name", "")) for user in result.values())
    
    def test_filter_union_injection(self, datastore):
        """Test UNION-based SQL injection"""
        filter_obj = FilterOperator("name", "=", "test' UNION SELECT * FROM user--")
        result = datastore.filter("user", filter_obj, ["id", "name"])
        # Should return empty or only matching users, not all users
        assert len(result) <= 1
```

## 2. Cross-Site Scripting (XSS) Testing

### 2.1 Stored XSS Tests

**Objective:** Verify HTML sanitization prevents XSS attacks

**Test Cases:**
```python
# Test Case 1: Basic script tag
xss_payload1 = "<script>alert('XSS')</script>"

# Test Case 2: Event handler
xss_payload2 = '<img src=x onerror="alert(\'XSS\')">'

# Test Case 3: SVG-based XSS
xss_payload3 = '<svg onload="alert(\'XSS\')">'

# Test Case 4: Data URI
xss_payload4 = '<a href="data:text/html,<script>alert(\'XSS\')</script>">Click</a>'

# Test Case 5: JavaScript protocol
xss_payload5 = '<a href="javascript:alert(\'XSS\')">Click</a>'

# Test Case 6: DOM-based XSS
xss_payload6 = '<iframe src="javascript:alert(\'XSS\')"></iframe>'
```

**Implementation:**
```python
# tests/security/test_xss_prevention.py
import pytest
from openslides_backend.shared.util import validate_html

class TestXSSPrevention:
    xss_payloads = [
        "<script>alert('XSS')</script>",
        '<img src=x onerror="alert(\'XSS\')">',
        '<svg onload="alert(\'XSS\')">',
        '<a href="javascript:alert(\'XSS\')">Click</a>',
        '<iframe src="javascript:alert(\'XSS\')"></iframe>',
        '<body onload="alert(\'XSS\')">',
        '<input onfocus="alert(\'XSS\')" autofocus>',
        '<select onfocus="alert(\'XSS\')" autofocus>',
        '<textarea onfocus="alert(\'XSS\')" autofocus>',
        '<button onclick="alert(\'XSS\')">Click</button>',
    ]
    
    @pytest.mark.parametrize("payload", xss_payloads)
    def test_html_sanitization_removes_xss(self, payload):
        """Test that XSS payloads are properly sanitized"""
        sanitized = validate_html(payload)
        
        # Should not contain script tags
        assert "<script" not in sanitized.lower()
        
        # Should not contain event handlers
        assert "onerror" not in sanitized.lower()
        assert "onload" not in sanitized.lower()
        assert "onclick" not in sanitized.lower()
        assert "onfocus" not in sanitized.lower()
        
        # Should not contain javascript: protocol
        assert "javascript:" not in sanitized.lower()
    
    def test_motion_text_xss_prevention(self, action_handler, user):
        """Test XSS prevention in motion text"""
        xss_text = '<script>alert("XSS")</script><p>Valid content</p>'
        
        response = action_handler.handle_request(
            [{
                "action": "motion.create",
                "data": [{
                    "meeting_id": 1,
                    "title": "Test Motion",
                    "text": xss_text
                }]
            }],
            user_id=user.id
        )
        
        # Verify the stored text is sanitized
        motion_id = response[0]["id"]
        motion = datastore.get(f"motion/{motion_id}", ["text"])
        assert "<script" not in motion["text"].lower()
```

## 3. Insecure Direct Object Reference (IDOR) Testing

### 3.1 Cross-User Access Tests

**Objective:** Verify users cannot access other users' private data

**Test Cases:**
```python
# Test Case 1: User A tries to read User B's private data
# User A: ID 1, Committee A
# User B: ID 2, Committee B
# User A should not be able to access User B's data

# Test Case 2: User tries to update another user's profile
# Should be denied unless user has admin privileges

# Test Case 3: Meeting participant tries to access different meeting's data
# Should be denied

# Test Case 4: Committee member tries to access different committee's data
# Should be denied
```

**Implementation:**
```python
# tests/security/test_idor.py
import pytest
from openslides_backend.shared.exceptions import PermissionDenied

class TestIDOR:
    def test_user_cannot_access_other_user_data(
        self, action_handler, user1, user2
    ):
        """Test that User 1 cannot access User 2's private data"""
        # User 1 tries to get User 2's data
        with pytest.raises(PermissionDenied):
            action_handler.handle_request(
                [{
                    "action": "user.update",
                    "data": [{
                        "id": user2.id,
                        "email": "hacked@example.com"
                    }]
                }],
                user_id=user1.id
            )
    
    def test_meeting_participant_cannot_access_other_meeting(
        self, action_handler, user, meeting1, meeting2
    ):
        """Test meeting isolation"""
        # User is participant in meeting1, tries to access meeting2
        with pytest.raises(PermissionDenied):
            action_handler.handle_request(
                [{
                    "action": "motion.create",
                    "data": [{
                        "meeting_id": meeting2.id,
                        "title": "Unauthorized motion"
                    }]
                }],
                user_id=user.id
            )
    
    def test_committee_isolation(
        self, action_handler, user, committee1, committee2
    ):
        """Test committee data isolation"""
        # User is member of committee1, tries to access committee2
        with pytest.raises(PermissionDenied):
            action_handler.handle_request(
                [{
                    "action": "committee.update",
                    "data": [{
                        "id": committee2.id,
                        "name": "Hacked Committee"
                    }]
                }],
                user_id=user.id
            )
```

## 4. Authentication and Session Security Testing

### 4.1 Brute Force Protection Tests

**Objective:** Verify rate limiting prevents brute force attacks

**Test Cases:**
```python
# Test Case 1: Multiple failed login attempts
# Should be rate limited after N attempts

# Test Case 2: Password reset flood
# Should be rate limited

# Test Case 3: Account enumeration via timing
# Should have constant-time response for valid/invalid users
```

**Implementation:**
```python
# tests/security/test_authentication.py
import pytest
import time

class TestAuthenticationSecurity:
    def test_rate_limiting_on_login(self, auth_service):
        """Test that login endpoint is rate limited"""
        # Attempt multiple failed logins
        for i in range(10):
            try:
                auth_service.authenticate("user@example.com", "wrong_password")
            except Exception:
                pass
        
        # Next attempt should be rate limited
        with pytest.raises(TooManyRequests):
            auth_service.authenticate("user@example.com", "wrong_password")
    
    def test_timing_attack_prevention(self, auth_service):
        """Test that valid/invalid user lookups take similar time"""
        # Valid user
        start = time.time()
        try:
            auth_service.authenticate("valid@example.com", "wrong_password")
        except:
            pass
        valid_time = time.time() - start
        
        # Invalid user
        start = time.time()
        try:
            auth_service.authenticate("invalid@example.com", "wrong_password")
        except:
            pass
        invalid_time = time.time() - start
        
        # Time difference should be minimal (< 100ms)
        assert abs(valid_time - invalid_time) < 0.1
    
    def test_session_timeout(self, auth_service, user):
        """Test that sessions expire after timeout"""
        # Create session
        session_id = auth_service.authenticate(user.email, user.password)
        
        # Wait for timeout (mock time if needed)
        time.sleep(SESSION_TIMEOUT + 1)
        
        # Session should be invalid
        with pytest.raises(InvalidSession):
            auth_service.validate_session(session_id)
    
    def test_password_hash_strength(self, auth_service):
        """Test that password hashing uses strong algorithm"""
        password = "TestPassword123!"
        hashed = auth_service.hash(password)
        
        # Hash should be long enough (bcrypt: 60 chars, Argon2: 90+)
        assert len(hashed) >= 60
        
        # Should include salt
        # bcrypt format: $2b$rounds$salt+hash
        # Argon2 format: $argon2id$v=19$m=65536,t=3,p=4$salt$hash
        assert hashed.startswith(("$2b$", "$argon2"))
        
    def test_password_comparison_constant_time(self, auth_service):
        """Test that password comparison is timing-attack resistant"""
        password = "TestPassword123!"
        correct_hash = auth_service.hash(password)
        wrong_hash = auth_service.hash("WrongPassword123!")
        
        # Time multiple comparisons
        times_correct = []
        times_wrong = []
        
        for _ in range(100):
            # Correct password
            start = time.time()
            auth_service.is_equal(password, correct_hash)
            times_correct.append(time.time() - start)
            
            # Wrong password (same length)
            start = time.time()
            auth_service.is_equal(password, wrong_hash)
            times_wrong.append(time.time() - start)
        
        # Average times should be similar (within 10%)
        avg_correct = sum(times_correct) / len(times_correct)
        avg_wrong = sum(times_wrong) / len(times_wrong)
        assert abs(avg_correct - avg_wrong) / avg_correct < 0.1
```

## 5. Authorization Bypass Testing

### 5.1 Privilege Escalation Tests

**Objective:** Verify users cannot escalate their privileges

**Test Cases:**
```python
# Test Case 1: Regular user tries to become admin
# Test Case 2: Meeting participant tries to become meeting admin
# Test Case 3: User tries to grant themselves permissions
```

**Implementation:**
```python
# tests/security/test_authorization.py
import pytest

class TestAuthorizationSecurity:
    def test_user_cannot_self_promote_to_admin(
        self, action_handler, regular_user
    ):
        """Test that users cannot grant themselves admin privileges"""
        with pytest.raises(PermissionDenied):
            action_handler.handle_request(
                [{
                    "action": "user.update",
                    "data": [{
                        "id": regular_user.id,
                        "organization_management_level": "superadmin"
                    }]
                }],
                user_id=regular_user.id
            )
    
    def test_meeting_participant_cannot_become_admin(
        self, action_handler, participant, meeting
    ):
        """Test meeting permission escalation prevention"""
        with pytest.raises(PermissionDenied):
            action_handler.handle_request(
                [{
                    "action": "meeting_user.update",
                    "data": [{
                        "id": participant.meeting_user_id,
                        "group_ids": [meeting.admin_group_id]
                    }]
                }],
                user_id=participant.id
            )
```

## 6. Mass Assignment Testing

### 6.1 Protected Field Tests

**Objective:** Verify protected fields cannot be set via mass assignment

**Test Cases:**
```python
# Test Case 1: Try to set 'id' field in update
# Test Case 2: Try to set 'created_at' in create
# Test Case 3: Try to set 'meta_*' fields
# Test Case 4: Try to set permission-related fields without permission
```

**Implementation:**
```python
# tests/security/test_mass_assignment.py
import pytest

class TestMassAssignment:
    def test_cannot_override_id_field(self, action_handler, user):
        """Test that ID field cannot be overridden"""
        original_id = user.id
        
        response = action_handler.handle_request(
            [{
                "action": "user.update",
                "data": [{
                    "id": original_id,
                    "id": 9999,  # Try to change ID
                    "username": "updated"
                }]
            }],
            user_id=user.id
        )
        
        # ID should remain unchanged
        assert response[0]["id"] == original_id
    
    def test_cannot_set_meta_fields(self, action_handler, user):
        """Test that meta_ fields are protected"""
        with pytest.raises(ActionException):
            action_handler.handle_request(
                [{
                    "action": "user.update",
                    "data": [{
                        "id": user.id,
                        "meta_position": 9999
                    }]
                }],
                user_id=user.id
            )
```

## 7. CSRF Testing

### 7.1 Token Validation Tests

**Objective:** Verify CSRF protection is properly implemented

**Test Cases:**
```python
# Test Case 1: Request without CSRF token should be rejected
# Test Case 2: Request with invalid CSRF token should be rejected  
# Test Case 3: CSRF token should be tied to session
# Test Case 4: CSRF token should expire
```

**Implementation:**
```python
# tests/security/test_csrf.py
import pytest

class TestCSRF:
    def test_state_changing_request_requires_csrf_token(self, client):
        """Test that POST requests require CSRF token"""
        response = client.post(
            "/system/action/handle_request",
            json=[{
                "action": "user.create",
                "data": [{"username": "test"}]
            }],
            # No CSRF token
        )
        assert response.status_code == 403
    
    def test_invalid_csrf_token_rejected(self, client, session):
        """Test that invalid CSRF tokens are rejected"""
        response = client.post(
            "/system/action/handle_request",
            json=[{
                "action": "user.create",
                "data": [{"username": "test"}]
            }],
            headers={"X-CSRF-Token": "invalid_token"}
        )
        assert response.status_code == 403
```

## 8. Input Validation Testing

### 8.1 Schema Validation Tests

**Objective:** Verify JSON schema validation catches invalid input

**Test Cases:**
```python
# Test Case 1: Missing required fields
# Test Case 2: Invalid field types
# Test Case 3: Extra unexpected fields
# Test Case 4: Array/object nesting validation
# Test Case 5: String length limits
```

**Implementation:**
```python
# tests/security/test_input_validation.py
import pytest

class TestInputValidation:
    def test_missing_required_fields(self, action_handler):
        """Test that missing required fields are rejected"""
        with pytest.raises(ActionException):
            action_handler.handle_request(
                [{
                    "action": "user.create",
                    "data": [{
                        # Missing required fields
                        "email": "test@example.com"
                    }]
                }],
                user_id=1
            )
    
    def test_invalid_field_types(self, action_handler):
        """Test that invalid field types are rejected"""
        with pytest.raises(ActionException):
            action_handler.handle_request(
                [{
                    "action": "meeting.create",
                    "data": [{
                        "name": "Test Meeting",
                        "start_time": "not_a_number"  # Should be int
                    }]
                }],
                user_id=1
            )
    
    def test_string_length_limits(self, action_handler):
        """Test that excessively long strings are rejected"""
        long_string = "A" * 10000000  # 10MB string
        
        with pytest.raises(ActionException):
            action_handler.handle_request(
                [{
                    "action": "user.create",
                    "data": [{
                        "username": long_string
                    }]
                }],
                user_id=1
            )
```

## 9. Dependency Security Testing

### 9.1 Vulnerability Scanning

**Commands to run:**
```bash
# Install security scanners
pip install pip-audit safety

# Run pip-audit
pip-audit -r requirements/requirements_production.txt

# Run safety check
safety check -r requirements/requirements_production.txt

# Check for outdated packages
pip list --outdated
```

## 10. Penetration Testing Checklist

### Manual Tests to Perform:

- [ ] SQL Injection in all filter/search/sort parameters
- [ ] XSS in all text input fields (motion text, comments, descriptions, etc.)
- [ ] IDOR on all resources (users, meetings, committees, motions, etc.)
- [ ] Authentication bypass attempts
- [ ] Session fixation attacks
- [ ] Session hijacking attempts
- [ ] CSRF on all state-changing operations
- [ ] Mass assignment on all create/update actions
- [ ] Privilege escalation attempts
- [ ] Rate limiting on all endpoints
- [ ] File upload vulnerabilities (if applicable)
- [ ] XML External Entity (XXE) attacks (if XML parsing used)
- [ ] Server-Side Request Forgery (SSRF)
- [ ] Information disclosure via error messages
- [ ] Directory traversal attacks
- [ ] Command injection

## Summary

This test plan provides comprehensive security testing coverage for the OpenSlides backend. All tests should be implemented and run regularly as part of the CI/CD pipeline.

**Priority Order:**
1. High Priority: Authentication, Authorization, IDOR, SQL Injection
2. Medium Priority: XSS, CSRF, Mass Assignment, Input Validation
3. Low Priority: Timing attacks, Dependency scanning

**Continuous Testing:**
- Run security tests on every commit
- Run full penetration tests quarterly
- Update tests when new features are added
- Re-test after dependency updates
