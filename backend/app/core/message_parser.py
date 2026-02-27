#!/usr/bin/env python3
"""
Message Parser - Detects special content like code blocks that should be
sent as separate messages to Telegram.
"""

import re
from typing import Dict, Any, List, Tuple, Optional

class MessageParser:
    """Parse and extract special content from messages"""
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
        """
        Extract code blocks from text
        
        Args:
            text: Message text
            
        Returns:
            List of tuples (language, code)
        """
        # Find code blocks with syntax highlighting
        pattern = r'```(\w*)\n([\s\S]*?)```'
        matches = re.findall(pattern, text)
        
        # Find basic code blocks
        if not matches:
            basic_pattern = r'```([\s\S]*?)```'
            basic_matches = re.findall(basic_pattern, text)
            matches = [('', m) for m in basic_matches]
            
        return matches
    
    @staticmethod
    def should_send_separately(text: str) -> bool:
        """
        Determine if text should be sent as a separate message
        
        Args:
            text: Message text
            
        Returns:
            True if should be sent separately
        """
        # Contains code blocks
        if '```' in text:
            return True
            
        # Contains explicit sending instructions
        send_phrases = [
            "sending to telegram",
            "sent to telegram",
            "sending to your telegram",
            "sent to your telegram",
            "sending it to telegram",
            "sent it to telegram",
            "i've sent",
            "i have sent",
            "i'll send",
            "i will send"
        ]
        
        lower_text = text.lower()
        return any(phrase in lower_text for phrase in send_phrases)
    
    @staticmethod
    def prepare_code_message(code_blocks: List[Tuple[str, str]]) -> str:
        """
        Prepare a nicely formatted code message for Telegram
        
        Args:
            code_blocks: List of (language, code) tuples
            
        Returns:
            Formatted message
        """
        if not code_blocks:
            return ""
            
        message = "📝 **Here's the code you requested:**\n\n"
        
        for i, (lang, code) in enumerate(code_blocks):
            if i > 0:
                message += "\n\n"
                
            if lang:
                message += f"```{lang}\n{code.strip()}\n```"
            else:
                message += f"```\n{code.strip()}\n```"
                
        return message
    
    @staticmethod
    def extract_sending_context(text: str) -> Optional[str]:
        """
        Extract what's being sent based on context
        
        Args:
            text: Message text
            
        Returns:
            Description of what's being sent or None
        """
        # Find sentences containing sent/sending phrases
        send_patterns = [
            r'I(?:\'ve| have) sent (.*?) to (?:your )?[Tt]elegram',
            r'I(?:\'ll| will) send (.*?) to (?:your )?[Tt]elegram',
            r'[Ss]ending (.*?) to (?:your )?[Tt]elegram',
        ]
        
        for pattern in send_patterns:
            matches = re.search(pattern, text)
            if matches:
                return matches.group(1)
                
        return None