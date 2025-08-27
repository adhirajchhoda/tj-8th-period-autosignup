"""Club name matching and availability detection utilities"""
import re
import logging

logger = logging.getLogger(__name__)

class ClubMatcher:
    """Handles club name matching and availability detection"""
    
    def __init__(self, favorites):
        self.favorites = favorites
        self.unavailable_patterns = [
            r'full', r'closed', r'0/\d+', r'(\d+)/\1', r'waitlist', 
            r'cancelled', r'no\s+space', r'disabled'
        ]
    
    def extract_club_name(self, text):
        """Extract club name from activity text"""
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
        combined_text = f"{text} {html}".lower()
        
        for pattern in self.unavailable_patterns:
            if re.search(pattern, combined_text, re.I):
                return False
        
        return True
    
    def find_matches(self, page_content):
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
                signup_element = self._find_signup_element(activity)
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
    
    def _find_signup_element(self, activity_element):
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