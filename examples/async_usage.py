"""
Async usage examples for the Laneful Python client.

Requires: pip install laneful-python[async]
"""

import asyncio
import os
import time
import base64

try:
    from laneful import AsyncLanefulClient, Email, Address, Attachment, TrackingSettings
except ImportError as e:
    print(f"Error: {e}")
    print("To run async examples, install with: pip install laneful-python[async]")
    exit(1)


async def basic_async_email_example():
    """Send a basic email asynchronously."""
    async with AsyncLanefulClient(
        base_url="https://custom-endpoint.send.laneful.net",
        auth_token="your-auth-token"
    ) as client:
        email = Email(
            from_address=Address(email="sender@example.com", name="Your Name"),
            to=[Address(email="recipient@example.com", name="Recipient Name")],
            subject="Hello from Laneful (Async)",
            text_content="This is a test email sent asynchronously.",
            html_content="<h1>This is a test email sent asynchronously.</h1>",
        )
        
        try:
            response = await client.send_email(email)
            print(f"Async email sent successfully: {response.status}")
            if response.message_id:
                print(f"Message ID: {response.message_id}")
        except Exception as e:
            print(f"Failed to send async email: {e}")


async def template_async_email_example():
    """Send a template email asynchronously."""
    async with AsyncLanefulClient(
        base_url=os.getenv("LANEFUL_BASE_URL", "https://api.laneful.net"),
        auth_token=os.getenv("LANEFUL_AUTH_TOKEN", "your-token")
    ) as client:
        email = Email(
            from_address=Address(email="sender@example.com"),
            to=[Address(email="user@example.com")],
            subject="Welcome to Our Service (Async)",
            template_id="welcome-template",
            template_data={
                "name": "John Doe",
                "company": "Acme Corp",
                "activation_link": "https://example.com/activate?token=abc123"
            },
        )
        
        response = await client.send_email(email)
        print(f"Async template email sent: {response.status}")


async def bulk_async_email_example():
    """Send multiple emails asynchronously."""
    async with AsyncLanefulClient(
        base_url="https://custom-endpoint.send.laneful.net",
        auth_token="your-auth-token"
    ) as client:
        emails = [
            Email(
                from_address=Address(email="sender@example.com"),
                to=[Address(email="user1@example.com")],
                subject="Async Bulk Email 1",
                text_content="This is the first async bulk email.",
            ),
            Email(
                from_address=Address(email="sender@example.com"),
                to=[Address(email="user2@example.com")],
                subject="Async Bulk Email 2",
                text_content="This is the second async bulk email.",
            ),
        ]
        
        responses = await client.send_emails(emails)
        for i, response in enumerate(responses):
            print(f"Async email {i+1} status: {response.status}")


async def concurrent_email_sending():
    """Send multiple emails concurrently using asyncio.gather."""
    async with AsyncLanefulClient(
        base_url="https://custom-endpoint.send.laneful.net",
        auth_token="your-auth-token"
    ) as client:
        # Create multiple email tasks
        email_tasks = []
        
        for i in range(5):
            email = Email(
                from_address=Address(email="sender@example.com"),
                to=[Address(email=f"user{i}@example.com")],
                subject=f"Concurrent Email {i+1}",
                text_content=f"This is concurrent email number {i+1}.",
            )
            # Create a task for each email
            task = client.send_email(email)
            email_tasks.append(task)
        
        # Send all emails concurrently
        print("Sending 5 emails concurrently...")
        start_time = time.time()
        
        responses = await asyncio.gather(*email_tasks, return_exceptions=True)
        
        end_time = time.time()
        print(f"All emails processed in {end_time - start_time:.2f} seconds")
        
        # Process results
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"Email {i+1} failed: {response}")
            else:
                print(f"Email {i+1} status: {response.status}")


async def async_email_with_status_check():
    """Send email and check its status asynchronously."""
    async with AsyncLanefulClient(
        base_url="https://custom-endpoint.send.laneful.net",
        auth_token="your-auth-token"
    ) as client:
        email = Email(
            from_address=Address(email="sender@example.com"),
            to=[Address(email="recipient@example.com")],
            subject="Email with Status Check (Async)",
            text_content="This email's status will be checked.",
        )
        
        # Send email
        response = await client.send_email(email)
        print(f"Email sent: {response.status}")
        
        if response.message_id:
            # Wait a bit and check status
            await asyncio.sleep(1)
            try:
                status = await client.get_email_status(response.message_id)
                print(f"Email status: {status}")
            except Exception as e:
                print(f"Failed to get email status: {e}")


