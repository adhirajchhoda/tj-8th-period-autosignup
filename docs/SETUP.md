# Secure Deployment Checklist

Follow this checklist to deploy your 8th Period Monitor safely and securely.

## Pre-Deployment Setup

### 1. GitHub Repository Setup
- [ ] Fork this repository to your GitHub account
- [ ] Ensure repository is set to **PUBLIC** (required for unlimited Actions)
- [ ] Verify all files are present: `monitor.py`, `requirements.txt`, `.github/workflows/monitor.yml`

### 2. Gmail Configuration (for SMS)
- [ ] Create or use existing Gmail account
- [ ] Enable 2-Factor Authentication
- [ ] Generate App Password:
  - [ ] Go to Gmail → Account → Security → 2-Step Verification
  - [ ] Click "App passwords"
  - [ ] Select "Mail" → Generate
  - [ ] Save the 16-character password (format: `xxxx xxxx xxxx xxxx`)

### 3. Determine Your SMS Gateway
Find your carrier and format your phone number correctly:

- [ ] **Verizon**: `YOURNUMBER@vtext.com`
- [ ] **AT&T**: `YOURNUMBER@txt.att.net`
- [ ] **T-Mobile**: `YOURNUMBER@tmomail.net`
- [ ] **Sprint**: `YOURNUMBER@messaging.sprintpcs.com`

Example: If your number is 571-223-7914 and you have Verizon, use: `5712237914@vtext.com`

## Secrets Configuration

Go to your repository → Settings → Secrets and variables → Actions

Add ALL these secrets (copy names exactly):

### Authentication Secrets
- [ ] `LOGIN_URL` = `https://ion.tjhsst.edu/login`
- [ ] `USERNAME` = Your ion username
- [ ] `PASSWORD` = Your ion password

### Monitoring Configuration
- [ ] `URL_BASE` = `https://ion.tjhsst.edu/eighth/signup/`
- [ ] `URL_START` = `4555`
- [ ] `URL_END` = `4583`
- [ ] `FAVORITES` = Your favorite clubs (comma-separated)
  - Example: `Investment Club,Rocketry Club,Computer Vision Club`

### Notification Configuration
- [ ] `NOTIFICATION_EMAIL` = Your Gmail address
- [ ] `NOTIFICATION_PASSWORD` = Your Gmail app password (16 characters)
- [ ] `TARGET_SMS` = Your phone with carrier gateway
  - Format: `5712237914@vtext.com` (replace with your info)

### Optional Configuration
- [ ] `RATE_LIMIT_DELAY` = `15` (seconds between requests)

## Testing Phase

### 1. Manual Test Run
- [ ] Go to Actions tab in your repository
- [ ] Click "8th Period Monitor" workflow
- [ ] Click "Run workflow" → "Run workflow"
- [ ] Wait for workflow to complete (should take 2-5 minutes)

### 2. Check Results
- [ ] Workflow shows green checkmark (success)
- [ ] No red X marks (errors)
- [ ] Click on the workflow run to view logs
- [ ] Look for "Authentication successful" in logs
- [ ] Look for "Found X clubs on page" messages

### 3. SMS Test
If the test finds available spots in your favorites:
- [ ] You should receive an SMS within 1-2 minutes
- [ ] SMS should contain club names and signup links
- [ ] Links should work when clicked

## Production Deployment

### 1. Enable Scheduled Monitoring
- [ ] Workflow will automatically run every 10 minutes
- [ ] No additional setup needed - it starts immediately
- [ ] Check Actions tab to see scheduled runs appearing

### 2. Monitor System Health
- [ ] Check Actions tab daily for any failed runs
- [ ] Green checkmarks = working properly
- [ ] Red X marks = investigate errors in logs

## Security Verification

### Double-check Security Settings
- [ ] Repository is public (allows unlimited Actions)
- [ ] All sensitive data is in Secrets (not visible in code)
- [ ] Secrets contain no typos or extra spaces
- [ ] Phone number is properly hidden in TARGET_SMS secret

### Test Security
- [ ] View your repository's code - confirm no sensitive info visible
- [ ] Check workflow logs - confirm credentials are not logged
- [ ] Verify only you can access your repository's Settings → Secrets

## Final Checklist

- [ ] System is running automatically every 10 minutes
- [ ] You receive SMS notifications for available favorite clubs
- [ ] All workflows are passing (green checkmarks)
- [ ] No sensitive information is visible in public repository
- [ ] SMS notifications include working signup links

## Ready to Deploy!

Once all items are checked, your system is:
- **Secure** - No credentials exposed
- **Automated** - Runs 24/7 without your computer
- **Free** - Uses only free services
- **Private** - Only you receive notifications

Your 8th Period Monitor is now live and will alert you whenever your favorite clubs have open spots!

---

## Troubleshooting

**No SMS received?**
- Verify TARGET_SMS format is correct for your carrier
- Check Gmail app password is properly set
- Try sending a test email to your TARGET_SMS address manually

**Authentication errors?**
- Double-check USERNAME and PASSWORD secrets
- Try logging into ion.tjhsst.edu manually to verify credentials
- Check if your account has been temporarily restricted

**Workflow failures?**
- Click on the failed workflow to see error logs
- Common issues: typos in secrets, network timeouts, site changes
- Try running manually first to isolate issues