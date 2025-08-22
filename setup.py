# setup.py

from setuptools import setup, find_packages

setup(
    name="crypto-portfolio-tracker",
    version="1.0.0",
    description="Professional crypto portfolio performance tracking system",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "dash>=2.14.0",
        "plotly>=5.17.0",
        "dash-bootstrap-components>=1.5.0",
        "requests>=2.31.0",
        "scipy>=1.11.0",
        "python-dateutil>=2.8.2",
        "openpyxl>=3.1.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "crypto-portfolio=main:main",
        ],
    },
)
