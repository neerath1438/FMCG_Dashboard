"""
Simple Authentication Module for Demo Purposes
No password hashing, no JWT - just basic validation for client demo
"""

import uuid
from datetime import datetime
from typing import Optional, Dict

# Demo user credentials (hardcoded for client demo)
DEMO_USER = {
    "email": "rosini.alexander@metora.co",
    "password": "Roshini@123",  # Plain text for demo only
    "name": "Rosini Alexander",
    "company": "Metora"
}

# In-memory session storage (will reset on server restart)
# For demo purposes only - not for production
active_sessions: Dict[str, dict] = {}


def validate_credentials(email: str, password: str) -> bool:
    """
    Validate user credentials against hardcoded demo user
    
    Args:
        email: User email
        password: User password (plain text)
    
    Returns:
        True if credentials match, False otherwise
    """
    return (
        email == DEMO_USER["email"] and 
        password == DEMO_USER["password"]
    )


def create_session(email: str) -> str:
    """
    Create a new session for the user
    
    Args:
        email: User email
    
    Returns:
        Session token (UUID)
    """
    session_token = str(uuid.uuid4())
    active_sessions[session_token] = {
        "email": email,
        "name": DEMO_USER["name"],
        "company": DEMO_USER["company"],
        "created_at": datetime.now().isoformat()
    }
    return session_token


def verify_session(session_token: str) -> Optional[dict]:
    """
    Verify if a session token is valid
    
    Args:
        session_token: Session token to verify
    
    Returns:
        User info dict if valid, None otherwise
    """
    return active_sessions.get(session_token)


def destroy_session(session_token: str) -> bool:
    """
    Destroy a session (logout)
    
    Args:
        session_token: Session token to destroy
    
    Returns:
        True if session was destroyed, False if not found
    """
    if session_token in active_sessions:
        del active_sessions[session_token]
        return True
    return False


def get_user_info(email: str) -> dict:
    """
    Get user information
    
    Args:
        email: User email
    
    Returns:
        User info dict
    """
    return {
        "email": DEMO_USER["email"],
        "name": DEMO_USER["name"],
        "company": DEMO_USER["company"]
    }
