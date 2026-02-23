from setuptools import setup, find_packages

setup(
    name="hellas-abm",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "tqdm>=4.62.0",
        "plotly>=5.0.0",
        "streamlit>=1.20.0",
    ],
    author="CryptoEconLab",
    description="Agent-Based Model for Hellas Fraud Game Protocol",
    python_requires=">=3.8",
)
