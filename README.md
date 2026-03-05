# Rummy Score Tracker

A simple, mobile-friendly web app for tracking scores in in-person rummy card games. Built with FastAPI, Tailwind CSS, and SQLite.

## Features

- **Mobile-Friendly Design** - Works perfectly on phones and tablets
- **Standard Rummy Rules** - Supports configurable point cutoffs (100, 150, 201, etc.)
- **Real-time Analytics** - Live leaderboards and points-to-win tracking
- **Simple Authentication** - Magic link email login (no passwords)
- **Fast & Lightweight** - Local SQLite database with sub-millisecond queries

## Tech Stack

- **Backend**: FastAPI + Python 3.12
- **Frontend**: Tailwind CSS + Alpine.js + Jinja2 templates
- **Database**: SQLite (WAL mode)
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

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

**Required configuration:**

1. **Mailjet** - Create a free account at mailjet.com
   - Get your API key and secret
   - Verify your sender domain/email

2. **Generate JWT Secret**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **SQLite Database Path** - Defaults to `data/rummy.db` (created automatically on first run)

### 3. Run the App

```bash
python run.py
```

Visit `http://localhost:8000` to start tracking your rummy games!

## How It Works

1. **Visit Homepage** - See rummy instructions and click "Track Scores"
2. **Quick Login** - Enter your email, receive a magic link (no password needed)
3. **Setup Game** - Select number of players, score cutoff, and enter player names
4. **Track Scores** - Add round scores as you play, watch the leaderboard update
5. **Game Analytics** - See who's winning, points needed to win, and round-by-round history

## Game Rules Supported

- **Standard Rummy** with sets and runs
- **Face cards**: 10 points each
- **Number cards**: Face value
- **Aces**: 1 point (can be customized to 15 points)
- **Elimination**: Players who reach the cutoff are eliminated; last player standing wins

## Project Structure

```
rummy/
├── app/
│   ├── api/           # API routes (auth, game)
│   ├── models/        # Database layer and Pydantic schemas
│   ├── services/      # Business logic (auth, email, game)
│   └── utils/         # Validation utilities
├── templates/         # Jinja2 HTML templates
├── static/            # CSS, JS, images
├── data/              # SQLite database (created at runtime)
├── scripts/           # Migration and backup scripts
├── database_schema_sqlite.sql  # SQLite schema
└── requirements.txt   # Python dependencies
```

## Database

The app uses SQLite with WAL (Write-Ahead Logging) for better concurrency. The database is created automatically on first run at the path specified by `SQLITE_DB_PATH` in `.env`.

### Schema

Five tables: `users`, `games`, `players`, `rounds`, `scores` with foreign key constraints and cascade deletes.

See `database_schema_sqlite.sql` for the full schema.

### Backups

```bash
# Manual backup
./scripts/backup.sh

# Automated daily backup (add to crontab)
0 4 * * * /path/to/rummy/scripts/backup.sh
```

## Development

### Adding Features

- Follow the existing service layer pattern
- Use Pydantic schemas for data validation
- Add responsive design classes for mobile compatibility

### Database Changes

1. Update `database_schema_sqlite.sql`
2. Update Pydantic schemas in `app/models/schemas.py`
3. Update queries in the relevant service files

### Deployment

The app supports subdirectory deployment via the `BASE_PATH` environment variable (e.g., `/rummy`).

## Security Features

- JWT tokens with 7-day expiration
- Email validation with MX record verification
- Disposable email detection
- SQL injection protection via parameterized queries
- XSS protection via Jinja2 templating
- CSRF protection via secure cookies

## License

MIT License - feel free to use for personal or commercial projects.
