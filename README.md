# Azebra Donation Telegram Bot

A production-ready Telegram bot developed to manage donations for a Minecraft server.  
The bot supports manual card payments with admin moderation and automated Telegram Stars payments, includes a referral bonus system, and is fully deployed in the cloud with persistent storage.

---

## 🚀 Features

- 💰 **Donation system**
  - Manual card payments with receipt verification
  - Telegram Stars payments (in-app purchases)

- 🧮 **Automatic bonus calculation**
  - Referral-based cumulative bonus system
  - Dynamic percentage calculation with upper limit

- 👥 **Referral system**
  - Personal invite links
  - Cumulative donations tracking

- 📜 **Rules & compliance system**
  - Mandatory rules acceptance before donating
  - Admin ability to reset or revoke access

- 🔐 **Admin moderation**
  - Accept / reject donations
  - Reject with custom reason
  - User payment locking / unlocking

- 🧾 **Minecraft integration**
  - Automatic generation of ready-to-use console commands

- 🌍 **Multilingual support**
  - English
  - Russian
  - Azerbaijani

- ☁️ **Cloud deployment**
  - Hosted on Render (free tier)
  - 24/7 uptime using keep-alive mechanism
  - Health check endpoint

---

## 🧠 System Architecture

User

↓

Telegram Bot (python-telegram-bot, async)

↓

Donation Flow

├── 
Manual Card Payment (admin moderation)

├── 
Telegram Stars Payment (automatic)

↓

PostgreSQL (Neon)

↓

Admin Notification + Minecraft Console Command

---

## 🛠 Tech Stack

- **Language:** Python 3
- **Telegram Framework:** python-telegram-bot (async)
- **Async HTTP Server:** aiohttp
- **Database:** PostgreSQL (Neon)
- **DB Driver:** asyncpg
- **Hosting:** Render (cloud hosting)
- **Payments:** Telegram Stars API
- **Version Control:** GitHub

---

## 🗄 Database Design

The bot uses a persistent PostgreSQL database to store:

- Users and language preferences
- Donation history
- Pending payment requests
- Referral relationships
- Bonus calculation data
- Rules acceptance status
- Payment lock states
- Atomic counters for transaction tracking

This ensures full data consistency and reliability across restarts.

---

## 🔒 Security & Configuration

- All sensitive data is stored using **environment variables**
- No secrets are committed to the repository
- Admin-only actions are protected by access checks
- Payments require explicit confirmation or admin approval

Environment variables used:

BOT_TOKEN
ADMIN_ID
DATABASE_URL
MY_CARD
RENDER_URL

---

## ⚙️ Deployment

The bot is deployed on **Render** using GitHub integration.

Key deployment features:
- Health check endpoint (`/health`)
- Keep-alive task to prevent free-tier sleeping
- Asynchronous polling mode
- Automatic restart on failure

---

- 🎓 Why This Project Matters

This project demonstrates:

1.Asynchronous backend development

2.Real-world payment flow handling

3.Secure configuration management

4.Cloud deployment and uptime management

5.Database-driven business logic

6.Admin moderation workflows

7.It was developed as a real production system for a live Minecraft server community.

---

## 🤖 Live Bot
Telegram: https://t.me/azebradonate_bot
