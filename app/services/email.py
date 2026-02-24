import dns.resolver
import re
from typing import Tuple
from ..config import settings
from mailjet_rest import Client
from ..utils.validation import validation_service


class EmailService:
    def __init__(self):
        self.mailjet = Client(auth=(settings.mailjet_api_key, settings.mailjet_api_secret), version='v3.1')
        self.disposable_domains = {
            'tempmail.com', 'mailinator.com', '10minutemail.com', 'guerrillamail.com',
            'throwaway.email', 'temp-mail.org', 'yopmail.com', 'maildrop.cc',
            'getairmail.com', '20minutemail.com', 'tempmail.net', 'mailnesia.com'
        }

    def validate_email(self, email: str) -> Tuple[bool, str]:
        """Multi-layer email validation"""
        
        # 1. Format validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # 2. Disposable email detection
        domain = email.split('@')[1].lower()
        if domain in self.disposable_domains:
            return False, "Disposable email addresses are not allowed"
        
        # 3. MX record verification
        try:
            dns.resolver.resolve(domain, 'MX')
        except dns.resolver.NXDOMAIN:
            return False, "Domain does not exist"
        except dns.resolver.NoAnswer:
            return False, "Domain does not have mail servers"
        except dns.resolver.NoNameservers:
            # DNS resolution failed - allow email but log
            print(f"Warning: DNS resolution failed for {domain}")
        except Exception as e:
            # Network issues - allow email but log
            print(f"Warning: MX record check failed for {domain}: {e}")
        
        return True, ""

    def send_magic_link(self, to_email: str, magic_link: str) -> bool:
        """Send magic link email for authentication"""
        
        try:
            # HTML email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Rummy Score Tracker - Login</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        padding: 20px 0;
                        border-bottom: 2px solid #e5e7eb;
                    }}
                    .content {{
                        padding: 30px 0;
                        text-align: center;
                    }}
                    .button {{
                        display: inline-block;
                        background-color: #3b82f6;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 8px;
                        margin: 20px 0;
                        font-weight: 600;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 20px 0;
                        border-top: 1px solid #e5e7eb;
                        font-size: 14px;
                        color: #6b7280;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🃏 Rummy Score Tracker</h1>
                </div>
                <div class="content">
                    <h2>Welcome Back!</h2>
                    <p>Click the button below to securely access your rummy games:</p>
                    <a href="{magic_link}" class="button">Access Your Games</a>
                    <p><small>This link expires in 7 days for your security.</small></p>
                    <p><small>If you didn't request this email, you can safely ignore it.</small></p>
                </div>
                <div class="footer">
                    <p>Track your rummy games with ease</p>
                </div>
            </body>
            </html>
            """
            
            data = {
                'Messages': [
                    {
                        'From': {
                            'Email': settings.from_email,
                            'Name': 'Rummy Score Tracker'
                        },
                        'To': [
                            {
                                'Email': to_email
                            }
                        ],
                        'Subject': '🃏 Rummy Score Tracker - Login Link',
                        'HTMLPart': html_content
                    }
                ]
            }
            
            result = self.mailjet.send.create(data=data)
            return result.status_code == 200
            
        except Exception as e:
            print(f"Error sending magic link email: {e}")
            return False




email_service = EmailService()