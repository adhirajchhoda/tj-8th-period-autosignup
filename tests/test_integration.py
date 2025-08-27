#!/usr/bin/env python3
"""
Comprehensive integration tests for the auto-signup system
This is a BRUTAL HONEST assessment of what actually works vs theory
"""
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config import Config
from notifications.sms_notifier import SMSNotifier
from auth.ion_auth import IonAuthenticator
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemAnalyzer:
    """Brutal honest system analyzer"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []
    
    def add_issue(self, issue):
        """Add a critical issue"""
        self.issues.append(issue)
        logger.error(f"CRITICAL: {issue}")
    
    def add_warning(self, warning):
        """Add a warning"""
        self.warnings.append(warning)
        logger.warning(f"WARNING: {warning}")
    
    def add_success(self, success):
        """Add a success"""
        self.successes.append(success)
        logger.info(f"SUCCESS: {success}")
    
    def test_configuration(self):
        """Test configuration loading and validation"""
        logger.info("=== Testing Configuration ===")
        
        try:
            config = Config()
            
            # Test basic loading
            if config.username and config.password:
                self.add_success("Configuration loads credentials")
            else:
                self.add_issue("No credentials configured - system will fail")
            
            if config.favorites:
                self.add_success(f"Found {len(config.favorites)} favorites")
            else:
                self.add_issue("No favorites configured - nothing to monitor")
            
            if config.notification_email and config.target_sms:
                self.add_success("SMS notification configured")
            else:
                self.add_warning("SMS notification not configured - you won't get alerts")
            
            # Test URL generation
            if len(config.monitor_urls) > 0:
                self.add_success(f"Generated {len(config.monitor_urls)} URLs to monitor")
            else:
                self.add_issue("No URLs to monitor - system pointless")
                
            return config
            
        except Exception as e:
            self.add_issue(f"Configuration loading failed: {e}")
            return None
    
    def test_sms_notification(self, config):
        """Test SMS notification system"""
        logger.info("=== Testing SMS Notifications ===")
        
        if not config or not config.notification_email:
            self.add_warning("Skipping SMS test - no configuration")
            return
        
        try:
            notifier = SMSNotifier(
                config.notification_email,
                config.notification_password, 
                config.target_sms
            )
            
            # This would actually send an SMS - be careful!
            # success = notifier.send_sms("Test from auto-signup system")
            # For now, just test object creation
            self.add_success("SMS notifier created successfully")
            
            # Test message formatting
            test_message = notifier.send_signup_success("Test Club", "https://test.com")
            # This doesn't actually send, just formats
            
        except Exception as e:
            self.add_issue(f"SMS notification system broken: {e}")
    
    def test_authentication_theory(self, config):
        """Test authentication in theory (without actually doing it)"""
        logger.info("=== Testing Authentication (Theory) ===")
        
        if not config:
            return
        
        # Test authenticator creation
        try:
            auth = IonAuthenticator(config)
            self.add_success("Authentication module created")
        except Exception as e:
            self.add_issue(f"Cannot create authenticator: {e}")
            return
        
        # Check for session file handling
        if hasattr(auth, 'session_file'):
            self.add_success("Session persistence configured")
        else:
            self.add_warning("No session persistence - will re-login every time")
        
        # Major authentication concerns
        self.add_issue("2FA KILLER: If Ion account has 2FA enabled, automation will FAIL")
        self.add_issue("SESSION PERSISTENCE: GitHub Actions won't persist session files between runs")
        self.add_warning("Rate limiting: Too many login attempts may lock account")
        self.add_warning("Bot detection: Ion may detect automated browser patterns")
    
    def test_playwright_availability(self):
        """Test if Playwright actually works"""
        logger.info("=== Testing Playwright ===")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Test basic navigation
                page.goto("https://example.com", timeout=10000)
                
                if "Example Domain" in page.content():
                    self.add_success("Playwright can navigate and load pages")
                else:
                    self.add_warning("Playwright navigation seems broken")
                
                browser.close()
                
        except Exception as e:
            self.add_issue(f"Playwright completely broken: {e}")
    
    def test_github_actions_reality(self):
        """Test GitHub Actions limitations"""
        logger.info("=== Testing GitHub Actions Reality ===")
        
        # These are known limitations
        self.add_issue("STORAGE: Session files won't persist between workflow runs")
        self.add_issue("2FA: Cannot handle 2FA in headless GitHub Actions environment")
        self.add_warning("NETWORK: GitHub Actions IPs might be blocked by Ion")
        self.add_warning("TIMING: Cron jobs in GitHub Actions can be delayed during high load")
        self.add_warning("TIMEOUT: 45-minute timeout might not be enough for all URLs")
        
        # Check if we're running in GitHub Actions
        if os.getenv('GITHUB_ACTIONS'):
            self.add_warning("Currently running in GitHub Actions - session issues likely")
        else:
            self.add_success("Running locally - better chance of working")
    
    def test_signup_flow_theory(self):
        """Analyze the signup flow logic"""
        logger.info("=== Analyzing Signup Flow ===")
        
        # Selector assumptions
        self.add_issue("HTML SELECTORS: Code assumes specific Ion HTML structure - will break if Ion updates UI")
        self.add_issue("RACE CONDITIONS: Multiple students signing up simultaneously will cause conflicts")
        self.add_warning("ELEMENT DETECTION: 'Sign up' button detection is fragile and assumption-heavy")
        
        # Club matching
        self.add_warning("FUZZY MATCHING: Club name matching might be too aggressive or miss variations")
        self.add_warning("AVAILABILITY DETECTION: Checking for 'full' text might miss other unavailability indicators")
        
        # Form submission
        self.add_issue("CSRF TOKENS: Ion likely requires CSRF tokens that aren't being handled properly")
        self.add_issue("JAVASCRIPT: Ion signup might require JavaScript execution that's not accounted for")
    
    def analyze_real_world_usage(self):
        """Analyze real-world usage scenarios"""
        logger.info("=== Real World Usage Analysis ===")
        
        # Practical limitations
        self.add_issue("POPULARITY: Popular clubs (Investment Club) fill up in SECONDS, faster than any automation")
        self.add_warning("TIMING: 10-minute intervals mean you'll miss most opportunities")
        self.add_warning("COMPETITION: Other students also trying to signup at the same time")
        
        # Ethical concerns
        self.add_warning("FAIRNESS: Automated signup gives unfair advantage over manual students")
        self.add_warning("POLICY: School might prohibit automated signups")
        self.add_issue("DETECTION: Repeated automated patterns might get account flagged")
    
    def run_full_analysis(self):
        """Run complete brutal honest analysis"""
        logger.info("Starting BRUTAL HONEST system analysis...")
        logger.info("This will identify what ACTUALLY works vs what's theoretical")
        
        config = self.test_configuration()
        self.test_sms_notification(config)
        self.test_authentication_theory(config)
        self.test_playwright_availability()
        self.test_github_actions_reality()
        self.test_signup_flow_theory()
        self.analyze_real_world_usage()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate final assessment report"""
        logger.info("\n" + "="*80)
        logger.info("BRUTAL HONEST ASSESSMENT REPORT")
        logger.info("="*80)
        
        logger.info(f"\n✅ SUCCESSES ({len(self.successes)}):")
        for success in self.successes:
            logger.info(f"  + {success}")
        
        logger.info(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
        for warning in self.warnings:
            logger.info(f"  - {warning}")
        
        logger.info(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
        for issue in self.issues:
            logger.info(f"  ! {issue}")
        
        # Overall assessment
        critical_count = len(self.issues)
        warning_count = len(self.warnings)
        
        logger.info(f"\n🎯 FINAL VERDICT:")
        if critical_count == 0:
            logger.info("  LIKELY TO WORK: No critical issues found")
        elif critical_count <= 3:
            logger.info("  MIGHT WORK: Some critical issues, but potentially solvable")
        else:
            logger.info("  UNLIKELY TO WORK: Too many critical issues for reliable operation")
        
        logger.info(f"\n📊 REALITY CHECK:")
        logger.info(f"  Success Rate Estimate: {max(0, 80 - (critical_count * 15) - (warning_count * 5))}%")
        logger.info(f"  Will work in GitHub Actions: {'PROBABLY NOT' if critical_count > 2 else 'MAYBE'}")
        logger.info(f"  Will work locally: {'POSSIBLY' if critical_count < 5 else 'UNLIKELY'}")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        if 'Session files' in str(self.issues):
            logger.info("  - Consider using a VPS instead of GitHub Actions")
        if '2FA' in str(self.issues):
            logger.info("  - Disable 2FA on Ion account (if possible)")
        if 'HTML SELECTORS' in str(self.issues):
            logger.info("  - Test thoroughly on actual Ion pages before deploying")
        logger.info("  - Start with notification-only mode before enabling auto-signup")
        logger.info("  - Have a backup manual signup strategy")

def main():
    """Main test runner"""
    analyzer = SystemAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()