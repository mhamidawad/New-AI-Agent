#!/usr/bin/env python3
"""Demo script for the AI Coding Agent."""

import asyncio
import os
from ai_coding_agent import CodingAgent, Config


async def main():
    """Run the demo."""
    print("🤖 AI Coding Agent Demo")
    print("=" * 50)
    
    # Check if API keys are available
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  No API keys found!")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Initialize the agent
        print("🔧 Initializing AI Coding Agent...")
        config = Config.from_env()
        agent = CodingAgent(config)
        
        print(f"✅ Agent initialized with {agent.provider.__class__.__name__}")
        print()
        
        # Demo 1: Code Generation
        print("📝 Demo 1: Code Generation")
        print("-" * 30)
        
        description = "Create a Python function that calculates the factorial of a number"
        print(f"Request: {description}")
        
        code = await agent.generate_code(description, "python")
        print("Generated Code:")
        print(code)
        print()
        
        # Demo 2: Code Analysis
        print("🔍 Demo 2: Code Analysis")
        print("-" * 30)
        
        sample_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
        
        print("Analyzing this code:")
        print(sample_code)
        
        # Create a temporary file for analysis
        with open("temp_fibonacci.py", "w") as f:
            f.write(sample_code)
        
        analysis = await agent.analyze_file("temp_fibonacci.py")
        print("Analysis Results:")
        print(f"Language: {analysis['language']}")
        print(f"Summary: {analysis['summary']}")
        
        # Cleanup
        os.remove("temp_fibonacci.py")
        print()
        
        # Demo 3: Chat Interaction
        print("💬 Demo 3: Chat Interaction")
        print("-" * 30)
        
        questions = [
            "What is the time complexity of the fibonacci function above?",
            "How can I optimize the recursive fibonacci implementation?",
            "What are the best practices for Python function documentation?"
        ]
        
        for question in questions:
            print(f"Q: {question}")
            response = await agent.chat(question)
            print(f"A: {response[:200]}...")  # Show first 200 chars
            print()
        
        # Demo 4: Code Review
        print("🔎 Demo 4: Code Review")
        print("-" * 30)
        
        review_code = '''
def divide_numbers(a, b):
    return a / b

result = divide_numbers(10, 0)
print(result)
'''
        
        print("Reviewing this code:")
        print(review_code)
        
        review = await agent.review_code(review_code, "python")
        print("Review:")
        print(review[:300] + "...")  # Show first 300 chars
        print()
        
        print("✨ Demo completed successfully!")
        
        # Show agent status
        status = agent.get_status()
        print("\n📊 Agent Status:")
        print(f"Model: {status['model']}")
        print(f"Provider: {status['provider']}")
        print(f"Messages in context: {status['context']['message_count']}")
        print(f"Files in context: {status['context']['file_count']}")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        return


if __name__ == "__main__":
    asyncio.run(main())