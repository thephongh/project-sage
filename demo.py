#!/usr/bin/env python3
"""
Demo script for Project Sage installation and usage.

This script demonstrates how to:
1. Install Project Sage
2. Set up a sample project
3. Add sample documents
4. Use the main commands

Run this in a clean directory to see Sage in action.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path


def create_sample_documents(project_dir: Path):
    """Create sample documents for demonstration."""
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Create sample markdown file
    with open(docs_dir / "project_overview.md", "w") as f:
        f.write("""# Renewable Energy Project Overview

## Project Details
- **Name**: Solar Farm Development Project
- **Location**: Hưng Yên Province, Vietnam
- **Capacity**: 50 MW Solar PV
- **Investment**: $45 million USD
- **Timeline**: 24 months (2024-2026)

## Key Stakeholders
- **Developer**: Green Energy Solutions Ltd.
- **EPC Contractor**: Vietnam Solar Tech Co.
- **Investor**: International Clean Energy Fund
- **Local Partner**: Hưng Yên Energy JSC

## Technical Specifications
- Solar panels: Mono-crystalline silicon, 540W per panel
- Inverters: Central inverters, 2.5 MW capacity each
- Grid connection: 110kV transmission line
- Expected annual generation: 75 GWh

## Project Phases
1. **Phase 1**: Site preparation and permitting (6 months)
2. **Phase 2**: Equipment procurement and delivery (8 months)
3. **Phase 3**: Construction and installation (10 months)
4. **Phase 4**: Testing and commissioning (2 months)

## Financial Structure
- Total project cost: $45,000,000
- Debt financing: 70% ($31,500,000)
- Equity financing: 30% ($13,500,000)
- Expected IRR: 12.5%
- Payback period: 8.5 years
""")
    
    # Create sample contract document
    with open(docs_dir / "epc_contract_summary.txt", "w") as f:
        f.write("""EPC CONTRACT SUMMARY

Contract Number: EPC-2024-001
Date: March 15, 2024
Contractor: Vietnam Solar Tech Co.

SCOPE OF WORK:
- Engineering design and detailed drawings
- Procurement of all major equipment
- Construction and installation services
- Testing and commissioning
- 2-year warranty period

KEY COMMERCIAL TERMS:
- Contract Price: $35,000,000 USD (Fixed Price)
- Payment Terms: 
  * 10% advance payment upon contract signing
  * 20% upon equipment delivery to site
  * 60% progress payments based on milestones
  * 10% retention released after warranty period

MAJOR EQUIPMENT INCLUDED:
- 92,593 solar panels (540W each)
- 20 central inverters (2.5MW each)
- Electrical equipment and cables
- Mounting structures and foundations
- SCADA and monitoring systems

DELIVERY SCHEDULE:
- Engineering completion: 4 months
- Equipment delivery: 8 months
- Construction completion: 18 months
- Commercial operation: 20 months

PENALTIES AND BONUSES:
- Liquidated damages: $50,000 per week for delay
- Early completion bonus: $25,000 per week
- Performance guarantees required for all major equipment

WARRANTIES:
- Solar panels: 25 years performance warranty
- Inverters: 5 years full warranty
- Construction work: 2 years warranty
- System performance: 95% availability guarantee
""")
    
    # Create sample technical specification
    with open(docs_dir / "technical_specs.md", "w") as f:
        f.write("""# Technical Specifications Document

## Solar Panel Specifications
- **Model**: SunPower SPR-540-COM
- **Type**: Monocrystalline Silicon
- **Power Output**: 540W ±3%
- **Efficiency**: 21.2%
- **Dimensions**: 2384 x 1303 x 46 mm
- **Weight**: 32.5 kg
- **Operating Temperature**: -40°C to +85°C
- **Wind Load**: 2400 Pa
- **Snow Load**: 5400 Pa
- **Warranty**: 25 years power output guarantee

## Inverter Specifications
- **Model**: SMA Sunny Central 2500-EV
- **Type**: Central inverter
- **AC Power Output**: 2500 kW
- **Maximum Efficiency**: 98.5%
- **Input Voltage Range**: 880-1500 VDC
- **Output Voltage**: 400V AC
- **Protection**: IP65 rating
- **Operating Temperature**: -25°C to +60°C
- **Warranty**: 5 years standard, extendable to 20 years

## Monitoring System
- **SCADA Platform**: SMA Data Manager M
- **Communication**: Ethernet, WiFi, cellular
- **Data Logging**: 10-second intervals
- **Performance Monitoring**: Real-time generation tracking
- **Alarm System**: SMS and email notifications
- **Weather Monitoring**: Irradiance, temperature, wind speed

## Grid Connection
- **Connection Point**: Hưng Yên 110kV substation
- **Transmission Line**: 5 km, 110kV overhead line
- **Protection Systems**: Distance protection, overcurrent protection
- **Power Factor**: 0.95 leading to 0.95 lagging
- **Grid Code Compliance**: EVN grid code requirements
""")
    
    print(f"Created sample documents in {docs_dir}")


def main():
    """Run the demo."""
    print("🌟 Project Sage Demo")
    print("=" * 50)
    
    # Check if we're in the project directory
    if not Path("sage").exists():
        print("❌ This demo should be run from the project-sage directory")
        print("Please run: cd /path/to/project-sage && python demo.py")
        sys.exit(1)
    
    # Create a temporary demo project
    demo_dir = Path.cwd() / "demo_project"
    if demo_dir.exists():
        print(f"Removing existing demo directory: {demo_dir}")
        shutil.rmtree(demo_dir)
    
    demo_dir.mkdir()
    print(f"Created demo project directory: {demo_dir}")
    
    # Change to demo directory
    original_dir = Path.cwd()
    os.chdir(demo_dir)
    
    try:
        # Create sample documents
        create_sample_documents(Path.cwd())
        
        print("\n📝 Sample documents created!")
        print("\nTo continue the demo:")
        print(f"1. cd {demo_dir}")
        print("2. sage setup  # This will open a GUI - enter your API key")
        print("3. sage update  # Index the sample documents")
        print("4. sage status  # Check the knowledge base status")
        print('5. sage ask "What is the total investment amount?"')
        print('6. sage ask "Who is the EPC contractor?"')
        print('7. sage ask "What are the solar panel specifications?"')
        
        print(f"\n🎯 Demo project ready at: {demo_dir}")
        print("The sample documents include:")
        print("  • Project overview with financial details")
        print("  • EPC contract summary with commercial terms")
        print("  • Technical specifications for equipment")
        
    except Exception as e:
        print(f"❌ Error setting up demo: {e}")
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    main()