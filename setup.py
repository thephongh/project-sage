"""Setup script for Project Sage."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="project-sage",
    version="1.1.0",
    author="Project Sage Team",
    author_email="sage@example.com",
    description="An intelligent AI assistant for complex project management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/project-sage",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Project Management",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
        "customtkinter>=5.2.0",
        "langchain>=0.2.0",
        "langchain-community>=0.2.0",
        "langchain-google-genai>=1.0.0",
        "langchain-anthropic>=0.1.0",
        "langchain-openai>=0.1.0",
        "chromadb>=0.5.0",
        "unstructured[all-docs]>=0.14.0",
        "pytesseract>=0.3.10",
        "pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "tiktoken>=0.7.0",
        "matplotlib>=3.5.0"
    ],
    entry_points={
        "console_scripts": [
            "sage=sage.cli:main",
        ],
    },
)