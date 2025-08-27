# Codebase Structure

This document explains the organized structure of the TJ 8th Period Auto-Signup System.

## Directory Structure

```
/
├── src/                          # Core application code
│   ├── monitors/                 # Monitoring implementations
│   │   ├── base_monitor.py       # Abstract base monitor class
│   │   ├── http_monitor.py       # HTTP-based monitoring (legacy)
│   │   └── playwright_monitor.py # Playwright-based monitoring (current)
│   ├── auth/
│   │   └── ion_auth.py           # Ion authentication & session management
│   ├── notifications/
│   │   └── sms_notifier.py       # SMS notification system
│   └── utils/
│       ├── config.py             # Configuration management
│       └── club_matcher.py       # Club name matching & availability detection
├── tests/                        # Test files
│   ├── test_setup.py             # Basic setup validation
│   └── test_integration.py       # Comprehensive system analysis
├── scripts/                      # Executable scripts
│   ├── run_monitor.py            # Main entry point
│   └── setup_local.py            # Local development setup
├── docs/                         # Documentation
│   ├── README.md                 # Auto-signup guide
│   ├── SETUP.md                  # Setup checklist
│   └── CODEBASE.md               # This file
├── config/                       # Configuration templates
│   └── config.template           # GitHub Secrets template
├── .github/workflows/            # GitHub Actions
│   └── monitor.yml               # Automated monitoring workflow
└── requirements.txt              # Python dependencies
```

## Core Components

### 1. Monitoring System (`src/monitors/`)

**BaseMonitor** (`base_monitor.py`)
- Abstract base class for all monitors
- Defines common interface and shared functionality
- Handles continuous monitoring loop and error recovery

**PlaywrightMonitor** (`playwright_monitor.py`) 
- Current implementation using Playwright browser automation
- Real browser interaction for reliable signup functionality
- Handles JavaScript-heavy pages and dynamic content

**HTTPMonitor** (`http_monitor.py`)
- Legacy HTTP-based monitoring (notification only)
- Kept for fallback/comparison purposes
- Less reliable but faster than browser automation

### 2. Authentication (`src/auth/`)

**IonAuthenticator** (`ion_auth.py`)
- Handles Ion login flow with session persistence
- Manages CSRF tokens and form submission
- Detects and handles session expiration
- **Critical Limitation**: Cannot handle 2FA automatically

### 3. Notifications (`src/notifications/`)

**SMSNotifier** (`sms_notifier.py`)
- Sends SMS via email-to-SMS gateways (free)
- Supports multiple message types (success, error, availability)
- Uses Gmail SMTP with app passwords for security

### 4. Utilities (`src/utils/`)

**Config** (`config.py`)
- Loads configuration from environment variables
- Validates required settings
- Provides centralized configuration management

**ClubMatcher** (`club_matcher.py`)
- Fuzzy matching for club names (handles variations)
- Detects availability based on text patterns
- Prioritizes clubs based on favorites order
- Finds signup buttons/links within activities

## Entry Points

### Production Entry Point
```bash
python scripts/run_monitor.py
```

### Local Development/Testing
```bash
python scripts/setup_local.py
```

### Integration Testing
```bash
python tests/test_integration.py
```

## Configuration Flow

1. **Environment Variables** → `Config` class loads settings
2. **Config** → Passed to all components that need it
3. **Secrets Management** → GitHub Secrets for production, local env for development

## Data Flow

```
GitHub Actions Trigger (every 10 minutes)
    ↓
scripts/run_monitor.py
    ↓
Config loads environment variables
    ↓
SMSNotifier configured for alerts
    ↓
PlaywrightMonitor starts browser
    ↓
IonAuthenticator handles login
    ↓
Monitor loops through signup URLs
    ↓
ClubMatcher finds available favorites
    ↓
Auto-signup attempts (if enabled)
    ↓
SMSNotifier sends results
    ↓
Browser cleanup and exit
```

## Key Design Decisions

### Modular Architecture
- **Separation of Concerns**: Each component has a single responsibility
- **Testability**: Components can be tested in isolation
- **Maintainability**: Easy to update or replace individual components

### Abstract Base Classes
- **BaseMonitor**: Allows easy switching between HTTP and Playwright implementations
- **Future-proofing**: Can add new monitoring strategies without changing main code

### Configuration Management
- **Single Source of Truth**: All settings in one Config class
- **Environment-based**: Different configs for local vs production
- **Validation**: Catches missing configuration early

### Error Handling Strategy
- **Graceful Degradation**: System continues even if individual pages fail
- **Comprehensive Logging**: Detailed logs for debugging
- **Retry Logic**: Automatic retry with exponential backoff

## Testing Strategy

### Unit Tests (Missing - TODO)
- Test individual components in isolation
- Mock external dependencies
- Validate configuration handling

### Integration Tests (`test_integration.py`)
- **Brutal Honest Assessment**: Tests what actually works vs theory
- Identifies critical issues before deployment
- Validates end-to-end flow

### Local Testing (`setup_local.py`)
- Interactive testing with real browser
- Manual verification of authentication flow
- Page structure analysis and debugging

## Known Limitations

### Critical Issues
1. **2FA Incompatibility**: Cannot handle 2FA in automated environment
2. **Session Persistence**: GitHub Actions doesn't persist files between runs
3. **HTML Structure Assumptions**: Breaks if Ion changes their UI
4. **Race Conditions**: Multiple students signing up simultaneously

### Warnings
1. **Rate Limiting**: Ion may block frequent automated requests
2. **Bot Detection**: Automated patterns might be flagged
3. **Network Restrictions**: GitHub Actions IPs might be blocked
4. **Timing Issues**: Popular clubs fill faster than automation can respond

## Future Improvements

### High Priority
1. **Better Error Handling**: More specific error recovery strategies
2. **UI Change Detection**: Alert when Ion HTML structure changes
3. **Session Management**: Better handling of authentication state
4. **Rate Limit Adaptation**: Dynamic delays based on server response times

### Medium Priority
1. **Multiple User Support**: Handle multiple accounts safely
2. **Advanced Scheduling**: More flexible monitoring schedules
3. **Conflict Resolution**: Better handling of simultaneous signup attempts
4. **Performance Monitoring**: Track success rates and failure patterns

### Low Priority
1. **Web UI**: Browser-based configuration and monitoring
2. **Advanced Notifications**: Discord, Slack, email options
3. **Analytics**: Historical success rate tracking
4. **Mobile App**: Native mobile notifications

## Development Workflow

### Adding New Features
1. Update relevant component in `src/`
2. Add tests to `tests/`
3. Update configuration if needed
4. Test locally with `setup_local.py`
5. Deploy via GitHub Actions

### Debugging Issues
1. Check GitHub Actions logs
2. Run `test_integration.py` for system analysis
3. Use `setup_local.py` for interactive debugging
4. Check Ion website for UI changes

### Modifying Configuration
1. Update `config/config.template`
2. Update GitHub Secrets if needed
3. Update `Config` class validation
4. Test with new settings