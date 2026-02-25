#!/bin/bash
# Complete setup script for voice-chat-v2

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Voice Chat v2 - Complete Setup                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi

if ! command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis not found. Please install and start Redis${NC}"
    echo "   macOS: brew install redis && brew services start redis"
    echo "   Ubuntu: sudo apt-get install redis-server && sudo service redis-server start"
fi

echo -e "${GREEN}✅ Prerequisites check complete${NC}"
echo ""

# Setup Backend
echo "📦 Setting up Backend..."
echo ""

cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Please configure your API keys${NC}"
    cp .env.example .env
    echo "   Edit backend/.env with your:"
    echo "   - OPENAI_API_KEY"
    echo "   - ELEVENLABS_API_KEY (optional)"
    echo ""
fi

cd ..

# Setup Frontend
echo ""
echo "📦 Setting up Frontend..."
echo ""

cd frontend

echo "Installing Node.js dependencies..."
npm install

cd ..

# Create run script
echo "Creating run.sh script..."
cat > run.sh << 'RUNSCRIPT'
#!/bin/bash
# Run both backend and frontend

echo "🚀 Starting Voice Chat v2..."
echo ""

# Start backend
echo "Starting Backend on port 9004..."
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 9004 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting Frontend on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both services started!"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔌 Backend:  http://localhost:9004"
echo "📚 API Docs: http://localhost:9004/docs"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
RUNSCRIPT

chmod +x run.sh

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP COMPLETE!                                      ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  Next steps:                                             ║"
echo "║                                                          ║"
echo "║  1. Configure API keys:                                  ║"
echo "║     Edit backend/.env                                    ║"
echo "║                                                          ║"
echo "║  2. Start the application:                               ║"
echo "║     ./run.sh                                             ║"
echo "║                                                          ║"
echo "║  3. Open in browser:                                     ║"
echo "║     http://localhost:5173                                ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
