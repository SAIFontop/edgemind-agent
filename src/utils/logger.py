"""
EdgeMind Agent - Logger
=========================
نظام التسجيل المتقدم
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path
from datetime import datetime

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


class EdgeMindLogger:
    """
    نظام تسجيل مخصص لـ EdgeMind Agent
    
    - دعم الألوان
    - تدوير الملفات
    - مستويات متعددة
    """
    
    def __init__(
        self,
        name: str = "EdgeMind",
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        console_output: bool = True
    ):
        """
        تهيئة نظام التسجيل
        
        Args:
            name: اسم المسجل
            level: مستوى التسجيل
            log_file: مسار ملف السجل
            max_size: أقصى حجم للملف
            backup_count: عدد النسخ الاحتياطية
            console_output: إخراج للوحدة الطرفية
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers = []  # مسح المعالجات السابقة
        
        # صيغة التسجيل
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # معالج الوحدة الطرفية
        if console_output:
            if HAS_COLORLOG:
                # مع ألوان
                color_format = (
                    "%(log_color)s%(asctime)s - %(name)s - "
                    "%(levelname)s - %(message)s%(reset)s"
                )
                color_formatter = colorlog.ColoredFormatter(
                    color_format,
                    datefmt=date_format,
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(color_formatter)
            else:
                # بدون ألوان
                formatter = logging.Formatter(log_format, date_format)
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
        
        # معالج الملف
        if log_file:
            # إنشاء المجلد إذا لم يوجد
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(log_format, date_format)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """تسجيل debug"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """تسجيل info"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """تسجيل warning"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """تسجيل error"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """تسجيل critical"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """تسجيل استثناء مع traceback"""
        self.logger.exception(message, *args, **kwargs)


# مسجل عام
_default_logger: Optional[EdgeMindLogger] = None


def get_logger(
    name: str = "EdgeMind",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> EdgeMindLogger:
    """
    الحصول على مسجل
    
    Args:
        name: اسم المسجل
        level: المستوى
        log_file: ملف السجل
    
    Returns:
        EdgeMindLogger
    """
    global _default_logger
    
    if _default_logger is None:
        # تحديد مسار السجل الافتراضي
        if log_file is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_file = str(log_dir / "edgemind.log")
        
        _default_logger = EdgeMindLogger(
            name=name,
            level=level,
            log_file=log_file
        )
    
    return _default_logger


# للاختبار
if __name__ == "__main__":
    logger = get_logger(level="DEBUG")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    try:
        raise ValueError("Test exception")
    except:
        logger.exception("An exception occurred")
