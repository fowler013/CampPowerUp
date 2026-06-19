# 🔐 Camp Power-Up Security Implementation Guide

## Overview

This guide covers the comprehensive security features implemented in Camp Power-Up to protect sensitive camper and parent data.

## ✅ Implemented Security Features

### 1. Authentication & Authorization

#### User Management
- **Admin accounts** with role-based access control
- **Password hashing** using bcrypt with salt
- **Account lockout** after 5 failed login attempts (30-minute lockout)
- **Session management** with configurable timeout (8 hours default)
- **Mandatory password changes** for default accounts

#### Roles & Permissions
- **Admin**: Full system access, user management
- **Manager**: Communication, registration, reports
- **Staff**: Communication, registration only
- **Viewer**: Reports only

### 2. Data Protection

#### Encryption
- **Sensitive data encryption** using Fernet (AES 128)
- **Secure key storage** with proper file permissions (600)
- **Database encryption** for personally identifiable information (PII)

#### Secure Storage
- **Passwords**: bcrypt hashed with salt
- **Session data**: Encrypted and signed
- **Configuration**: Environment variables only

### 3. Input Validation & Protection

#### Rate Limiting
- **Login attempts**: 5 per minute
- **Email sending**: 10 per minute  
- **SMS sending**: 10 per minute
- **General API**: 200 per day, 50 per hour

#### CSRF Protection
- **Cross-site request forgery** protection enabled
- **Form tokens** validate all state-changing requests
- **AJAX protection** for API endpoints

### 4. Audit & Monitoring

#### Security Logging
- **Authentication events** (login/logout/failures)
- **User management** (creation/deletion/role changes)
- **Data access** (email sends, contact viewing)
- **System events** with IP addresses and user agents

#### Database Tables
- `security_audit`: All security events
- `user_sessions`: Active session tracking
- `users`: User accounts and security metadata

### 5. Network Security

#### HTTPS Configuration
- **TLS encryption** for all data in transit
- **Secure cookies** in production
- **HSTS headers** to enforce HTTPS

#### Headers & Policies
- **Security headers** prevent XSS, clickjacking
- **Content Security Policy** (CSP) to prevent injection
- **Referrer Policy** to protect user privacy

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Install security dependencies
pip install -r requirements.txt

# Initialize security database
python -c "from security import SecurityManager; SecurityManager()._create_security_tables(); SecurityManager()._create_default_admin()"

# Check initial admin credentials
cat INITIAL_ADMIN_CREDENTIALS.txt
```

### 2. First Login

1. Access the application: `http://localhost:5004`
2. You'll be redirected to login: `http://localhost:5004/admin/login`
3. Use credentials from `INITIAL_ADMIN_CREDENTIALS.txt`
4. **IMMEDIATELY** change the default password

### 3. Production Deployment

```bash
# Copy environment template
cp .env.example .env

# Configure production settings
nano .env

# Set production environment
export FLASK_ENV=production

# Validate configuration
python config.py
```

## 🛡️ Security Features In Detail

### Authentication Flow

1. **Login Request**: User submits credentials
2. **Rate Limiting**: Check if too many attempts
3. **Account Status**: Verify account not locked
4. **Password Verification**: bcrypt hash comparison
5. **Session Creation**: Secure session with timeout
6. **Audit Logging**: Record authentication event

### Authorization Checks

```python
@login_required              # Must be authenticated
@require_role('admin')       # Must have admin role
def admin_function():
    # Protected function
    pass
```

### Data Encryption

```python
# Encrypt sensitive data before storage
encrypted_data = encrypt_sensitive_data(sensitive_info)

# Decrypt when retrieving
decrypted_data = decrypt_sensitive_data(encrypted_data)
```

### Rate Limiting Protection

```python
@limiter.limit("10 per minute")  # Maximum 10 requests per minute
def send_email():
    # Rate-limited function
    pass
```

## 📋 Security Checklist

### Development Environment
- [ ] Default admin password changed
- [ ] `.env` file configured
- [ ] Security database initialized
- [ ] SSL/TLS certificates installed
- [ ] Audit logging enabled

### Production Environment
- [ ] Strong secret key (32+ characters)
- [ ] HTTPS enabled and enforced
- [ ] Secure cookies enabled
- [ ] Database backups encrypted
- [ ] Log monitoring configured
- [ ] Security scanning scheduled

### User Management
- [ ] Default accounts disabled or changed
- [ ] Role assignments reviewed
- [ ] Inactive accounts disabled
- [ ] Password policies enforced
- [ ] Session timeouts configured

## 🚨 Security Incidents

### If You Suspect a Breach

1. **Immediate Actions**:
   - Change all passwords
   - Revoke active sessions
   - Check audit logs

2. **Investigation**:
   ```sql
   -- Check recent failed login attempts
   SELECT * FROM security_audit 
   WHERE action = 'login_attempt' AND success = 0 
   ORDER BY timestamp DESC;
   
   -- Check unusual access patterns
   SELECT user_id, COUNT(*) as attempts, ip_address 
   FROM security_audit 
   WHERE timestamp > datetime('now', '-1 hour')
   GROUP BY user_id, ip_address;
   ```

3. **Recovery**:
   - Reset affected accounts
   - Update security policies
   - Document incident

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Generated | Flask secret key (32+ chars) |
| `SESSION_TIMEOUT_HOURS` | 8 | User session timeout |
| `MAX_LOGIN_ATTEMPTS` | 5 | Failed logins before lockout |
| `ACCOUNT_LOCKOUT_MINUTES` | 30 | Account lockout duration |
| `PASSWORD_MIN_LENGTH` | 8 | Minimum password length |
| `HTTPS_ONLY` | False (dev) | Force HTTPS in production |
| `SECURE_COOKIES` | False (dev) | Secure cookie flag |

### Security Settings

```python
# config.py
class ProductionConfig(Config):
    HTTPS_ONLY = True
    SECURE_COOKIES = True
    RATE_LIMIT_DEFAULT = '100 per day, 20 per hour'
    RATE_LIMIT_LOGIN = '3 per minute'
```

## 📖 Best Practices

### For Administrators

1. **Password Management**:
   - Use unique, strong passwords
   - Enable password managers
   - Regular password rotation

2. **Access Control**:
   - Principle of least privilege
   - Regular access reviews
   - Remove unused accounts

3. **Monitoring**:
   - Review audit logs weekly
   - Monitor failed login attempts
   - Set up security alerts

### For Developers

1. **Code Security**:
   - Input validation on all forms
   - SQL injection prevention
   - XSS protection
   - CSRF tokens on forms

2. **Data Handling**:
   - Encrypt sensitive data
   - Secure API endpoints
   - Validate file uploads
   - Sanitize user input

## 🆘 Support & Resources

### Internal Documentation
- `SECURITY_PLAN.md`: Complete security roadmap
- `requirements.txt`: Security dependencies
- `config.py`: Configuration management
- `security.py`: Core security implementation

### External Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/security/)
- [Python Cryptography](https://cryptography.io/)

### Emergency Contacts
- System Administrator: [Your Contact]
- Security Team: [Your Team Contact]
- Technical Support: [Support Contact]

---

**Last Updated**: January 2025
**Security Version**: 1.0
**Next Review**: [Schedule Date]
