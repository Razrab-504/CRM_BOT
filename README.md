# 🤖 Telegram CRM Bot

A full-featured, asynchronous Telegram CRM system for managing orders and connecting clients with service providers/freelancers directly in Telegram.

---

## 📋 Overview

This Telegram bot automates two-sided business processes: finding service providers, order creation, and a feedback system with ratings and reviews. It is ideal for service marketplaces, freelance hubs, tutoring agencies, or service centers.

---

## ✨ Key Features

- 👥 **Dual Registration System:** Separate onboarding flows for Clients and Service Providers (Employees).
- 🔍 **Smart Search:** Filter service providers by branch/specialization and average rating.
- 📝 **Order Lifecycle Management:** Complete flow from order creation and contractor confirmation to order completion.
- ⭐ **Rating & Review System:** Clients can leave ratings (1–5) and feedback after order completion.
- 📊 **Provider Analytics:** Performance stats and history for contractors.
- 🔔 **Automated Notifications:** Instant alerts when order statuses change or new requests arrive.
- 🗄️ **Async Database Architecture:** High performance and non-blocking I/O using SQLAlchemy ORM.

---

## 🎯 Service Categories

- 💻 **IT** (Software Development, System Administration)
- 🎬 **Video Editing** (Post-production, Content Creation)
- 🏋️ **Personal Trainers** (Fitness, Sports)
- 📚 **Tutors** (Education, Language Teachers)
- 🎨 **Design** (Graphic Design, UX/UI)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **MySQL 8.0+**
- **Telegram Bot Token** (Get it from @BotFather)

### Installation

1. **Clone the repository:**
git clone https://github.com/Razrab-504/CRM_BOT.git
cd CRM_BOT

2. **Create and activate a virtual environment:**
python -m venv venv

# Linux / macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

3. **Install dependencies:**
pip install -r requirements.txt

4. **Set up the MySQL Database:**
Log in to your MySQL terminal:

CREATE DATABASE crm_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'bot_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON crm_bot.* TO 'bot_user'@'localhost';
FLUSH PRIVILEGES;

5. **Configure environment variables:**
Copy .env.example to .env:
cp .env.example .env

Fill in your .env configuration:
BOT_TOKEN=your_telegram_bot_token_here
DB_HOST=localhost
DB_PORT=3306
DB_USER=bot_user
DB_PASSWORD=your_secure_password
DB_NAME=crm_bot

6. **Initialize the Database:**
python src/create_database.py

7. **Run the Bot:**
python main.py

---

## 📁 Project Structure

CRM_BOT/
├── main.py                  # Entry point
├── config.py                # Configuration settings
├── requirements.txt         # Project dependencies
├── .env.example             # Environment variables template
├── README.md                # Project documentation
├── .gitignore               # Git ignore rules
│
└── src/
    ├── bot/
    │   ├── handlers/        # Bot handlers
    │   │   └── user/
    │   │       └── user_handlers.py  # User logic & FSM flows
    │   │
    │   └── kbd/             # Keyboards
    │       ├── admin_keyboard.py     # Admin keypads
    │       └── user_keyboard.py      # User keypads
    │
    ├── db/
    │   ├── crud/            # Database CRUD operations
    │   │   ├── __init__.py
    │   │   ├── client.py    # Client operations
    │   │   ├── employee.py  # Service provider operations
    │   │   ├── order.py     # Order operations
    │   │   └── review.py    # Review operations
    │   │
    │   └── models/          # SQLAlchemy ORM Models
    │       ├── __init__.py
    │       ├── client.py    # Client schema
    │       ├── employee.py  # Employee schema
    │       ├── order.py     # Order schema
    │       └── review.py    # Review schema
    │
    ├── base.py              # Declarative Base
    ├── config.py            # Main database config
    ├── create_database.py   # Database initialization script
    ├── enums.py             # Enums (Order statuses, Branches)
    └── session.py           # Async DB session setup

---

## 🗄️ Database Schema

### `employee` Table (Service Providers)
- `id` (PK)
- `telegram_user_id` (UNIQUE)
- `first_name`, `last_name`, `phone`, `birth_date`
- `branch` (ENUM: `IT`, `VIDEO_EDITING`, `TRAINER`, `TEACHER`, `DESIGN`)
- `rating` (Float: 0.00 - 5.00)
- `total_reviews` (Integer)
- `created_at` (Timestamp)

### `clients` Table (Customers)
- `id` (PK)
- `telegram_user_id` (UNIQUE)
- `first_name`, `last_name`, `phone`, `birth_date`
- `created_at` (Timestamp)

### `orders` Table
- `id` (PK)
- `client_id` (FK → `clients.id`)
- `employee_id` (FK → `employee.id`)
- `description` (Text)
- `price` (Decimal)
- `status` (ENUM: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)
- `created_at`, `finished_at` (Timestamp)

### `reviews` Table
- `id` (PK)
- `client_id` (FK → `clients.id`)
- `employee_id` (FK → `employee.id`)
- `order_id` (FK → `orders.id`)
- `rating` (Integer: 1–5)
- `comment` (Text)
- `created_at` (Timestamp)

---

## 🎮 How It Works

### For Clients:
1. Send `/start` → Select **"I am a Client"**.
2. Complete profile registration.
3. Tap **"🔍 Find Contractor"** → Select a category.
4. Choose a service provider → Send job description and details.
5. Wait for contractor approval.
6. Once work is finished → Tap **"Complete Order"** → Leave a review & score.

### For Contractors:
1. Send `/start` → Select **"I am a Provider"**.
2. Fill out profile details and choose a specialization.
3. Receive real-time notifications for incoming work requests.
4. Tap **"✅ Accept"** or **"❌ Reject"**.
5. Contact client via provided phone/Telegram handle.

---

## 🛠️ Tech Stack & Dependencies

- **Aiogram 3.x:** Asynchronous Telegram Bot API framework.
- **SQLAlchemy 2.x:** Modern Python SQL Toolkit & ORM.
- **MySQL 8.0+:** Relational database storage.
- **Alembic:** Database migration management.
- **python-dotenv:** Environment configuration loader.
- **asyncio:** Built-in Python library for concurrent programming.

### `requirements.txt`:
aiogram==3.4.1
SQLAlchemy==2.0.25
pymysql==1.1.0
cryptography==41.0.7
python-dotenv==1.0.0
alembic==1.13.1

---

## 🔐 Security Best Practices

- ✅ Environment variables (`.env`) for storing sensitive API keys and database passwords.
- ✅ SQL Injection protection out of the box via SQLAlchemy ORM.
- ✅ Input validation on registration steps.
- ⚠️ **Never commit your `.env` file to public repositories!**

---

## 🚧 Roadmap

- [ ] Web-based Admin Dashboard
- [ ] Payment Gateway Integration (Stripe / Telegram Payments)
- [ ] Multi-language Support (EN / RU / AZ)
- [ ] Export Reports (CSV / Excel)
- [ ] AI-assisted contractor recommendations

---

## 📝 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## 👨‍💻 Author

- **GitHub:** @Razrab-504
- **Telegram:** @motivator6438
- **Email:** mammedovibrahim38@gmail.com

---
*Made with ❤️ using Python & Aiogram 3*
