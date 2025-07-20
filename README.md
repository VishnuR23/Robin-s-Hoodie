# AI-Driven Trading System

A comprehensive algorithmic trading platform with AI sentiment analysis.

## Architecture
- **C++ Backend**: High-performance market data ingestion and sentiment analysis
- **Python Engine**: Trading algorithms and machine learning models  
- **Swift iOS App**: Portfolio management and user interface

## Quick Start

### Development Environment Setup
```bash
# Run the setup script
./scripts/setup_dev_environment.sh

# Start development servers
docker-compose up -d
```

### Building Components
```bash
# C++ Backend
cd cpp && mkdir build && cd build
cmake .. && make

# Python Engine
cd python && pip install -e .

# iOS App
open swift/TradingApp.xcodeproj
```

## Development Workflow
- Use **VS Code** for production code development
- Use **Jupyter Lab** for research and data analysis  
- Commit frequently with descriptive messages

See `docs/development_workflow.md` for detailed guidelines.
