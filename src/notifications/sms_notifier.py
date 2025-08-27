"""SMS notification system using email-to-SMS gateways"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

class SMSNotifier:
    """Handles SMS notifications via email gateways"""
    
    def __init__(self, email, password, target_sms):
        self.email = email
        self.password = password
        self.target_sms = target_sms
    
    def send_sms(self, message):
        """Send SMS notification via email gateway"""
        if not self.email or not self.target_sms:
            logger.warning("SMS notification not configured")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.target_sms
            msg['Subject'] = "8th Period Alert"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info("SMS notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def send_signup_success(self, club_name, url):
        """Send success notification for signup"""
        message = f"AUTO-SIGNUP SUCCESS!\n\n{club_name}\nPage: {url}\nTime: {datetime.now().strftime('%H:%M:%S')}"
        return self.send_sms(message)
    
    def send_favorites_available(self, matches):
        """Send notification when favorites are available but auto-signup is disabled"""
        message_parts = ["Available favorites found (auto-signup disabled):"]
        for match in matches[:5]:  # Limit to top 5
            message_parts.append(f"- {match['name']}")
        
        return self.send_sms('\n'.join(message_parts))
    
    def send_error_notification(self, error_message):
        """Send error notification"""
        message = f"8th Period Monitor Error:\n{error_message}"
        return self.send_sms(message)