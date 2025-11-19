"""
Email Service - Async SMTP for sending emails
"""
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import logging
import sys
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file explicitly from backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'

print(f"[EMAIL_SERVICE] Loading .env from: {env_path}")
print(f"[EMAIL_SERVICE] .env file exists: {env_path.exists()}")

# Load environment variables - MUST be before using os.getenv()
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"[EMAIL_SERVICE] [OK] .env file loaded successfully")
else:
    print(f"[EMAIL_SERVICE] [WARN] .env file NOT FOUND at {env_path}")
    # Try loading from parent directories
    for i in range(1, 5):
        potential_path = backend_dir / ('../' * i) / '.env'
        potential_path = potential_path.resolve()
        if potential_path.exists():
            load_dotenv(dotenv_path=potential_path, override=True)
            print(f"[EMAIL_SERVICE] [OK] .env loaded from: {potential_path}")
            break

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

# Email Configuration từ environment variables - AFTER load_dotenv
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_NAME = os.getenv("SENDER_NAME", "Fitness Dashboard")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# If SENDER_EMAIL not set, use SMTP_USER
if not SENDER_EMAIL:
    SENDER_EMAIL = SMTP_USER

print(f"[EMAIL_SERVICE] ========================================")
print(f"[EMAIL_SERVICE] SMTP Configuration Loaded:")
print(f"[EMAIL_SERVICE]   SMTP_HOST={SMTP_HOST}")
print(f"[EMAIL_SERVICE]   SMTP_PORT={SMTP_PORT}")
print(f"[EMAIL_SERVICE]   SMTP_USER={SMTP_USER if SMTP_USER else '(NOT SET)'}")
print(f"[EMAIL_SERVICE]   SMTP_PASSWORD={'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else '(NOT SET)'}")
print(f"[EMAIL_SERVICE]   SENDER_EMAIL={SENDER_EMAIL if SENDER_EMAIL else '(NOT SET)'}")
print(f"[EMAIL_SERVICE]   SENDER_NAME={SENDER_NAME}")
print(f"[EMAIL_SERVICE]   FRONTEND_URL={FRONTEND_URL}")
print(f"[EMAIL_SERVICE] ========================================")