async def async_email_with_attachment():
    """Send an email with attachment asynchronously."""
    async with AsyncLanefulClient(
        base_url="https://custom-endpoint.send.laneful.net",
        auth_token="your-auth-token"
    ) as client:
        # Example: attach a simple text file
        file_content = "This is async attachment content."
        encoded_content = base64.b64encode(file_content.encode()).decode()
        
        email = Email(
            from_address=Address(email="sender@example.com"),
            to=[Address(email="user@example.com")],
            subject="Async Email with Attachment",
            text_content="Please find the document attached (sent async).",
            attachments=[
                Attachment(
                    file_name="async_document.txt",
                    content=encoded_content,
                    content_type="text/plain",
                )
            ],
        )
        
        response = await client.send_email(email)
        print(f"Async email with attachment sent: {response.status}")


async def async_scheduled_email():
    """Send a scheduled email asynchronously."""
    async with AsyncLanefulClient(
        base_url="https://custom-endpoint.send.laneful.net",
        auth_token="your-auth-token"
    ) as client:
        # Schedule email to be sent 1 hour from now
        send_time = int(time.time()) + 3600
        
        email = Email(
            from_address=Address(email="sender@example.com"),
            to=[Address(email="user@example.com")],
            subject="Async Scheduled Email",
            text_content="This email was scheduled asynchronously.",
            send_time=send_time,
        )
        
        response = await client.send_email(email)
        print(f"Async scheduled email queued: {response.status}")


async def async_tracked_email():
    """Send a tracked email asynchronously."""
    async with AsyncLanefulClient(
        base_url="https://custom-endpoint.send.laneful.net",
        auth_token="your-auth-token"
    ) as client:
        email = Email(
            from_address=Address(email="sender@example.com"),
            to=[Address(email="user@example.com")],
            subject="Async Tracked Email",
            html_content="""
            <h1>This async email is tracked</h1>
            <p>We'll know when you open this email and click on links.</p>
            <a href="https://example.com">Click here</a>
            """,
            tracking=TrackingSettings(
                opens=True,
                clicks=True,
                unsubscribes=True
            ),
        )
        
        response = await client.send_email(email)
        print(f"Async tracked email sent: {response.status}")


async def mixed_sync_async_example():
    """Example showing how to use sync and async clients together."""
    try:
        from laneful import LanefulClient  # Import sync client
    except ImportError:
        print("Sync client not available. Install with: pip install laneful-python[all]")
        return
    
    # You can use both sync and async clients in the same application
    print("Using sync client:")
    sync_client = LanefulClient(
        base_url="https://api.laneful.net",
        auth_token="your-token"
    )
    
    sync_email = Email(
        from_address=Address(email="sender@example.com"),
        to=[Address(email="sync@example.com")],
        subject="Sync Email",
        text_content="This was sent synchronously."
    )
    
    try:
        sync_response = sync_client.send_email(sync_email)
        print(f"Sync email status: {sync_response.status}")
    except Exception as e:
        print(f"Sync email failed: {e}")
    finally:
        sync_client.close()
    
    print("\nUsing async client:")
    async with AsyncLanefulClient(
        base_url="https://api.laneful.net",
        auth_token="your-token"
    ) as async_client:
        async_email = Email(
            from_address=Address(email="sender@example.com"),
            to=[Address(email="async@example.com")],
            subject="Async Email",
            text_content="This was sent asynchronously."
        )
        
        try:
            async_response = await async_client.send_email(async_email)
            print(f"Async email status: {async_response.status}")
        except Exception as e:
            print(f"Async email failed: {e}")


async def main():
    """Run all async examples."""
    print("Laneful Async Python Client Examples")
    print("====================================")
    
    examples = [
        ("Basic async email", basic_async_email_example),
        ("Template async email", template_async_email_example),
        ("Bulk async emails", bulk_async_email_example),
        ("Concurrent email sending", concurrent_email_sending),
        ("Email with status check", async_email_with_status_check),
        ("Email with attachment", async_email_with_attachment),
        ("Scheduled email", async_scheduled_email),
        ("Tracked email", async_tracked_email),
        ("Mixed sync/async usage", mixed_sync_async_example),
    ]
    
    for name, example_func in examples:
        print(f"\n--- {name} ---")
        try:
            await example_func()
            print("✓ Example completed successfully")
        except Exception as e:
            print(f"✗ Example failed: {e}")


if __name__ == "__main__":
    # Run the async examples
    asyncio.run(main())
