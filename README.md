# 🃏 Rummy Score Tracker

A simple, mobile-friendly web app for tracking scores in in-person rummy card games. Built with FastAPI, Tailwind CSS, and Supabase.

## Features

- 📱 **Mobile-Friendly Design** - Works perfectly on phones and tablets
- 🎯 **Standard Rummy Rules** - Supports 100, 150, and 201 point games
- 📊 **Real-time Analytics** - Live leaderboards and winning probability tracking
- 🔐 **Simple Authentication** - Magic link email login (no passwords)
- ⚡ **Fast & Lightweight** - Instant score updates and smooth animations

## Tech Stack

- **Backend**: FastAPI + Python 3.12
- **Frontend**: Tailwind CSS + Alpine.js + Jinja2 templates
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT tokens with magic link emails
- **Email**: Mailjet for magic link delivery

## Quick Start

### 1. Setup Environment

```bash
# Clone and navigate
git clone <repository-url>
cd rummy

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Services

Copy `.env.example` to `.env` and fill in your service credentials:

```bash
cp .env.example .env
```

**Required Services:**

1. **Supabase** - Create a free account at supabase.com
   - Get your project URL and anon key
   - Run the SQL from `database_schema.sql` in your Supabase SQL editor

2. **Mailjet** - Create a free account at mailjet.com
   - Get your API key and secret
   - Verify your sender domain/email

3. **Generate JWT Secret**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

### 3. Database Setup

Run the SQL schema in `database_schema.sql` in your Supabase SQL editor to create the required tables.

### 4. Run the App

```bash
python run.py
```

Visit `http://localhost:8000` to start tracking your rummy games!

## How It Works

1. **Visit Homepage** - See rummy instructions and click "Track Scores"
2. **Quick Login** - Enter your email, receive a magic link (no password needed)
3. **Setup Game** - Select number of players, score cutoff (100/150/201), and enter player names
4. **Track Scores** - Add round scores as you play, watch the leaderboard update in real-time
5. **Game Analytics** - See who's winning, points needed to win, and round-by-round history

## Game Rules Supported

- **Standard Rummy** with sets and runs
- **Face cards**: 10 points each
- **Number cards**: Face value
- **Aces**: 1 point (can be customized to 15 points)
- **Goal**: First player to reach the cutoff loses (others win)

## Project Structure

```
rummy/
├── app/
│   ├── api/           # API routes (auth, game)
│   ├── models/        # Database models and schemas
│   ├── services/      # Business logic (auth, email, game)
│   └── utils/         # Validation utilities
├── templates/         # Jinja2 HTML templates
├── static/           # CSS, JS, images
├── database_schema.sql    # Supabase setup
└── requirements.txt       # Python dependencies
```

## Development

### Adding Features

- Follow the existing service layer pattern
- Use Pydantic schemas for data validation
- Add responsive design classes for mobile compatibility
- Test with multiple screen sizes

### Database Changes

1. Make changes in `database_schema.sql`
2. Test in Supabase development environment
3. Update Pydantic schemas in `app/models/schemas.py`

### Deployment

The app is designed for easy deployment:
- Docker support (add Dockerfile for containerization)
- Environment-based configuration
- Production-ready security practices

## Security Features

- JWT tokens with 7-day expiration
- Email validation with MX record verification
- Disposable email detection
- SQL injection protection via Supabase
- XSS protection via Jinja2 templating
- CSRF protection via secure cookies

## Mobile Optimization

- Touch-friendly buttons and inputs
- Responsive grid layouts
- Swipeable score cards
- Collapsible analytics panels
- Fast loading times with minimal JavaScript

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow existing code patterns
4. Test on multiple devices
5. Submit a pull request

## License

MIT License - feel free to use for personal or commercial projects.

---

**Built with ❤️ for card game lovers who want simple, effective score tracking.**