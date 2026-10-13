# 📅 Booking Assistant - Telegram Booking & Lead Capture Bot

A Telegram bot for small businesses: customers pick a service, date and time, leave their contact details and submit a booking request. Everything is saved locally in SQLite and the administrator is notified instantly. It also includes an FAQ, a Contact screen and a simple "Ask a question" lead-capture flow.

> **Status:** portfolio demo / starter template. It is **not** claimed to be production-ready. The services, prices, FAQ and contact details are **editable sample data**.

## ✨ Features

- Inline-keyboard main menu: Book an appointment, Services, FAQ, Contact, Ask a question
- Booking flow (FSM): service → date (next 7 days) → time slot → name → phone → confirmation
- Duplicate protection: a partial unique index on active `service + date + time` slots
- Phone via Telegram contact button, with manual text fallback; name and phone validation
- Cancel button in every multi-step flow
- Admin notifications for new bookings and questions
- Admin commands: `/bookings`, `/leads`, `/cancel_booking <id>` (restricted to `ADMIN_CHAT_ID`)
- FAQ (6 editable entries) and Contact screen with business hours
- All user-facing text lives in `config.py`
- Long polling only; no paid APIs, no scraping, no unsolicited messages (the bot only replies to people who start it)

## 🖼 Screenshots

Placeholders - add your own images to `docs/images/`.

| Main menu | Booking flow | Admin notification |
|---|---|---|
| ![Main menu](docs/images/main-menu.png) | ![Booking](docs/images/booking.png) | ![Admin](docs/images/admin.png) |

## 🧰 Tech Stack

- Python 3.14
- [aiogram 3.x](https://docs.aiogram.dev/) (Routers, FSM, long polling)
- SQLite via the standard-library `sqlite3`
- python-dotenv
- asyncio

## 📁 File Structure

```
telegram-booking-bot/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── bot.py            # entry point, logging, polling, error handler
├── config.py         # settings validation + editable services, slots, FAQ, texts
├── database.py       # all SQLite logic (parameterized queries)
├── keyboards.py      # inline / reply keyboards
├── states.py         # FSM state groups
├── data/
│   └── .gitkeep      # bot.db is created here at runtime (git-ignored)
└── handlers/
    ├── __init__.py   # router registration
    ├── start.py      # /start, menu, services, cancel, fallbacks
    ├── booking.py    # booking flow
    ├── faq.py
    ├── contact.py    # contact + ask-a-question flow
    └── admin.py      # admin commands
```

## 🚀 Local Setup (Windows PowerShell)

```powershell
cd telegram-booking-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env        # set BOT_TOKEN and ADMIN_CHAT_ID
python bot.py
```

If activation is blocked, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

`.env` format:

```
BOT_TOKEN=your token from BotFather
ADMIN_CHAT_ID=your numeric chat id
DATABASE_PATH=data/bot.db
```

The database file and tables are created automatically on first run. Stop the bot with `Ctrl+C`.

## 🤖 Creating a Bot with @BotFather

1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, then choose a display name (e.g. "Booking Assistant") and a username ending in `bot`.
3. BotFather replies with an HTTP API token. Paste it into `.env` as `BOT_TOKEN`.
4. Optional: `/setdescription`, `/setabouttext`, `/setcommands` (add `start`, `cancel`).

## 🔑 Getting ADMIN_CHAT_ID Safely

1. Message [@userinfobot](https://t.me/userinfobot) (or a similar trusted ID bot) and read your numeric ID, **or**
2. Temporarily set `ADMIN_CHAT_ID` to any number, start your bot, send it a message, and open `https://api.telegram.org/bot<TOKEN>/getUpdates` in your own browser to read `"from": {"id": ...}`. Do not paste that URL anywhere public: it contains your token.
3. **Important:** open your bot and press **Start** at least once. Telegram does not let bots message users who have never started them.

For a group admin chat, use the (negative) chat ID instead.

## 🔒 Security Note

**Never commit `.env` or share your bot token.** `.gitignore` excludes `.env` and the SQLite database. The bot never logs the token. If a token leaks, revoke it with `/revoke` in @BotFather. Bookings contain personal data (names, phone numbers) - handle it responsibly.

## 📖 Command Reference

| Command | Who | Description |
|---|---|---|
| `/start` | Everyone | Welcome message and main menu |
| `/cancel` | Everyone | Cancel the current flow |
| `/bookings` | Admin | Latest 10 bookings |
| `/leads` | Admin | Latest 10 questions/leads |
| `/cancel_booking <id>` | Admin | Cancel a booking and free its slot |

Example: `/cancel_booking 12`

## 🛠 Customization

Everything below is in `config.py`:

- **Services:** edit the `SERVICES` tuple (`key`, `name`, `description`, `duration`, `price`). These are sample services.
- **Business text:** `BUSINESS_NAME`, `BUSINESS_HOURS`, `CONTACT_INFO`.
- **FAQ:** edit the `FAQ` tuple of `(question, answer)` pairs.
- **Time slots:** edit `TIME_SLOTS` (format `HH:MM`).
- **Dates:** `BOOKING_START_OFFSET_DAYS` (1 = starting tomorrow, 0 = today) and `BOOKING_DAYS_AHEAD` (number of days offered).
- **Messages and button labels:** all `TEXT_*` and `BTN_*` constants (HTML formatting is supported in messages).

Note: bookings store the service *name*, so renaming a service does not retroactively block old slots.

## ☁️ Deployment Notes (Railway / Render)

- Run as a **worker / background service** with start command `python bot.py` (no web port needed; long polling).
- Set `BOT_TOKEN`, `ADMIN_CHAT_ID` and `DATABASE_PATH` as environment variables in the dashboard, not in files.
- **SQLite needs persistent storage.** Container filesystems are ephemeral: without a mounted volume/disk, bookings and leads are lost on every deploy or restart. Mount a persistent volume (Railway Volume / Render Disk) and point `DATABASE_PATH` to it, e.g. `/data/bot.db`.
- Run only **one instance** at a time; two pollers with the same token conflict.
- For anything beyond a demo, consider PostgreSQL and persistent FSM storage (FSM state here is in memory and is lost on restart).

## 💼 Portfolio: Problems This Solves

- Customers book 24/7 without phone calls or back-and-forth messages
- No double-bookings thanks to database-level slot protection
- Owners get instant notifications with all details and a local record
- Common questions are answered automatically; unanswered ones become captured leads
- Easy to adapt to salons, repair shops, consultants, clinics, tutors, etc.

## ✅ Testing Checklist

- [ ] Bot exits with a clear message when `BOT_TOKEN` is missing or `ADMIN_CHAT_ID` is non-numeric
- [ ] `data/bot.db` is created on first run and is not tracked by Git
- [ ] `/start` shows welcome text and all 5 menu buttons
- [ ] Services screen shows 3 services with description, duration and price
- [ ] Full booking: service → date → time → name → phone (contact button) → confirm
- [ ] Booking with a manually typed phone number works; invalid name/phone is rejected
- [ ] Admin receives the booking notification; user receives the success message
- [ ] The same service/date/time is no longer offered to a second user
- [ ] Cancel works at every step (inline and reply-keyboard buttons)
- [ ] FAQ list, answers and Back buttons work
- [ ] Contact screen shows hours and contact text
- [ ] "Ask a question" saves a lead, notifies admin and confirms to the user
- [ ] `/bookings` and `/leads` work for admin and show a friendly error for others
- [ ] `/cancel_booking <id>` handles valid, missing, repeated and non-numeric IDs
- [ ] Restarting the bot keeps existing data

## 📄 License

Add your preferred license (e.g. MIT) before publishing.

