#!/usr/bin/env python3
"""
Enhanced 8th Period Auto-Signup Monitor
True automation with Playwright - monitors AND automatically signs up for favorite clubs
"""

import os
import re
import json
import time
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IonAutoSignupMonitor:
    def __init__(self):
        self.load_config()
        self.session_file = "ion_session.json"
        self.previous_signups = set()  # Track successful signups to avoid duplicates
        
    def load_config(self):
        """Load configuration from environment variables"""
        self.login_url = os.getenv('LOGIN_URL', 'https://ion.tjhsst.edu/login')
        self.username = os.getenv('USERNAME', '')
        self.password = os.getenv('PASSWORD', '')
        
        # Parse URL range
        url_base = os.getenv('URL_BASE', 'https://ion.tjhsst.edu/eighth/signup/')
        url_start = int(os.getenv('URL_START', '4555'))
        url_end = int(os.getenv('URL_END', '4583'))
        self.monitor_urls = [f"{url_base}{i}" for i in range(url_start, url_end + 1)]
        
        # Parse favorites list with priority (first = highest priority)
        favorites_str = os.getenv('FAVORITES', '')
        self.favorites = [club.strip() for club in favorites_str.split(',') if club.strip()]
        
        # Notification settings
        self.notification_email = os.getenv('NOTIFICATION_EMAIL', '')
        self.notification_password = os.getenv('NOTIFICATION_PASSWORD', '')
        self.target_sms = os.getenv('TARGET_SMS', '')
        
        # Auto-signup settings
        self.auto_signup_enabled = os.getenv('AUTO_SIGNUP', 'true').lower() == 'true'
        self.rate_limit_delay = int(os.getenv('RATE_LIMIT_DELAY', '15'))
        
        logger.info(f"Monitoring {len(self.monitor_urls)} URLs for {len(self.favorites)} favorite clubs")
        logger.info(f"Auto-signup: {'ENABLED' if self.auto_signup_enabled else 'DISABLED'}")

    def send_sms_notification(self, message):
        """Send SMS notification via email gateway"""
        if not self.notification_email or not self.target_sms:
            logger.warning("SMS notification not configured")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.notification_email
            msg['To'] = self.target_sms
            msg['Subject'] = "8th Period Alert"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.notification_email, self.notification_password)
            server.send_message(msg)
            server.quit()
            
            logger.info("SMS notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def authenticate(self, page):
        """Handle Ion authentication with session persistence"""
        try:
            # Try to load existing session
            if os.path.exists(self.session_file):
                logger.info("Loading existing session...")
                # Session loaded via context creation
                
                # Test if session is still valid
                page.goto("https://ion.tjhsst.edu/eighth/", wait_until="networkidle", timeout=30000)
                
                if "login" not in page.url.lower():
                    logger.info("Existing session valid")
                    return True
                else:
                    logger.info("Session expired, re-authenticating...")
            
            # Perform login
            logger.info("Logging in to Ion...")
            page.goto(self.login_url, wait_until="networkidle", timeout=30000)
            
            # Extract CSRF token
            csrf_element = page.locator('input[name*="csrf"]').first
            csrf_token = csrf_element.get_attribute('value') if csrf_element.is_visible() else None
            
            # Fill login form
            page.fill('input[name="username"]', self.username)
            page.fill('input[name="password"]', self.password)
            
            # Submit form
            page.click('input[type="submit"], button[type="submit"]')
            
            # Wait for redirect (either to 2FA or dashboard)
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Check if 2FA is required
            if "two-factor" in page.url.lower() or page.locator('input[name*="otp"], input[name*="token"]').is_visible():
                logger.warning("2FA required - manual intervention needed")
                print("2FA code required. Please check your authenticator app and enter the code in the browser.")
                input("Press ENTER when you have completed 2FA...")
                page.wait_for_load_state("networkidle", timeout=60000)
            
            # Verify successful login
            if "eighth" in page.url.lower() or "dashboard" in page.url.lower():
                logger.info("Authentication successful")
                # Save session
                page.context.storage_state(path=self.session_file)
                return True
            else:
                logger.error(f"Authentication failed - current URL: {page.url}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def find_club_matches(self, page_content):
        """Find clubs on page that match favorites list"""
        matches = []
        
        # Look for activity rows/containers
        activity_selectors = [
            '.activity-row',
            '.signup-row', 
            'tr.activity',
            '.eighth-activity',
            '[data-activity]'
        ]
        
        for selector in activity_selectors:
            activities = page_content.locator(selector).all()
            if activities:
                break
        else:
            # Fallback: look for any element containing activity names
            activities = page_content.locator('*').filter(has_text=re.compile('club|investment|fbla|launch', re.I)).all()
        
        for activity in activities[:20]:  # Limit search to prevent timeouts
            try:
                activity_text = activity.inner_text()
                activity_html = activity.inner_html()
                
                # Extract club name
                club_name = self.extract_club_name(activity_text)
                if not club_name:
                    continue
                
                # Check if it matches favorites
                matching_favorite = self.check_favorite_match(club_name)
                if not matching_favorite:
                    continue
                
                # Check availability
                is_available = self.check_availability(activity_text, activity_html)
                if not is_available:
                    continue
                
                # Find signup element
                signup_element = self.find_signup_element(activity)
                if not signup_element:
                    continue
                
                matches.append({
                    'name': club_name,
                    'favorite': matching_favorite,
                    'element': activity,
                    'signup_element': signup_element,
                    'priority': self.favorites.index(matching_favorite)
                })
                
            except Exception as e:
                logger.debug(f"Error processing activity element: {e}")
                continue
        
        # Sort by priority (lower index = higher priority)
        matches.sort(key=lambda x: x['priority'])
        return matches

    def extract_club_name(self, text):
        """Extract club name from activity text"""
        # Clean up text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            # Skip status lines
            if any(word in line.lower() for word in ['signups', 'capacity', 'room', 'sponsor']):
                continue
            
            # Look for actual club names
            if len(line) > 5 and not line.isdigit():
                return line
        
        return lines[0] if lines else None

    def check_favorite_match(self, club_name):
        """Check if club name matches any favorite (fuzzy matching)"""
        for favorite in self.favorites:
            if (favorite.lower() in club_name.lower() or 
                club_name.lower() in favorite.lower() or
                any(word.lower() in club_name.lower() for word in favorite.split() if len(word) > 3)):
                return favorite
        return None

    def check_availability(self, text, html):
        """Check if activity has available spots"""
        unavailable_patterns = [
            r'full', r'closed', r'0/\d+', r'(\d+)/\1', r'waitlist', 
            r'cancelled', r'no\s+space', r'disabled'
        ]
        
        combined_text = f"{text} {html}".lower()
        
        for pattern in unavailable_patterns:
            if re.search(pattern, combined_text, re.I):
                return False
        
        return True

    def find_signup_element(self, activity_element):
        """Find clickable signup element within activity"""
        signup_selectors = [
            'button:has-text("Sign up")',
            'a:has-text("Sign up")',
            'input[value*="Sign up"]',
            'button:has-text("Join")',
            'a:has-text("Join")',
            '.signup-button',
            '.btn-signup'
        ]
        
        for selector in signup_selectors:
            element = activity_element.locator(selector).first
            if element.is_visible():
                return element
        
        return None

    def attempt_signup(self, page, match):
        """Attempt to sign up for a specific activity"""
        try:
            logger.info(f"Attempting signup for: {match['name']}")
            
            # Click signup element
            signup_element = match['signup_element']
            signup_element.scroll_into_view_if_needed()
            signup_element.click()
            
            # Wait for response
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Handle confirmation dialog if present
            confirmation_selectors = [
                'button:has-text("Confirm")',
                'button:has-text("Yes")', 
                'button:has-text("OK")',
                '.modal-confirm button',
                '.confirm-button'
            ]
            
            for selector in confirmation_selectors:
                if page.locator(selector).is_visible():
                    logger.info("Confirming signup...")
                    page.locator(selector).click()
                    page.wait_for_load_state("networkidle", timeout=10000)
                    break
            
            # Check result
            success, message = self.detect_signup_result(page)
            
            if success:
                logger.info(f"SUCCESS: Signed up for {match['name']}")
                self.previous_signups.add(match['name'])
                
                # Send success notification
                notification = f"AUTO-SIGNUP SUCCESS!\n\n{match['name']}\nPage: {page.url}\nTime: {datetime.now().strftime('%H:%M:%S')}\n\n{message}"
                self.send_sms_notification(notification)
                
                return True, message
            else:
                logger.warning(f"FAILED: {match['name']} - {message}")
                return False, message
                
        except Exception as e:
            error_msg = f"Signup error: {e}"
            logger.error(f"ERROR: {match['name']} - {error_msg}")
            return False, error_msg

    def detect_signup_result(self, page):
        """Detect if signup was successful or failed"""
        success_selectors = [
            '.alert-success',
            '.success-message',
            '.notification.success',
            '.message.success'
        ]
        
        error_selectors = [
            '.alert-error', 
            '.error-message',
            '.notification.error',
            '.message.error'
        ]
        
        # Check for success indicators
        for selector in success_selectors:
            if page.locator(selector).is_visible():
                message = page.locator(selector).inner_text()
                return True, message
        
        # Check for error indicators  
        for selector in error_selectors:
            if page.locator(selector).is_visible():
                message = page.locator(selector).inner_text()
                return False, message
        
        # Check URL for success patterns
        if "success" in page.url.lower() or "signed-up" in page.url.lower():
            return True, "Signup appeared successful (URL changed)"
        
        # Check page content for success text
        page_text = page.content().lower()
        success_patterns = ['successfully signed up', 'registration confirmed', 'added to activity']
        error_patterns = ['already signed up', 'activity is full', 'registration failed']
        
        for pattern in success_patterns:
            if pattern in page_text:
                return True, f"Success detected: {pattern}"
        
        for pattern in error_patterns:
            if pattern in page_text:
                return False, f"Error detected: {pattern}"
        
        return None, "Result unclear"

    def monitor_page(self, page, url):
        """Monitor a single signup page for available favorites"""
        try:
            logger.info(f"Checking: {url}")
            
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Check if redirected to login
            if "login" in page.url.lower():
                logger.warning("Session expired, re-authenticating...")
                if not self.authenticate(page):
                    return []
                page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Find matching activities
            matches = self.find_club_matches(page)
            
            if matches:
                logger.info(f"Found {len(matches)} matching activities on {url}")
                for match in matches:
                    logger.info(f"  - {match['name']} (priority {match['priority']})")
            
            return matches
            
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout loading {url}")
            return []
        except Exception as e:
            logger.error(f"Error monitoring {url}: {e}")
            return []

    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            
            # Create context with session if available
            if os.path.exists(self.session_file):
                context = browser.new_context(storage_state=self.session_file)
            else:
                context = browser.new_context()
            
            page = context.new_page()
            
            try:
                # Authenticate
                if not self.authenticate(page):
                    logger.error("Authentication failed, skipping cycle")
                    return False
                
                all_matches = []
                
                # Check each signup page
                for i, url in enumerate(self.monitor_urls):
                    matches = self.monitor_page(page, url)
                    
                    if matches:
                        all_matches.extend(matches)
                        
                        # If auto-signup enabled, try to sign up for highest priority match
                        if self.auto_signup_enabled:
                            best_match = matches[0]  # Already sorted by priority
                            
                            # Skip if already signed up
                            if best_match['name'] in self.previous_signups:
                                logger.info(f"Already signed up for {best_match['name']}, skipping")
                                continue
                            
                            success, message = self.attempt_signup(page, best_match)
                            
                            if success:
                                logger.info("Auto-signup successful, stopping monitoring cycle")
                                return True  # Stop after successful signup
                    
                    # Rate limiting
                    if i < len(self.monitor_urls) - 1:
                        time.sleep(self.rate_limit_delay)
                
                # Send summary notification if matches found but no signup
                if all_matches and not self.auto_signup_enabled:
                    message_parts = ["Available favorites found (auto-signup disabled):"]
                    for match in all_matches[:5]:  # Limit to top 5
                        message_parts.append(f"- {match['name']}")
                    
                    self.send_sms_notification('\n'.join(message_parts))
                
                return len(all_matches) > 0
                
            finally:
                browser.close()

    def run_continuous(self):
        """Run continuous monitoring"""
        logger.info("Starting continuous 8th period auto-signup monitoring...")
        logger.info(f"Favorites (priority order): {', '.join(self.favorites)}")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"=== Monitoring Cycle {cycle_count} ===")
                
                success = self.run_monitoring_cycle()
                
                if success and self.auto_signup_enabled:
                    logger.info("Successful signup completed. Monitoring will continue for other periods.")
                
                logger.info(f"Cycle {cycle_count} completed. Next check in 10 minutes...")
                time.sleep(600)  # 10 minutes between cycles
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                logger.info("Waiting 2 minutes before retry...")
                time.sleep(120)

def main():
    """Main entry point"""
    monitor = IonAutoSignupMonitor()
    
    # Check configuration
    if not monitor.username or not monitor.password:
        logger.error("USERNAME and PASSWORD environment variables are required")
        return
    
    if not monitor.favorites:
        logger.error("FAVORITES environment variable is required")
        return
    
    # Run monitoring
    monitor.run_continuous()

if __name__ == "__main__":
    main()