"""Base monitoring class for 8th period signup systems"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseMonitor(ABC):
    """Abstract base class for 8th period monitors"""
    
    def __init__(self, config, notifier):
        self.config = config
        self.notifier = notifier
        self.previous_signups = set()  # Track successful signups to avoid duplicates
    
    @abstractmethod
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        pass
    
    @abstractmethod
    def monitor_page(self, url):
        """Monitor a single signup page"""
        pass
    
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
    
    def run_continuous(self):
        """Run continuous monitoring"""
        logger.info("Starting continuous 8th period monitoring...")
        logger.info(f"Favorites (priority order): {', '.join(self.config.favorites)}")
        
        # Validate configuration
        missing = self.config.validate()
        if missing:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
            return
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"=== Monitoring Cycle {cycle_count} ===")
                
                success = self.run_monitoring_cycle()
                
                if success and self.config.auto_signup_enabled:
                    logger.info("Successful signup completed. Monitoring will continue for other periods.")
                
                logger.info(f"Cycle {cycle_count} completed. Next check in 10 minutes...")
                import time
                time.sleep(600)  # 10 minutes between cycles
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                logger.info("Waiting 2 minutes before retry...")
                import time
                time.sleep(120)