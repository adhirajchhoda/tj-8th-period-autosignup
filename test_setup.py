#!/usr/bin/env python3
"""
Setup Test Script
Validates that all configuration is correct before deploying
"""

import os
import re
import smtplib
from email.mime.text import MIMEText

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("Testing Environment Variables...")
    
    required_vars = [
        'USERNAME', 'PASSWORD', 'LOGIN_URL',
        'URL_BASE', 'URL_START', 'URL_END', 'FAVORITES',
        'NOTIFICATION_EMAIL', 'NOTIFICATION_PASSWORD', 'TARGET_SMS'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"FAIL: Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("PASS: All environment variables are set")
    return True

def test_url_configuration():
    """Test URL configuration"""
    print("\nTesting URL Configuration...")
    
    url_base = os.getenv('URL_BASE', '')
    url_start = os.getenv('URL_START', '')
    url_end = os.getenv('URL_END', '')
    
    if not url_base.startswith('http'):
        print(f"FAIL: URL_BASE should start with http/https: {url_base}")
        return False
    
    try:
        start_num = int(url_start)
        end_num = int(url_end)
        
        if start_num >= end_num:
            print(f"FAIL: URL_START ({start_num}) should be less than URL_END ({end_num})")
            return False
        
        if end_num - start_num > 50:
            print(f"WARNING: Large URL range ({end_num - start_num + 1} URLs). This may be slow.")
        
        print(f"PASS: URL configuration valid: {start_num} to {end_num} ({end_num - start_num + 1} URLs)")
        return True
        
    except ValueError:
        print(f"FAIL: URL_START and URL_END must be numbers: start={url_start}, end={url_end}")
        return False

def test_favorites_configuration():
    """Test favorites configuration"""
    print("\nTesting Favorites Configuration...")
    
    favorites_str = os.getenv('FAVORITES', '')
    if not favorites_str:
        print("FAIL: FAVORITES is empty")
        return False
    
    favorites = [club.strip() for club in favorites_str.split(',') if club.strip()]
    
    if not favorites:
        print("FAIL: No valid favorites found after parsing")
        return False
    
    print(f"PASS: Found {len(favorites)} favorite clubs:")
    for i, club in enumerate(favorites, 1):
        print(f"   {i}. {club}")
    
    return True

def test_sms_configuration():
    """Test SMS configuration"""
    print("\nTesting SMS Configuration...")
    
    target_sms = os.getenv('TARGET_SMS', '')
    
    # Check format: number@carrier.com
    sms_pattern = r'^\d{10}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(sms_pattern, target_sms):
        print(f"FAIL: TARGET_SMS format incorrect: {target_sms}")
        print("   Expected format: 1234567890@carrier.com")
        print("   Common carriers:")
        print("     Verizon: @vtext.com")
        print("     AT&T: @txt.att.net")
        print("     T-Mobile: @tmomail.net")
        print("     Sprint: @messaging.sprintpcs.com")
        return False
    
    print(f"PASS: SMS format valid: {target_sms}")
    return True

def test_gmail_connection():
    """Test Gmail connection for SMS"""
    print("\nTesting Gmail Connection...")
    
    email = os.getenv('NOTIFICATION_EMAIL', '')
    password = os.getenv('NOTIFICATION_PASSWORD', '')
    
    if not email or not password:
        print("FAIL: Gmail credentials not configured")
        return False
    
    try:
        # Test SMTP connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        server.quit()
        
        print(f"PASS: Gmail connection successful: {email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print(f"FAIL: Gmail authentication failed for {email}")
        print("   Check that:")
        print("   - 2FA is enabled on your Gmail account")
        print("   - You're using an App Password (not your regular password)")
        print("   - The app password is correct (16 characters)")
        return False
        
    except Exception as e:
        print(f"FAIL: Gmail connection error: {e}")
        return False

def send_test_sms():
    """Send a test SMS"""
    print("\nSending Test SMS...")
    
    email = os.getenv('NOTIFICATION_EMAIL', '')
    password = os.getenv('NOTIFICATION_PASSWORD', '')
    target_sms = os.getenv('TARGET_SMS', '')
    
    try:
        msg = MIMEText("Test message from 8th Period Monitor setup")
        msg['Subject'] = "Test Setup"
        msg['From'] = email
        msg['To'] = target_sms
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        
        print(f"PASS: Test SMS sent to {target_sms}")
        print("   Check your phone for the test message")
        return True
        
    except Exception as e:
        print(f"FAIL: Failed to send test SMS: {e}")
        return False

def main():
    """Run all tests"""
    print("8th Period Monitor - Setup Test")
    print("=" * 50)
    
    tests = [
        test_environment_variables,
        test_url_configuration,
        test_favorites_configuration,
        test_sms_configuration,
        test_gmail_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            break  # Stop on first failure
    
    print("\n" + "=" * 50)
    
    if passed == total:
        print(f"SUCCESS: All tests passed ({passed}/{total})")
        
        # Optional: send test SMS
        print("\nOptional: Send test SMS? (y/N): ", end="")
        try:
            if input().lower().startswith('y'):
                send_test_sms()
        except (EOFError, KeyboardInterrupt):
            pass  # Running in automated environment
        
        print("\nSetup validation complete! Your monitor is ready to deploy.")
        return True
    else:
        print(f"FAILED: Tests failed ({passed}/{total})")
        print("\nFix the issues above before deploying.")
        return False

if __name__ == "__main__":
    main()