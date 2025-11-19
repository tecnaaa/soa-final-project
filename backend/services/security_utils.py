import re
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

class SecurityUtils:
    def __init__(self):
        self._failed_attempts = defaultdict(list)
        self._account_lockouts = {}
        
    def check_password_strength(self, password: str) -> tuple[bool, Optional[str]]:
        """
        Kiểm tra độ mạnh của mật khẩu
        """
        if len(password) < 8:
            return False, "Mật khẩu phải có ít nhất 8 ký tự"
            
        if not re.search(r"[A-Z]", password):
            return False, "Mật khẩu phải chứa ít nhất 1 chữ hoa"
            
        if not re.search(r"[a-z]", password):
            return False, "Mật khẩu phải chứa ít nhất 1 chữ thường"
            
        if not re.search(r"\d", password):
            return False, "Mật khẩu phải chứa ít nhất 1 số"
            
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt"
            
        return True, None
        
    def track_failed_attempt(self, username: str):
        """
        Theo dõi các lần đăng nhập thất bại
        """
        now = datetime.now()
        self._failed_attempts[username] = [
            attempt for attempt in self._failed_attempts[username]
            if now - attempt < timedelta(minutes=30)
        ]
        self._failed_attempts[username].append(now)
        
        # Khóa tài khoản nếu có quá nhiều lần thất bại
        if len(self._failed_attempts[username]) >= 5:
            self._account_lockouts[username] = now + timedelta(minutes=30)
            
    def clear_failed_attempts(self, username: str):
        """
        Xóa lịch sử đăng nhập thất bại khi đăng nhập thành công
        """
        if username in self._failed_attempts:
            del self._failed_attempts[username]
            
    def is_account_locked(self, username: str) -> tuple[bool, Optional[timedelta]]:
        """
        Kiểm tra xem tài khoản có bị khóa không
        """
        if username in self._account_lockouts:
            lockout_until = self._account_lockouts[username]
            if datetime.now() < lockout_until:
                remaining = lockout_until - datetime.now()
                return True, remaining
            else:
                del self._account_lockouts[username]
                
        return False, None