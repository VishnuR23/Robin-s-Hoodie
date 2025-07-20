#!/bin/bash
# Development Environment Setup Script

echo "🔧 Setting up development environment..."

# Check if required tools are installed
command -v cmake >/dev/null 2>&1 || { echo "❌ CMake is required but not installed. Please install CMake first."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Please install Python 3 first."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Please install Docker first."; exit 1; }

# Create Python virtual environment for development
echo "🐍 Setting up Python virtual environment..."
cd python
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python dependencies
pip install jupyter pandas numpy matplotlib seaborn scikit-learn
pip install fastapi uvicorn redis asyncio
pip install requests websockets
pip install ta-lib backtrader

# Create Jupyter kernel for this project
python -m ipykernel install --user --name=ai-trading-system --display-name="AI Trading System"

cd ..

# Build C++ components
echo "⚙️ Building C++ components..."
cd cpp
mkdir -p build
cd build
cmake ..
make -j$(nproc)
cd ../..

# Copy API keys template
if [ ! -f config/api_keys.json ]; then
    echo "🔑 Creating API keys file..."
    cp config/api_keys_template.json config/api_keys.json
    echo "⚠️  Please edit config/api_keys.json with your actual API keys"
fi

# Start development services
echo "🐳 Starting development services with Docker..."
docker-compose up -d redis postgres

echo "✅ Development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit config/api_keys.json with your actual API keys"
echo "2. Start coding in VS Code"
echo "3. Use Jupyter Lab for research: cd python && source venv/bin/activate && jupyter lab"
echo "4. Start the backend services: docker-compose up python-engine cpp-backend"
