#!/usr/bin/env python3
"""
Local Testing Script for Auto-Signup System
Test authentication, page parsing, and signup flow locally before deploying
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

def setup_environment():
    """Setup test environment variables"""
    # Test credentials - replace with actual values for testing
    os.environ['LOGIN_URL'] = 'https://ion.tjhsst.edu/login'
    os.environ['USERNAME'] = '2027achhoda'
    os.environ['PASSWORD'] = 'Chickfilla.01'
    
    os.environ['URL_BASE'] = 'https://ion.tjhsst.edu/eighth/signup/'
    os.environ['URL_START'] = '4555'
    os.environ['URL_END'] = '4583'
    os.environ['FAVORITES'] = 'Investment Club,Future Business Leaders of American,FBLA,Future Business Leaders,FBL,Launch X'
    
    # Disable auto-signup for testing
    os.environ['AUTO_SIGNUP'] = 'false'
    os.environ['RATE_LIMIT_DELAY'] = '3'
    
    print("Environment configured for local testing")

def test_authentication():
    """Test Ion authentication flow"""
    print("\n=== Testing Authentication ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to login
            print("Navigating to Ion login...")
            page.goto("https://ion.tjhsst.edu/login", wait_until="networkidle")
            
            # Take screenshot
            page.screenshot(path="login_page.png", full_page=True)
            print("Screenshot saved: login_page.png")
            
            # Check login form elements
            username_field = page.locator('input[name="username"]')
            password_field = page.locator('input[name="password"]')
            submit_button = page.locator('input[type="submit"], button[type="submit"]')
            
            print(f"Username field found: {username_field.is_visible()}")
            print(f"Password field found: {password_field.is_visible()}")
            print(f"Submit button found: {submit_button.is_visible()}")
            
            # Manual login test
            print("\nFilling login form...")
            username_field.fill('2027achhoda')
            password_field.fill('Chickfilla.01')
            
            print("Ready to submit login (check browser window)")
            input("Press ENTER to submit login form...")
            
            submit_button.click()
            
            # Wait for redirect
            page.wait_for_load_state("networkidle", timeout=30000)
            
            print(f"Post-login URL: {page.url}")
            
            # Check if 2FA required
            if "two-factor" in page.url.lower() or page.locator('input[name*="otp"]').is_visible():
                print("2FA detected - handle manually in browser")
                input("Complete 2FA and press ENTER...")
                page.wait_for_load_state("networkidle", timeout=60000)
            
            # Save session
            context.storage_state(path="test_session.json")
            print("Session saved: test_session.json")
            
            # Test navigation to signup area
            page.goto("https://ion.tjhsst.edu/eighth/signup/4558")
            page.screenshot(path="signup_page.png", full_page=True)
            print("Signup page screenshot: signup_page.png")
            
            return True
            
        except Exception as e:
            print(f"Authentication test failed: {e}")
            return False
        finally:
            input("Press ENTER to close browser...")
            browser.close()

def test_page_parsing():
    """Test signup page parsing"""
    print("\n=== Testing Page Parsing ===")
    
    if not os.path.exists("test_session.json"):
        print("No session file found. Run authentication test first.")
        return False
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(storage_state="test_session.json")
        page = context.new_page()
        
        try:
            # Test parsing multiple pages
            test_urls = [
                "https://ion.tjhsst.edu/eighth/signup/4558",
                "https://ion.tjhsst.edu/eighth/signup/4570", 
                "https://ion.tjhsst.edu/eighth/signup/4580"
            ]
            
            for i, url in enumerate(test_urls):
                print(f"\nTesting URL {i+1}: {url}")
                
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Save HTML for analysis
                html_file = f"test_page_{i+1}.html"
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(page.content())
                print(f"HTML saved: {html_file}")
                
                # Take screenshot
                screenshot_file = f"test_page_{i+1}.png"
                page.screenshot(path=screenshot_file, full_page=True)
                print(f"Screenshot saved: {screenshot_file}")
                
                # Look for activities
                activities = page.locator('*').filter(has_text='club').all()
                print(f"Found {len(activities)} potential activities")
                
                # Look for favorites
                favorites = ['Investment Club', 'FBLA', 'Launch X']
                for favorite in favorites:
                    matches = page.locator('*').filter(has_text=favorite).all()
                    if matches:
                        print(f"  - Found '{favorite}': {len(matches)} matches")
                        
                        # Look for signup elements
                        for match in matches[:2]:  # Check first 2 matches
                            parent = match.locator('..')
                            signup_buttons = parent.locator('button, a').filter(has_text='Sign up').all()
                            if signup_buttons:
                                print(f"    - Signup button found for {favorite}")
            
            return True
            
        except Exception as e:
            print(f"Page parsing test failed: {e}")
            return False
        finally:
            input("Press ENTER to close browser...")
            browser.close()

def test_monitoring_cycle():
    """Test one monitoring cycle"""
    print("\n=== Testing Monitoring Cycle ===")
    
    try:
        # Import the actual monitor
        from auto_signup_monitor import IonAutoSignupMonitor
        
        # Create monitor instance
        monitor = IonAutoSignupMonitor()
        
        print(f"Favorites configured: {monitor.favorites}")
        print(f"URLs to monitor: {len(monitor.monitor_urls)}")
        print(f"Auto-signup enabled: {monitor.auto_signup_enabled}")
        
        # Run one cycle
        print("\nRunning monitoring cycle...")
        success = monitor.run_monitoring_cycle()
        
        print(f"Monitoring cycle completed. Success: {success}")
        return success
        
    except ImportError:
        print("Could not import auto_signup_monitor. Check dependencies.")
        return False
    except Exception as e:
        print(f"Monitoring test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("TJ 8th Period Auto-Signup - Local Testing")
    print("=" * 50)
    
    # Check if Playwright is installed
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright not installed.")
        print("Run: pip install playwright && python -m playwright install chromium")
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Test menu
    while True:
        print("\nTest Options:")
        print("1. Test Authentication Flow")
        print("2. Test Page Parsing") 
        print("3. Test Full Monitoring Cycle")
        print("4. Exit")
        
        choice = input("\nSelect test (1-4): ").strip()
        
        if choice == '1':
            test_authentication()
        elif choice == '2':
            test_page_parsing()
        elif choice == '3':
            test_monitoring_cycle()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Try again.")
    
    print("\nTesting completed. Check generated files for debugging info.")

if __name__ == "__main__":
    main()