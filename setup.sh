#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies  
npm install

# Create database tables
python -c "from app import db; db.create_all()"

echo "Setup complete! Your TelX Telegram Mini App is ready."
echo ""
echo "To run the development server:"
echo "1. Set up your .env file with database and bot token"
echo "2. Run: python app.py"
echo "3. For frontend development: npm run dev"
