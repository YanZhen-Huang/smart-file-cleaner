#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件类型配置
定义各种文件类型的扩展名和处理规则
"""

# 文档类型文件扩展名
DOCUMENT_EXTENSIONS = {
    '.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.pages',
    '.xls', '.xlsx', '.ppt', '.pptx', '.odp', '.ods',
    '.md', '.markdown', '.rst', '.tex', '.latex'
}

# 图片类型文件扩展名
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.webp', '.svg', '.ico', '.psd', '.ai', '.eps', '.raw',
    '.cr2', '.nef', '.arw', '.dng', '.heic', '.heif'
}

# 代码文件扩展名（需要保护）
CODE_EXTENSIONS = {
    '.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
    '.ts', '.jsx', '.tsx', '.vue', '.html', '.css', '.scss',
    '.sass', '.less', '.sql', '.sh', '.bat', '.ps1', '.vbs'
}

# 配置文件扩展名（需要保护）
CONFIG_EXTENSIONS = {
    '.config', '.conf', '.cfg', '.ini', '.env', '.properties',
    '.yaml', '.yml', '.toml', '.xml', '.json', '.lock',
    '.gitignore', '.gitattributes', '.editorconfig'
}

# 程序文件扩展名（需要保护）
PROGRAM_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.app', '.deb', '.rpm',
    '.msi', '.pkg', '.dmg', '.iso', '.jar', '.war', '.ear'
}

# 临时文件扩展名（可删除）
TEMP_EXTENSIONS = {
    '.tmp', '.temp', '.log', '.bak', '.backup', '.old', '.cache',
    '.thumbs.db', '.ds_store', '.desktop.ini', '.dmp', '.crash',
    '.pyc', '.pyo', '.part', '.crdownload'
}

# 可删除文件名模式
DELETABLE_PATTERNS = {
    'temp', 'tmp', 'cache', 'log', 'backup', 'bak', 'old',
    'crash', 'dump', 'error', 'debug'
}

# 可删除目录模式
DELETABLE_DIRS = {
    'temp', 'tmp', 'cache', 'logs', 'backup', 'recycle',
    'trash', '__pycache__'
}

# 文件类型分类映射
FILE_TYPE_CATEGORIES = {
    'document': DOCUMENT_EXTENSIONS,
    'image': IMAGE_EXTENSIONS,
    'code': CODE_EXTENSIONS,
    'config': CONFIG_EXTENSIONS,
    'program': PROGRAM_EXTENSIONS,
    'temp': TEMP_EXTENSIONS
}

# 受保护的文件类型
PROTECTED_EXTENSIONS = CODE_EXTENSIONS | CONFIG_EXTENSIONS | PROGRAM_EXTENSIONS

# 可删除的文件类型
DELETABLE_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS | TEMP_EXTENSIONS