class EmailService:
    """Service de gui email async"""

    def __init__(self):
        self._reload_config()
        print(f"[EMAIL_SERVICE] EmailService initialized: sender={self.sender_email}, host={self.smtp_host}:{self.smtp_port}")

    def _reload_config(self):
        """Reload configuration from environment variables"""
        # Reload .env file to ensure fresh configuration
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        
        # Update configuration from environment
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.sender_name = os.getenv("SENDER_NAME", "Fitness Dashboard")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        
        # If SENDER_EMAIL not set, use SMTP_USER
        if not self.sender_email:
            self.sender_email = self.smtp_user

    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None,
    ) -> bool:
        """
        Gui email async
        
        Args:
            recipient_email: Email nguoi nhan
            subject: Tieu de email
            html_content: Noi dung HTML
            plain_text: Noi dung text (fallback)
        
        Returns:
            True neu gui thanh cong, False neu loi
        """
        try:
            # Reload config before sending to ensure fresh settings
            self._reload_config()
            
            # Kiem tra cau hinh
            if not self.smtp_user or not self.smtp_password:
                logger.warning("[EMAIL_SERVICE] SMTP credentials not configured. Email not sent.")
                print("[EMAIL_SERVICE] [ERROR] SMTP credentials are empty!")
                print(f"[EMAIL_SERVICE] SMTP_USER: {self.smtp_user if self.smtp_user else '(NOT SET)'}")
                print(f"[EMAIL_SERVICE] SMTP_PASSWORD: {self.smtp_password if self.smtp_password else '(NOT SET)'}")
                return False

            logger.info(f"[EMAIL_SERVICE] [INFO] Attempting to send email to {recipient_email}")
            print(f"[EMAIL_SERVICE] [INFO] Attempting to send email to {recipient_email}")
            print(f"[EMAIL_SERVICE] Subject: {subject}")
            print(f"[EMAIL_SERVICE] From: {self.sender_email}")

            # Tao message
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = recipient_email
            msg["Subject"] = subject

            # Them plain text phien ban
            if plain_text:
                msg.attach(MIMEText(plain_text, "plain"))
            else:
                msg.attach(MIMEText(html_content.replace("<br>", "\n"), "plain"))

            # Them HTML phien ban
            msg.attach(MIMEText(html_content, "html"))

            # Gui email voi timeout
            logger.info(f"[EMAIL_SERVICE] [INFO] Connecting to SMTP server {self.smtp_host}:{self.smtp_port}")
            print(f"[EMAIL_SERVICE] [INFO] Connecting to SMTP server {self.smtp_host}:{self.smtp_port}")
            
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host, 
                port=self.smtp_port,
                timeout=10
            ) as smtp:
                logger.info("[EMAIL_SERVICE] [OK] SMTP connection established")
                print("[EMAIL_SERVICE] [OK] SMTP connection established")
                
                logger.info(f"[EMAIL_SERVICE] [INFO] Attempting login with user: {self.smtp_user}")
                print(f"[EMAIL_SERVICE] [INFO] Attempting login with user: {self.smtp_user}")
                
                await smtp.login(self.smtp_user, self.smtp_password)
                logger.info(f"[EMAIL_SERVICE] [OK] SMTP login successful")
                print(f"[EMAIL_SERVICE] [OK] SMTP login successful")
                
                logger.info(f"[EMAIL_SERVICE] [INFO] Sending message to {recipient_email}")
                print(f"[EMAIL_SERVICE] [INFO] Sending message to {recipient_email}")
                
                await smtp.send_message(msg)
                logger.info(f"[EMAIL_SERVICE] [OK] Message sent successfully")
                print(f"[EMAIL_SERVICE] [OK] Message sent successfully")

            logger.info(f"[EMAIL_SERVICE] [SUCCESS] Email sent successfully to {recipient_email}")
            print(f"[EMAIL_SERVICE] [SUCCESS] Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"[EMAIL_SERVICE] [ERROR] Failed to send email to {recipient_email}: {type(e).__name__}: {str(e)}")
            print(f"[EMAIL_SERVICE] [ERROR]: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"[EMAIL_SERVICE] Traceback: {traceback.format_exc()}")
            print(f"[EMAIL_SERVICE] Traceback:\n{traceback.format_exc()}")
            return False

    async def send_password_reset_email(
        self, user_email: str, user_name: str, reset_token: str
    ) -> bool:
        """
        Gui email reset password
        
        Args:
            user_email: Email cua user
            user_name: Ten cua user
            reset_token: Token de reset password
        
        Returns:
            True neu gui thanh cong
        """
        # Reload config before sending
        self._reload_config()
        
        # Tao reset link
        reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"

        # HTML template cho email
        html_template = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #007bff; color: white; padding: 20px; border-radius: 5px; }
                    .content { padding: 20px; background-color: #f9f9f9; margin: 20px 0; }
                    .button { display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .footer { font-size: 12px; color: #666; text-align: center; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Fitness Dashboard</h1>
                        <p>Yeu cau Dat Lai Mat Khau</p>
                    </div>
                    
                    <div class="content">
                        <p>Xin chao {{ user_name }},</p>
                        <p>Chung toi nhan duoc yeu cau dat lai mat khau cua ban. Bam vao link ben duoi de tiep tuc:</p>
                        
                        <a href="{{ reset_link }}" class="button">Dat Lai Mat Khau</a>
                        
                        <p>Hoac sao chep link nay vao trinh duyet:</p>
                        <p style="word-break: break-all; background-color: #e9e9e9; padding: 10px; border-radius: 3px;">
                            {{ reset_link }}
                        </p>
                        
                        <p style="color: #666; font-size: 12px;">
                            <strong>Luu y:</strong> Link nay se het han trong 5 phut. Neu ban khong yeu cau dat lai mat khau, ban co the bo qua email nay.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 Fitness Dashboard. All rights reserved.</p>
                        <p>Day la email tu dong, vui long khong tra loi.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        # Plain text version
        plain_text = f"""
Fitness Dashboard - Yeu cau Dat Lai Mat Khau

Xin chao {user_name},

Chung toi nhan duoc yeu cau dat lai mat khau cua ban. Truy cap link ben duoi de tiep tuc:

{reset_link}

Link nay se het han trong 5 phut. Neu ban khong yeu cau dat lai mat khau, ban co the bo qua email nay.

© 2025 Fitness Dashboard. All rights reserved.
        """

        # Render template
        template = Template(html_template)
        html_content = template.render(user_name=user_name, reset_link=reset_link)

        # Gui email
        return await self.send_email(
            recipient_email=user_email,
            subject="Yeu cau Dat Lai Mat Khau - Fitness Dashboard",
            html_content=html_content,
            plain_text=plain_text,
        )

    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """
        Gui email chao mung sau khi dang ky
        
        Args:
            user_email: Email cua user
            user_name: Ten cua user
        
        Returns:
            True neu gui thanh cong
        """
        # Reload config before sending
        self._reload_config()
        
        html_template = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #28a745; color: white; padding: 20px; border-radius: 5px; }
                    .content { padding: 20px; background-color: #f9f9f9; margin: 20px 0; }
                    .footer { font-size: 12px; color: #666; text-align: center; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Fitness Dashboard</h1>
                        <p>Chao Mung Ban Tham Gia!</p>
                    </div>
                    
                    <div class="content">
                        <p>Xin chao {{ user_name }},</p>
                        <p>Chuc mung! Ban da dang ky thanh cong tai khoan Fitness Dashboard.</p>
                        <p>Hay bat dau theo doi suc khoe va fitness cua ban ngay hom nay!</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 Fitness Dashboard. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        template = Template(html_template)
        html_content = template.render(user_name=user_name)

        return await self.send_email(
            recipient_email=user_email,
            subject="Chao Mung - Fitness Dashboard",
            html_content=html_content,
        )


# Global instance
email_service = EmailService()
