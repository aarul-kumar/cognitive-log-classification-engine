import re

def classify_with_regex(log_message):
    """Classify logs using regex patterns for specific, well-defined patterns"""
    regex_patterns = {
        # Security patterns
        r"(?i)(blocked|denied|attack|malicious|threat|suspicious|unauthorized|invalid credentials|login failed|access denied)": "Security Alert",
        r"(?i)(admin|privilege|escalation|unauthorized access)": "Security Alert",
        r"(?i)(IP.*blocked|block.*attack)": "Security Alert",
        
        # HTTP patterns
        r"(?i)(HTTP|GET|POST|PUT|DELETE|PATCH|RCODE|status code)": "HTTP Status",
        r"(?i)(\s(200|201|204|301|302|304|400|401|403|404|500|502|503)\s)": "HTTP Status",
        
        # System notification patterns
        r"(?i)(backup|restore|completed successfully|finished|shutdown|reboot|restart)": "System Notification",
        r"(?i)(uploaded|downloaded|sync|synchronized)": "System Notification",
        r"(?i)(disk.*cleanup|maintenance|update.*version)": "System Notification",
        
        # User action patterns
        r"(?i)(user.*logged (in|out)|login|logout)": "User Action",
        r"(?i)(account.*created|user.*created|registration)": "User Action",
    }
    
    for pattern, label in regex_patterns.items():
        if re.search(pattern, log_message):
            print(f"[REGEX] Matched pattern for: {label}")
            return label
    
    print(f"[REGEX] No pattern matched")
    return None

if __name__ == "__main__":
    print(classify_with_regex("User User123 logged in."))
    print(classify_with_regex("Backup started at 2024-06-01 10:00:00."))
    print(classify_with_regex("System updated to version 2.1.0."))
    print(classify_with_regex("Random log message without match."))
    print(classify_with_regex("Account with ID 456 created by admin."))
