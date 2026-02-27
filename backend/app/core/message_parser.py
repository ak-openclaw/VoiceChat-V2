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
            "i will send",
            "code sent to telegram"
        ]
        
        lower_text = text.lower()
        return any(phrase in lower_text for phrase in send_phrases)
        
    @staticmethod
    def infer_programming_language(request: str) -> str:
        """
        Infer programming language from a request
        
        Args:
            request: User's request
            
        Returns:
            Inferred language
        """
        request = request.lower()
        
        # Check for explicit language mentions
        languages = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js"],
            "java": ["java"],
            "c++": ["c++", "cpp"],
            "c#": ["c#", "csharp"],
            "ruby": ["ruby"],
            "php": ["php"],
            "go": ["golang", "go"],
            "swift": ["swift"],
            "html": ["html"],
            "css": ["css"],
            "sql": ["sql"],
            "rust": ["rust"],
        }
        
        for lang, keywords in languages.items():
            for keyword in keywords:
                if keyword in request:
                    return lang
        
        # Default to Python if no language specified
        return "python"
        
    @staticmethod
    def generate_code_for_task(task: str, language: str = "python") -> str:
        """
        Generate code for a task when model claims to send code but doesn't
        
        Args:
            task: Description of the task
            language: Programming language
            
        Returns:
            Generated code
        """
        code = ""
        
        # Generate simple code based on task description
        if language == "python":
            if "add" in task.lower() and "number" in task.lower():
                code = """def add_numbers():
    try:
        # Get input from user
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))
        
        # Calculate sum
        sum_result = num1 + num2
        
        # Convert to integer if whole number
        if sum_result.is_integer():
            sum_result = int(sum_result)
        
        # Display result
        print(f"{num1} + {num2} = {sum_result}")
        return sum_result
    except ValueError:
        print("Error: Please enter valid numbers")
        return None

if __name__ == "__main__":
    add_numbers()
"""
            elif "calculator" in task.lower():
                code = """def calculator():
    try:
        # Get input from user
        num1 = float(input("Enter first number: "))
        operation = input("Enter operation (+, -, *, /): ")
        num2 = float(input("Enter second number: "))
        
        # Perform calculation based on operation
        if operation == "+":
            result = num1 + num2
        elif operation == "-":
            result = num1 - num2
        elif operation == "*":
            result = num1 * num2
        elif operation == "/":
            if num2 == 0:
                print("Error: Division by zero")
                return None
            result = num1 / num2
        else:
            print("Error: Invalid operation")
            return None
        
        # Convert to integer if whole number
        if result.is_integer():
            result = int(result)
        
        # Display result
        print(f"{num1} {operation} {num2} = {result}")
        return result
    except ValueError:
        print("Error: Please enter valid numbers")
        return None

if __name__ == "__main__":
    calculator()
"""
            else:
                # Generic Python function
                code = """# Simple program to demonstrate Python functions

def main():
    print("Hello, I'm a Python program!")
    
    # Get user input
    name = input("What's your name? ")
    
    # Greet the user
    print(f"Nice to meet you, {name}!")
    
    # Demonstrate some basic operations
    a = 10
    b = 5
    print(f"Doing some math: {a} + {b} = {a + b}")
    
    print("Program completed.")

if __name__ == "__main__":
    main()
"""
                
        elif language == "javascript":
            if "add" in task.lower() and "number" in task.lower():
                code = """function addNumbers() {
    try {
        // Get input from user (in a browser environment)
        const num1 = parseFloat(prompt("Enter first number:"));
        const num2 = parseFloat(prompt("Enter second number:"));
        
        if (isNaN(num1) || isNaN(num2)) {
            throw new Error("Invalid input");
        }
        
        // Calculate sum
        const sum = num1 + num2;
        
        // Display result
        console.log(`${num1} + ${num2} = ${sum}`);
        alert(`${num1} + ${num2} = ${sum}`);
        
        return sum;
    } catch (error) {
        console.error("Error:", error.message);
        alert("Please enter valid numbers");
    }
}

addNumbers();
"""
            else:
                # Generic JavaScript function
                code = """// Simple JavaScript program

function greetUser() {
    // Get user input in a browser environment
    const name = prompt("What's your name?");
    
    // Greet the user
    alert(`Hello, ${name}! Nice to meet you.`);
    
    // Demonstrate some basic operations
    const a = 10;
    const b = 5;
    console.log(`${a} + ${b} = ${a + b}`);
    
    return "Program completed!";
}

// Execute the function
greetUser();
"""
                
        # Add support for other languages as needed
            
        return code
    
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