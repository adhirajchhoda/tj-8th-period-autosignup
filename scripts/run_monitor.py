#!/usr/bin/env python3
"""Main entry point for the 8th period auto-signup monitor"""
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config import Config
from notifications.sms_notifier import SMSNotifier
from monitors.playwright_monitor import PlaywrightMonitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    logger.info("Starting TJ 8th Period Auto-Signup Monitor")
    
    # Load configuration
    config = Config()
    
    # Validate configuration
    missing = config.validate()
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        sys.exit(1)
    
    # Create notifier
    notifier = SMSNotifier(
        config.notification_email,
        config.notification_password,
        config.target_sms
    )
    
    # Create and run monitor
    monitor = PlaywrightMonitor(config, notifier)
    
    try:
        monitor.run_continuous()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()