"""
文件操作工具模块

提供文件读写、编码检测等工具函数。
"""

import logging
import os
from typing import Optional, Tuple

import chardet

logger = logging.getLogger(__name__)


def detect_encoding(file_path: str) -> str:
    """
    检测文件编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 检测到的编码，如果检测失败返回 'utf-8'
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10240)  # 读取前10KB检测编码

        if not raw_data:
            return 'utf-8'

        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')

        # 处理一些特殊情况
        if encoding and encoding.lower() in ['ascii', 'utf-8-sig']:
            encoding = 'utf-8'
        elif not encoding:
            encoding = 'utf-8'

        return encoding

    except Exception as e:
        logger.warning(f"检测文件编码失败 {file_path}: {e}")
        return 'utf-8'


def read_file_safe(file_path: str, encoding: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    安全读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 指定编码，如果为None则自动检测
        
    Returns:
        Tuple[Optional[str], str]: (文件内容, 使用的编码)，如果读取失败返回(None, "")
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None, ""

    if not encoding:
        encoding = detect_encoding(file_path)

    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        return content, encoding

    except Exception as e:
        logger.error(f"读取文件失败 {file_path}: {e}")
        return None, ""


def write_file_safe(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    安全写入文件内容
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码格式
        
    Returns:
        bool: 写入是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)

        logger.debug(f"文件写入成功: {file_path}")
        return True

    except Exception as e:
        logger.error(f"写入文件失败 {file_path}: {e}")
        return False


def ensure_dir(directory: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        bool: 创建或确认存在是否成功
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {directory}: {e}")
        return False


def get_file_size(file_path: str) -> int:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        int: 文件大小（字节），如果文件不存在返回-1
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return -1


def is_text_file(file_path: str) -> bool:
    """
    判断是否为文本文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否为文本文件
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)

        if not chunk:
            return True

        # 检查是否包含空字节（二进制文件的特征）
        if b'\x00' in chunk:
            return False

        # 尝试解码为文本
        try:
            chunk.decode('utf-8')
            return True
        except UnicodeDecodeError:
            try:
                chunk.decode('latin-1')
                return True
            except UnicodeDecodeError:
                return False

    except Exception:
        return False


def backup_file(file_path: str, backup_suffix: str = '.backup') -> Optional[str]:
    """
    备份文件
    
    Args:
        file_path: 原文件路径
        backup_suffix: 备份文件后缀
        
    Returns:
        Optional[str]: 备份文件路径，备份失败返回None
    """
    if not os.path.exists(file_path):
        return None

    backup_path = file_path + backup_suffix

    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"文件备份成功: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"文件备份失败 {file_path}: {e}")
        return None
