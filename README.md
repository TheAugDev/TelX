# TelX - Telegram Mini App Social Platform

A Twitter-like social platform designed specifically for Telegram Mini Apps, built with Flask, PostgreSQL, and the Telegram WebApp SDK.

## Features

- **Seamless Authentication**: Auto-login using Telegram user data
- **Social Feed**: Create posts, like, comment, and follow users  
- **Real-time UI**: Native Telegram theme integration
- **Mobile-First**: Optimized for mobile Telegram experience
- **Content Discovery**: Trending posts and user discovery
- **Multiple Feed Filters**: Latest, For You Page (FYP), Trending, Following

## Tech Stack

### Backend
- **Flask** - Python web framework
- **PostgreSQL** - Database 
- **SQLAlchemy** - ORM
- **Flask-CORS** - Cross-origin requests

### Frontend  
- **Telegram WebApp SDK** - Native Telegram integration
- **Tailwind CSS** - Styling framework
- **Axios** - HTTP client
- **Vanilla JavaScript** - No framework dependencies

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Telegram Bot Token

### Installation

1. **Clone and setup**
   ```bash
   git clone <your-repo>
   cd telx
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   BOT_TOKEN=your_telegram_bot_token
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

### Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Get your bot token
3. Set up a Mini App:
   ```
   /newapp
   Select your bot
   Enter app name: TelX
   Enter description: Social platform for Telegram
   Upload app icon (512x512)
   Enter Web App URL: https://your-domain.com
   ```

## Project Structure

```
telx/
├── app.py                 # Flask backend
├── index_production.html  # Production frontend
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
├── vite.config.js        # Vite configuration
├── .env.example          # Environment template
└── setup.sh              # Installation script
```

## API Endpoints

### Authentication
- `POST /api/auth` - Authenticate with Telegram data

### Posts
- `GET /api/posts` - Get posts (with filtering)
- `POST /api/posts` - Create new post
- `POST /api/posts/{id}/like` - Toggle like
- `GET /api/posts/{id}/comments` - Get comments
- `POST /api/posts/{id}/comments` - Add comment

### Users  
- `GET /api/users` - Get users for discovery
- `GET /api/users/{id}` - Get user profile
- `POST /api/users/{id}/follow` - Toggle follow
- `PUT /api/user/profile` - Update profile

## Database Schema

### Users
- Telegram ID, username, name, bio
- Profile photo URL
- Creation/update timestamps

### Posts
- Content (280 char limit)
- Optional image URL
- Author relationship
- Timestamps

### Relationships
- Likes (user + post)
- Comments (user + post + content)
- Follows (follower + following)

## Development

### Frontend Development
```bash
npm run dev  # Vite dev server
npm run build  # Production build
```

### Backend Development
```bash
python app.py  # Flask dev server
```

### Database Migrations
```python
# In Python shell
from app import db
db.create_all()  # Create tables
db.drop_all()    # Reset database
```

## Deployment

### Replit Deployment
1. Import this repository to Replit
2. Replit will auto-provide PostgreSQL database
3. Set `BOT_TOKEN` in Secrets
4. Run `python app.py`

### Production Considerations
- Set up proper environment variables
- Use production WSGI server (gunicorn)
- Configure PostgreSQL connection pooling
- Set up SSL/HTTPS
- Implement rate limiting
- Add proper error handling and logging

## Telegram Mini App Integration

The app automatically:
- Authenticates users via `initData`
- Adapts to Telegram's color scheme
- Responds to theme changes
- Handles viewport sizing
- Provides native navigation feel

## Security

- Telegram WebApp data validation
- SQL injection prevention via SQLAlchemy
- Input sanitization and validation
- Rate limiting ready for production
- CORS properly configured

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly  
5. Submit pull request

## License

MIT License - see LICENSE file

## Support

For issues and questions:
- Open GitHub issue
- Check Telegram Bot API docs
- Review Flask/SQLAlchemy documentation
