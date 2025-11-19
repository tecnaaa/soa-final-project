import logging
import json
from datetime import datetime, timedelta
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cấu hình logging
logging.basicConfig(
    filename='security_monitoring.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('security_monitoring')

class SecurityMonitor:
    def __init__(self):
        self._suspicious_activities = defaultdict(list)
        self._ip_blacklist = set()
        self._alert_thresholds = {
            'failed_login': 5,  # Số lần đăng nhập thất bại tối đa
            'password_change': 3,  # Số lần đổi mật khẩu tối đa trong 24h
            'api_rate': 100,  # Số request API tối đa trong 1 phút
        }
        
    def track_activity(
        self,
        activity_type: str,
        user_id: Optional[str],
        ip_address: str,
        details: Dict = None
    ):
        """Theo dõi hoạt động và kiểm tra có đáng ngờ không"""
        now = datetime.now()
        activity = {
            'timestamp': now,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details or {}
        }
        
        # Thêm hoạt động vào danh sách theo dõi
        self._suspicious_activities[activity_type].append(activity)
        
        # Kiểm tra các ngưỡng cảnh báo
        self._check_thresholds(activity_type, user_id, ip_address)
        
        # Xóa các hoạt động cũ (>24h)
        self._cleanup_old_activities()
        
    def _check_thresholds(self, activity_type: str, user_id: str, ip_address: str):
        """Kiểm tra các ngưỡng cảnh báo và gửi thông báo nếu vượt quá"""
        recent_activities = self._get_recent_activities(activity_type, user_id, ip_address)
        
        if activity_type == 'failed_login' and len(recent_activities) >= self._alert_thresholds['failed_login']:
            self._handle_alert(
                'Nhiều lần đăng nhập thất bại',
                f'Phát hiện {len(recent_activities)} lần đăng nhập thất bại từ IP {ip_address}',
                user_id
            )
            self._ip_blacklist.add(ip_address)
            
        elif activity_type == 'password_change' and len(recent_activities) >= self._alert_thresholds['password_change']:
            self._handle_alert(
                'Thay đổi mật khẩu bất thường',
                f'Người dùng {user_id} đã thay đổi mật khẩu {len(recent_activities)} lần trong 24h',
                user_id
            )
            
    def _get_recent_activities(
        self,
        activity_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict]:
        """Lấy các hoạt động gần đây của một loại cụ thể"""
        now = datetime.now()
        activities = self._suspicious_activities.get(activity_type, [])
        
        return [
            activity for activity in activities
            if (now - activity['timestamp'] < timedelta(hours=hours)) and
            (not user_id or activity['user_id'] == user_id) and
            (not ip_address or activity['ip_address'] == ip_address)
        ]
        
    def _cleanup_old_activities(self):
        """Xóa các hoạt động cũ hơn 24h"""
        now = datetime.now()
        for activity_type in self._suspicious_activities:
            self._suspicious_activities[activity_type] = [
                activity for activity in self._suspicious_activities[activity_type]
                if now - activity['timestamp'] < timedelta(hours=24)
            ]
            
    def _handle_alert(self, title: str, message: str, user_id: Optional[str]):
        """Xử lý cảnh báo bảo mật"""
        # Log cảnh báo
        logger.warning(f"Security Alert - {title}: {message}")
        
        # Gửi email cho admin
        self._send_alert_email(title, message)
        
    def _send_alert_email(self, title: str, message: str):
        """Gửi email cảnh báo cho admin"""
        try:
            smtp_host = os.getenv('SMTP_HOST')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_user = os.getenv('SMTP_USER')
            smtp_pass = os.getenv('SMTP_PASSWORD')
            admin_email = os.getenv('ADMIN_EMAIL')
            
            if not all([smtp_host, smtp_user, smtp_pass, admin_email]):
                logger.error("Missing email configuration")
                return
                
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = admin_email
            msg['Subject'] = f"Security Alert: {title}"
            
            body = f"""
            Security Alert Details:
            
            Title: {title}
            Message: {message}
            Time: {datetime.now()}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            
    def is_ip_blacklisted(self, ip_address: str) -> bool:
        """Kiểm tra IP có trong danh sách đen không"""
        return ip_address in self._ip_blacklist
        
    def remove_from_blacklist(self, ip_address: str):
        """Xóa IP khỏi danh sách đen"""
        if ip_address in self._ip_blacklist:
            self._ip_blacklist.remove(ip_address)
            
# Singleton instance
security_monitor = SecurityMonitor()