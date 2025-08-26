"""
Laneful Python Client Library Demo
"""

from laneful import LanefulClient, AsyncLanefulClient, Email, Address


def main():
    """Demo of the Laneful Python client."""
    print("Laneful Python Client Library")
    print("=============================")
    print()
    print("This is a Python client library for the Laneful API.")
    print("For usage examples, see the examples/ directory.")
    print()
    
    # Basic usage example
    print("Basic usage:")
    print("```python")
    print("from laneful import LanefulClient, Email, Address")
    print()
    print('client = LanefulClient("https://api.laneful.net", "your-token")')
    print()
    print("email = Email(")
    print('    from_address=Address(email="sender@example.com"),')
    print('    to=[Address(email="recipient@example.com")],')
    print('    subject="Hello from Laneful",')
    print('    text_content="This is a test email."')
    print(")")
    print()
    print("response = client.send_email(email)")
    print('print(f"Email sent: {response.status}")')
    print("```")
    print()
    print("For more examples, run:")
    print("  python examples/basic_usage.py")
    print("  python examples/webhook_examples.py")


if __name__ == "__main__":
    main()
