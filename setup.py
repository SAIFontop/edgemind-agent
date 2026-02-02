"""Setup configuration for EdgeMind Agent."""

from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "EdgeMind Agent - AI System Agent for Raspberry Pi OS"

setup(
    name='edgemind-agent',
    version='0.1.0',
    description='Secure AI system agent for Raspberry Pi OS',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='EdgeMind Team',
    author_email='team@edgemind.example',
    url='https://github.com/SAIFontop/edgemind-agent',
    packages=find_packages(),
    install_requires=[
        'google-generativeai>=0.3.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'flake8>=6.0.0',
            'black>=23.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'edgemind-agent=edgemind_agent.cli.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: POSIX :: Linux',
    ],
    python_requires='>=3.8',
)
