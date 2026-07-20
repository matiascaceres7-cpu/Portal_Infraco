# Email parser for ManageEngine format variables
import re
from typing import Dict


def parse_manage_engine_format(email_body: str) -> Dict[str, str]:
    """
    Parse ManageEngine format variables from email body.
    
    Extracts all occurrences of @@KEY=VALUE@@ pattern and returns
    a dictionary with lowercase keys and trimmed values.
    
    Args:
        email_body: The email body containing ManageEngine variables
        
    Returns:
        Dictionary with parsed variables (keys in lowercase, values trimmed)
    """
    pattern = r'@@(\w+)=([^@]*)@@'
    matches = re.findall(pattern, email_body)
    
    result = {}
    for key, value in matches:
        result[key.lower()] = value.strip()
    
    return result
