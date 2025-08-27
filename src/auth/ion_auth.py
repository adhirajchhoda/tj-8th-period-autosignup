"""Ion authentication and session management"""
import os
import logging
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class IonAuthenticator:
    """Handles Ion authentication and session management"""
    
    def __init__(self, config):
        self.config = config
        self.session_file = config.session_file
    
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
            page.goto(self.config.login_url, wait_until="networkidle", timeout=30000)
            
            # Extract CSRF token
            csrf_element = page.locator('input[name*="csrf"]').first
            csrf_token = csrf_element.get_attribute('value') if csrf_element.is_visible() else None
            
            # Fill login form
            page.fill('input[name="username"]', self.config.username)
            page.fill('input[name="password"]', self.config.password)
            
            # Submit form
            page.click('input[type="submit"], button[type="submit"]')
            
            # Wait for redirect (either to 2FA or dashboard)
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Check if 2FA is required
            if "two-factor" in page.url.lower() or page.locator('input[name*="otp"], input[name*="token"]').is_visible():
                logger.error("2FA required - cannot proceed with automated login")
                logger.error("This is a critical limitation for GitHub Actions automation")
                return False
            
            # Verify successful login
            if "eighth" in page.url.lower() or "dashboard" in page.url.lower():
                logger.info("Authentication successful")
                # Save session
                page.context.storage_state(path=self.session_file)
                return True
            else:
                logger.error(f"Authentication failed - current URL: {page.url}")
                return False
                
        except PlaywrightTimeoutError as e:
            logger.error(f"Authentication timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def is_authenticated(self, page):
        """Check if current session is authenticated"""
        try:
            current_url = page.url.lower()
            return "login" not in current_url and ("eighth" in current_url or "dashboard" in current_url)
        except:
            return False
    
    def handle_session_expiry(self, page):
        """Handle session expiry during monitoring"""
        if "login" in page.url.lower():
            logger.warning("Session expired during monitoring, re-authenticating...")
            return self.authenticate(page)
        return True