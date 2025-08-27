"""Playwright-based monitoring system for true auto-signup"""
import os
import time
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from .base_monitor import BaseMonitor
from ..auth.ion_auth import IonAuthenticator
from ..utils.club_matcher import ClubMatcher

logger = logging.getLogger(__name__)

class PlaywrightMonitor(BaseMonitor):
    """Playwright-based monitor with true auto-signup capability"""
    
    def __init__(self, config, notifier):
        super().__init__(config, notifier)
        self.authenticator = IonAuthenticator(config)
        self.club_matcher = ClubMatcher(config.favorites)
    
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
                self.notifier.send_signup_success(match['name'], page.url)
                return True, message
            else:
                logger.warning(f"FAILED: {match['name']} - {message}")
                return False, message
                
        except Exception as e:
            error_msg = f"Signup error: {e}"
            logger.error(f"ERROR: {match['name']} - {error_msg}")
            return False, error_msg
    
    def monitor_page(self, page, url):
        """Monitor a single signup page for available favorites"""
        try:
            logger.info(f"Checking: {url}")
            
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Check if redirected to login
            if not self.authenticator.handle_session_expiry(page):
                return []
            
            # Find matching activities
            matches = self.club_matcher.find_matches(page)
            
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
            if os.path.exists(self.config.session_file):
                context = browser.new_context(storage_state=self.config.session_file)
            else:
                context = browser.new_context()
            
            page = context.new_page()
            
            try:
                # Authenticate
                if not self.authenticator.authenticate(page):
                    logger.error("Authentication failed, skipping cycle")
                    return False
                
                all_matches = []
                
                # Check each signup page
                for i, url in enumerate(self.config.monitor_urls):
                    matches = self.monitor_page(page, url)
                    
                    if matches:
                        all_matches.extend(matches)
                        
                        # If auto-signup enabled, try to sign up for highest priority match
                        if self.config.auto_signup_enabled:
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
                    if i < len(self.config.monitor_urls) - 1:
                        time.sleep(self.config.rate_limit_delay)
                
                # Send summary notification if matches found but no signup
                if all_matches and not self.config.auto_signup_enabled:
                    self.notifier.send_favorites_available(all_matches)
                
                return len(all_matches) > 0
                
            finally:
                browser.close()