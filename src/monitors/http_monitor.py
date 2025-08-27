#!/usr/bin/env python3
"""
Generic Webpage Monitor
Monitors specified URLs for content changes and sends notifications
"""

import os
import re
import json
import time
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebpageMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.previous_state = {}
        self.load_config()
        
    def load_config(self):
        """Load configuration from environment variables"""
        self.login_url = os.getenv('LOGIN_URL', '')
        self.username = os.getenv('USERNAME', '')
        self.password = os.getenv('PASSWORD', '')
        
        # Parse URL range
        url_base = os.getenv('URL_BASE', 'https://ion.tjhsst.edu/eighth/signup/')
        url_start = int(os.getenv('URL_START', '4555'))
        url_end = int(os.getenv('URL_END', '4583'))
        self.monitor_urls = [f"{url_base}{i}" for i in range(url_start, url_end + 1)]
        
        # Parse favorites list
        favorites_str = os.getenv('FAVORITES', '')
        self.favorites = [club.strip() for club in favorites_str.split(',') if club.strip()]
        
        # Notification settings
        self.notification_email = os.getenv('NOTIFICATION_EMAIL', '')
        self.notification_password = os.getenv('NOTIFICATION_PASSWORD', '')
        self.target_sms = os.getenv('TARGET_SMS', '')  # Format: number@carrier.com
        
        # Rate limiting
        self.rate_limit_delay = int(os.getenv('RATE_LIMIT_DELAY', '15'))
        
        logger.info(f"Monitoring {len(self.monitor_urls)} URLs for {len(self.favorites)} favorite clubs")
    
    def authenticate(self):
        """Authenticate with the target site"""
        if not self.login_url or not self.username or not self.password:
            logger.warning("No login credentials provided, skipping authentication")
            return True
            
        try:
            # Get login page to extract any CSRF tokens
            login_page = self.session.get(self.login_url, timeout=30)
            soup = BeautifulSoup(login_page.content, 'html.parser')
            
            # Common CSRF token patterns
            csrf_token = None
            csrf_input = soup.find('input', {'name': re.compile(r'csrf|token', re.I)})
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            # Prepare login data
            login_data = {
                'username': self.username,
                'password': self.password
            }
            
            if csrf_token:
                # Add CSRF token with common field names
                for field_name in ['csrfmiddlewaretoken', 'csrf_token', '_token']:
                    login_data[field_name] = csrf_token
            
            # Submit login
            response = self.session.post(self.login_url, data=login_data, timeout=30)
            
            # Check if login was successful (common indicators)
            success_indicators = [
                'dashboard', 'profile', 'logout', 'eighth', 'signup'
            ]
            
            if any(indicator in response.text.lower() for indicator in success_indicators):
                logger.info("Authentication successful")
                return True
            else:
                logger.error("Authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def parse_signup_page(self, url, content):
        """Parse a signup page for club information"""
        soup = BeautifulSoup(content, 'html.parser')
        clubs = []
        
        try:
            # Look for common patterns in signup pages
            club_elements = soup.find_all(['tr', 'div', 'li'], class_=re.compile(r'activity|club|signup', re.I))
            
            for element in club_elements:
                # Extract club name (various possible selectors)
                name_element = element.find(['a', 'span', 'strong', 'h3', 'h4'], string=re.compile(r'\w+'))
                if not name_element:
                    name_element = element.find(text=re.compile(r'[A-Za-z]{3,}'))
                
                if name_element:
                    club_name = name_element.get_text().strip() if hasattr(name_element, 'get_text') else str(name_element).strip()
                    
                    # Look for capacity/availability indicators
                    capacity_text = element.get_text()
                    
                    # Common patterns for availability
                    is_available = True
                    unavailable_patterns = [
                        r'full', r'closed', r'0/\d+', r'(\d+)/\1',  # Full or at capacity
                        r'no\s+space', r'waitlist', r'cancelled'
                    ]
                    
                    for pattern in unavailable_patterns:
                        if re.search(pattern, capacity_text, re.I):
                            is_available = False
                            break
                    
                    # Look for signup links
                    signup_link = element.find('a', href=re.compile(r'signup|register', re.I))
                    signup_url = signup_link['href'] if signup_link else url
                    
                    clubs.append({
                        'name': club_name,
                        'available': is_available,
                        'signup_url': signup_url,
                        'capacity_text': capacity_text
                    })
            
            # If no clubs found, try alternative parsing
            if not clubs:
                # Look for any text that might be club names
                text_content = soup.get_text()
                potential_clubs = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+Club)?)', text_content)
                for club_name in potential_clubs[:10]:  # Limit to first 10 matches
                    if len(club_name) > 5:  # Filter out short matches
                        clubs.append({
                            'name': club_name,
                            'available': True,  # Assume available if we can't determine
                            'signup_url': url,
                            'capacity_text': 'Unknown capacity'
                        })
        
        except Exception as e:
            logger.error(f"Error parsing page {url}: {e}")
        
        return clubs
    
    def check_favorites_availability(self, clubs):
        """Check if any favorite clubs are available"""
        available_favorites = []
        
        for club in clubs:
            if club['available']:
                # Fuzzy matching for favorites
                for favorite in self.favorites:
                    if (favorite.lower() in club['name'].lower() or 
                        club['name'].lower() in favorite.lower()):
                        available_favorites.append({
                            'name': club['name'],
                            'signup_url': club['signup_url'],
                            'capacity_text': club['capacity_text']
                        })
                        break
        
        return available_favorites
    
    def send_sms_notification(self, message):
        """Send SMS notification via email gateway"""
        if not self.notification_email or not self.target_sms:
            logger.warning("SMS notification not configured")
            return False
            
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.notification_email
            msg['To'] = self.target_sms
            msg['Subject'] = "8th Period Alert"
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.notification_email, self.notification_password)
            
            # Send message
            server.send_message(msg)
            server.quit()
            
            logger.info("SMS notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def monitor_once(self):
        """Run one monitoring cycle"""
        if not self.authenticate():
            logger.error("Authentication failed, skipping monitoring cycle")
            return
        
        all_new_opportunities = []
        
        for i, url in enumerate(self.monitor_urls):
            try:
                logger.info(f"Checking URL {i+1}/{len(self.monitor_urls)}: {url}")
                
                # Fetch page
                response = self.session.get(url, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    continue
                
                # Parse clubs
                clubs = self.parse_signup_page(url, response.content)
                logger.info(f"Found {len(clubs)} clubs on page")
                
                # Check favorites
                available_favorites = self.check_favorites_availability(clubs)
                
                # Compare with previous state
                url_key = url.split('/')[-1]  # Use URL suffix as key
                previous_available = set(self.previous_state.get(url_key, []))
                current_available = set(club['name'] for club in available_favorites)
                
                # Find new opportunities
                new_opportunities = current_available - previous_available
                if new_opportunities:
                    for club in available_favorites:
                        if club['name'] in new_opportunities:
                            all_new_opportunities.append({
                                'url': url,
                                'club': club
                            })
                
                # Update state
                self.previous_state[url_key] = list(current_available)
                
                # Rate limiting
                if i < len(self.monitor_urls) - 1:
                    time.sleep(self.rate_limit_delay)
                    
            except Exception as e:
                logger.error(f"Error checking {url}: {e}")
        
        # Send notifications for new opportunities
        if all_new_opportunities:
            self.send_opportunity_notifications(all_new_opportunities)
    
    def send_opportunity_notifications(self, opportunities):
        """Send notifications for new opportunities"""
        message_parts = ["New 8th Period Spots Available!"]
        
        for opp in opportunities:
            club = opp['club']
            signup_url = club['signup_url']
            if not signup_url.startswith('http'):
                signup_url = f"https://ion.tjhsst.edu{signup_url}"
                
            message_parts.append(f"\n- {club['name']}")
            message_parts.append(f"  Link: {signup_url}")
            message_parts.append(f"  Status: {club['capacity_text']}")
        
        message = '\n'.join(message_parts)
        logger.info(f"Sending notification for {len(opportunities)} new opportunities")
        
        self.send_sms_notification(message)
    
    def run_continuous(self):
        """Run continuous monitoring"""
        logger.info("Starting continuous monitoring...")
        
        while True:
            try:
                self.monitor_once()
                logger.info("Monitoring cycle completed, waiting for next cycle...")
                time.sleep(600)  # 10 minutes between checks
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def main():
    monitor = WebpageMonitor()
    monitor.run_continuous()

if __name__ == "__main__":
    main()