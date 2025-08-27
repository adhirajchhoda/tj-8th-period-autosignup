"""Configuration management for 8th period auto-signup system"""
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the auto-signup system"""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment variables"""
        # Authentication
        self.login_url = os.getenv('LOGIN_URL', 'https://ion.tjhsst.edu/login')
        self.username = os.getenv('USERNAME', '')
        self.password = os.getenv('PASSWORD', '')
        
        # URL configuration
        url_base = os.getenv('URL_BASE', 'https://ion.tjhsst.edu/eighth/signup/')
        url_start = int(os.getenv('URL_START', '4555'))
        url_end = int(os.getenv('URL_END', '4583'))
        self.monitor_urls = [f"{url_base}{i}" for i in range(url_start, url_end + 1)]
        
        # Favorites configuration
        favorites_str = os.getenv('FAVORITES', '')
        self.favorites = [club.strip() for club in favorites_str.split(',') if club.strip()]
        
        # Auto-signup settings
        self.auto_signup_enabled = os.getenv('AUTO_SIGNUP', 'true').lower() == 'true'
        self.rate_limit_delay = int(os.getenv('RATE_LIMIT_DELAY', '15'))
        
        # Notification settings
        self.notification_email = os.getenv('NOTIFICATION_EMAIL', '')
        self.notification_password = os.getenv('NOTIFICATION_PASSWORD', '')
        self.target_sms = os.getenv('TARGET_SMS', '')
        
        logger.info(f"Configuration loaded: {len(self.monitor_urls)} URLs, {len(self.favorites)} favorites")
        logger.info(f"Auto-signup: {'ENABLED' if self.auto_signup_enabled else 'DISABLED'}")
    
    def validate(self):
        """Validate configuration and return list of missing required settings"""
        missing = []
        
        if not self.username:
            missing.append('USERNAME')
        if not self.password:
            missing.append('PASSWORD')
        if not self.favorites:
            missing.append('FAVORITES')
            
        return missing
    
    @property
    def session_file(self):
        """Get session file path"""
        return "ion_session.json"