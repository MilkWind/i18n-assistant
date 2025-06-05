"""
i18n-assistant 包配置文件
"""

from setuptools import setup, find_packages
import os
import sys

# 读取版本信息
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'src', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return '1.0.0'

# 读取README文件
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# 读取依赖
def get_requirements():
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 移除注释
                    requirement = line.split('#')[0].strip()
                    if requirement:
                        requirements.append(requirement)
    return requirements

# 开发依赖
dev_requirements = [
    'pytest>=7.4.3',
    'pytest-qt>=4.2.0',
    'pytest-cov>=4.0.0',
    'pytest-mock>=3.12.0',
    'black>=24.3.0',
    'flake8>=6.1.0',
    'mypy>=1.7.0',
    'isort>=5.12.0',
    'coverage>=7.3.2',
    'pre-commit>=3.6.0',
    'psutil>=5.9.0',  # 用于性能测试
]

# GUI依赖（可选）
gui_requirements = [
    'PyQt6>=6.5.0,<6.8.0',
    'PySide6>=6.5.0,<6.8.0',  # 备选GUI框架
]

setup(
    name="i18n-assistant",
    version=get_version(),
    author="Development Team",
    author_email="dev@example.com",
    description="国际化文件分析和管理工具",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/i18n-assistant",
    packages=find_packages(include=['src', 'src.*']),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Internationalization",
        "Topic :: Software Development :: Localization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.9",
    install_requires=get_requirements(),
    extras_require={
        'dev': dev_requirements,
        'gui': gui_requirements,
        'all': dev_requirements + gui_requirements,
    },
    entry_points={
        'console_scripts': [
            'i18n-assistant=src.main:main',
            'i18n-assistant-gui=src.gui.main_window:main',
            'i18n-assistant-cli=src.main:cli_main',
        ],
    },
    include_package_data=True,
    package_data={
        'src': [
            'gui/resources/*.png',
            'gui/resources/*.svg',
            'gui/resources/*.qss',
            'gui/resources/styles/*.css',
        ],
    },
    zip_safe=False,
    keywords=[
        'internationalization', 'i18n', 'localization', 'l10n',
        'translation', 'analysis', 'gui', 'tool'
    ],
    project_urls={
        "Bug Reports": "https://github.com/example/i18n-assistant/issues",
        "Source": "https://github.com/example/i18n-assistant",
        "Documentation": "https://i18n-assistant.readthedocs.io/",
    },
) 