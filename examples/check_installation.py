"""
Helper script to check what Laneful components are available.
"""

def check_installation():
    """Check what Laneful components are available and provide installation guidance."""
    print("Laneful Python Client - Installation Check")
    print("==========================================")
    print()
    
    try:
        import laneful
        print("✓ Laneful package is installed")
        print(f"  Version: {laneful.__version__}")
    except ImportError:
        print("✗ Laneful package not found")
        print("  Install with: pip install laneful-python")
        return
    
    # Check sync support
    if laneful.has_sync_support():
        print("✓ Synchronous client available")
        try:
            from laneful import LanefulClient
            print("  ✓ LanefulClient can be imported")
        except ImportError as e:
            print(f"  ✗ LanefulClient import failed: {e}")
    else:
        print("✗ Synchronous client not available")
        print("  Install with: pip install laneful-python[sync]")
    
    # Check async support  
    if laneful.has_async_support():
        print("✓ Asynchronous client available")
        try:
            from laneful import AsyncLanefulClient
            print("  ✓ AsyncLanefulClient can be imported")
        except ImportError as e:
            print(f"  ✗ AsyncLanefulClient import failed: {e}")
    else:
        print("✗ Asynchronous client not available")
        print("  Install with: pip install laneful-python[async]")
    
    # Show available clients
    available = laneful.get_available_clients()
    print(f"\nAvailable clients: {', '.join(available) if available else 'none'}")
    
    # Installation recommendations
    print("\nInstallation Options:")
    print("├── Default (sync only):     pip install laneful-python")
    print("├── Async support:           pip install laneful-python[async]")
    print("├── Explicit sync:           pip install laneful-python[sync]")
    print("└── Full support:            pip install laneful-python[all]")
    
    # Show examples based on what's available
    if laneful.has_sync_support():
        print("\n📄 Sync Example:")
        print("from laneful import LanefulClient, Email, Address")
        print("client = LanefulClient(base_url, token)")
        print("response = client.send_email(email)")
    
    if laneful.has_async_support():
        print("\n🚀 Async Example:")
        print("from laneful import AsyncLanefulClient, Email, Address")
        print("async with AsyncLanefulClient(base_url, token) as client:")
        print("    response = await client.send_email(email)")


if __name__ == "__main__":
    check_installation()
