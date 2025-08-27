# TJ 8th Period Auto-Signup System

**TRUE AUTO-SIGNUP**: This system doesn't just notify you - it automatically signs you up for your favorite clubs when spots become available.

## How It Works

1. **Monitors** all signup pages (4555-4583) every 10 minutes
2. **Detects** when your favorite clubs have open spots  
3. **Automatically signs up** for the highest priority available club
4. **Sends SMS confirmation** when signup is successful
5. **Continues monitoring** for other periods/dates

## Quick Start

### 1. Configure GitHub Secrets

Go to: Settings → Secrets and variables → Actions

**Required Secrets:**
```
LOGIN_URL = https://ion.tjhsst.edu/login
USERNAME = 2027achhoda  
PASSWORD = [your password]
FAVORITES = Investment Club,Future Business Leaders of American,FBLA,Launch X
AUTO_SIGNUP = true
```

**SMS Notifications:**
```
NOTIFICATION_EMAIL = [your Gmail]
NOTIFICATION_PASSWORD = [Gmail app password] 
TARGET_SMS = [your number]@vtext.com
```

### 2. Priority System

**Order matters in FAVORITES!** The system signs up for the FIRST available club in your list.

Example: `Investment Club,FBLA,Launch X`
- If both Investment Club and FBLA are available → signs up for Investment Club
- If only FBLA is available → signs up for FBLA  
- If only Launch X is available → signs up for Launch X

### 3. Test the System

1. Go to Actions tab → "8th Period Auto-Signup"
2. Click "Run workflow" to test manually
3. Check logs to see if it's working
4. You'll get SMS when successful signup occurs

## System Features

### Real Browser Automation
- Uses Playwright (not just HTTP requests)
- Handles JavaScript-heavy pages
- Properly submits forms and clicks buttons
- Manages Ion session authentication

### Smart Club Matching
- Fuzzy matching for club names
- Handles variations like "FBLA" vs "Future Business Leaders of America"
- Prioritizes based on your favorites order

### Robust Error Handling
- Session expiry → automatic re-authentication
- Page timeouts → retry with backoff
- Signup failures → detailed error reporting
- Rate limiting → respectful delays

### Security & Privacy
- All credentials encrypted in GitHub Secrets
- No sensitive data in logs or code
- Session management for reliable authentication
- Rate-limited to respect school servers

## Notification Examples

**Successful Auto-Signup:**
```
AUTO-SIGNUP SUCCESS!

Investment Club
Page: https://ion.tjhsst.edu/eighth/signup/4558
Time: 14:23:15

Successfully signed up for Investment Club
```

**Multiple Favorites Available (notification mode):**
```
Available favorites found (auto-signup disabled):
- Investment Club  
- FBLA
- Launch X
```

## Configuration Options

### Basic Settings
- `AUTO_SIGNUP=true` → Automatic signup enabled
- `AUTO_SIGNUP=false` → Notification only (no signup)
- `RATE_LIMIT_DELAY=15` → Seconds between requests

### Advanced Club Matching
Your favorites can include multiple variations:
```
FAVORITES=Investment Club,Future Business Leaders of American,FBLA,Future Business Leaders,Launch X,LaunchX
```

This catches variations like:
- "Investment Club" 
- "Investment Club - Interest Meeting"
- "FBLA - Future Business Leaders of America"
- "Launch X - Entrepreneurship"

## Monitoring & Debugging

### View Logs
1. Actions tab → Latest workflow run
2. Click "autosignup" job  
3. Expand "Run auto-signup monitor"
4. View detailed logs

### Common Log Messages
- `Authentication successful` → Login working
- `Found X matching activities` → Favorites detected
- `SUCCESS: Signed up for [Club]` → Auto-signup worked
- `FAILED: [Club] - [reason]` → Signup attempt failed
- `Session expired, re-authenticating` → Handled automatically

### Test Locally (Optional)
```bash
# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# Run local tests  
python test_local.py
```

## Safety Features

### Anti-Spam Protection
- Maximum one signup attempt per club per cycle
- Tracks successful signups to avoid duplicates
- Respectful rate limiting (15+ second delays)

### Conflict Resolution  
- Only signs up for ONE activity per monitoring cycle
- Prioritizes based on favorites order
- Stops monitoring after successful signup (for that cycle)

### Error Recovery
- Automatic session refresh on authentication failure
- Exponential backoff on repeated failures
- Comprehensive error logging for debugging

## Troubleshooting

### Not Getting Notifications?
1. Check Gmail app password is correct
2. Verify SMS gateway format: `5712237914@vtext.com`
3. Test SMS with different carrier gateways
4. Check workflow logs for SMS errors

### Auto-Signup Not Working?
1. Verify `AUTO_SIGNUP=true` in secrets
2. Check authentication logs for login failures  
3. Look for "SUCCESS:" or "FAILED:" messages in logs
4. Ensure favorites are spelled correctly

### Session/Login Issues?
1. Check username and password in secrets
2. Look for "Authentication failed" in logs
3. 2FA may need manual completion (rare in automation)
4. Ion may have temporary access restrictions

### High Failure Rate?
1. Popular clubs fill up very quickly
2. Try less popular backup clubs in favorites
3. Check if signup periods are actually open
4. Verify you're not already signed up

## Advanced Configuration

### Custom Monitoring Schedule
Edit `.github/workflows/monitor.yml`:
```yaml
schedule:
  - cron: '*/5 * * * *'  # Every 5 minutes
  - cron: '*/15 * * * *' # Every 15 minutes  
```

### Multiple Favorites Lists
For different priorities on different days, create multiple workflows with different favorites configurations.

### Integration with Other Tools
The system can be extended to:
- Send Discord notifications
- Update calendars automatically  
- Log signup history
- Coordinate with other students

## System Architecture

```
GitHub Actions (every 10 minutes)
    ↓
Playwright Browser Automation
    ↓
Ion Authentication & Session Management
    ↓
Page Monitoring (4555-4583)
    ↓
Club Detection & Matching
    ↓
Automatic Signup Execution
    ↓
SMS Notification & Logging
```

## Legal & Ethical Use

- **Personal Use Only**: Don't share access with others
- **Respectful Automation**: Built-in rate limiting and delays
- **School Policy Compliance**: Ensure automated signups are allowed  
- **Fair Access**: Doesn't monopolize signup opportunities

## Support

### Check These First:
1. Review workflow logs in Actions tab
2. Verify all secrets are configured correctly  
3. Test SMS notifications work
4. Confirm favorites spelling matches Ion exactly

### Common Solutions:
- **Login fails**: Update username/password secrets
- **No matches found**: Check favorites spelling
- **SMS not received**: Test different carrier gateways
- **Signup fails**: Club may have filled up between detection and signup

Your auto-signup system is now ready! It will monitor 24/7 and automatically sign you up for your favorite clubs when spots become available.