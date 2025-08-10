#!/bin/bash
# Project Sage Installation Script
# Automatically sets up virtual environment and installs Sage

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Project Sage Installation Script${NC}"
echo "=========================================="

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}❌ Python $required_version or higher is required. Found: $python_version${NC}"
    echo "Please install Python 3.9+ from https://python.org"
    exit 1
fi

echo -e "${GREEN}✅ Python $python_version found${NC}"

# Check if we're already in the project directory
if [ ! -f "pyproject.toml" ] || [ ! -d "sage" ]; then
    echo -e "${RED}❌ Please run this script from the project-sage directory${NC}"
    echo "Usage: cd project-sage && ./install.sh"
    exit 1
fi

# Check for Tesseract
echo -e "${YELLOW}Checking Tesseract OCR...${NC}"
if ! command -v tesseract &> /dev/null; then
    echo -e "${RED}❌ Tesseract OCR not found${NC}"
    echo -e "${YELLOW}Installing Tesseract...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install tesseract
            echo -e "${GREEN}✅ Tesseract installed via Homebrew${NC}"
        else
            echo -e "${RED}❌ Homebrew not found. Please install Tesseract manually:${NC}"
            echo "brew install tesseract"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y tesseract-ocr
            echo -e "${GREEN}✅ Tesseract installed via apt${NC}"
        else
            echo -e "${RED}❌ apt-get not found. Please install Tesseract manually${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Unsupported operating system. Please install Tesseract manually${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Tesseract OCR found${NC}"
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d "sage-env" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists. Removing...${NC}"
    rm -rf sage-env
fi

python3 -m venv sage-env
echo -e "${GREEN}✅ Virtual environment created${NC}"

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source sage-env/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✅ pip upgraded${NC}"

# Install Project Sage
echo -e "${YELLOW}Installing Project Sage...${NC}"
pip install -e .
echo -e "${GREEN}✅ Project Sage installed${NC}"

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
sage_version=$(sage --version 2>/dev/null || echo "unknown")
if [ "$sage_version" != "unknown" ]; then
    echo -e "${GREEN}✅ Installation verified: $sage_version${NC}"
else
    echo -e "${RED}❌ Installation verification failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Project Sage installed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Navigate to your project directory:"
echo "   cd /path/to/your/project"
echo ""
echo "2. Activate the Sage environment:"
echo "   source $(pwd)/sage-env/bin/activate"
echo ""
echo "3. Initialize Sage for your project:"
echo "   sage setup"
echo ""
echo "4. Index your documents:"
echo "   sage update"
echo ""
echo "5. Start using Sage:"
echo "   sage chat"
echo ""
echo -e "${YELLOW}💡 Pro Tip: For Vietnamese documents, choose Google Gemini during setup!${NC}"
echo ""
echo -e "${BLUE}📚 Documentation: https://github.com/yourusername/project-sage${NC}"