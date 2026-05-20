# NyumbaDirectly — Backend Setup Guide

## Stack
- **Language**: Python 3.11+
- **Framework**: Django 5 + Django REST Framework
- **Database**: PostgreSQL
- **Auth**: JWT (phone number based)
- **SMS/WhatsApp**: Africa's Talking
- **Payments**: M-Pesa Daraja API (STK Push)
- **Hosting**: Railway / Render (recommended)

---

## 1. Install Prerequisites

```bash
# Install Python (if not installed)
# https://www.python.org/downloads/

# Install PostgreSQL
# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib

# Mac:
brew install postgresql
```

---

## 2. Clone & Setup

```bash
# Navigate to project folder
cd nyumba-backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your actual values
nano .env   # or use any editor
```

**Key values to set in `.env`:**
- `SECRET_KEY` → Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DB_PASSWORD` → Your PostgreSQL password
- `AT_API_KEY` → Africa's Talking API key (register at africastalking.com)
- `MPESA_*` → M-Pesa Daraja credentials (register at developer.safaricom.co.ke)

---

## 4. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE nyumba_db;"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Seed Nairobi location data
python manage.py seed_locations

# Create admin account
python manage.py createsuperuser
# Enter phone number: +254712000000
# Enter full name: Admin
# Enter password: (your choice)
```

---

## 5. Run the Server

```bash
# Development server
python manage.py runserver

# API is now at: http://localhost:8000/api/
# Admin panel:   http://localhost:8000/admin/
# API Docs:      http://localhost:8000/api/docs/
```

---

## API Endpoints Summary

### Auth (`/api/auth/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register/tenant/` | Register tenant |
| POST | `/register/landlord/` | Register landlord |
| POST | `/login/` | Login → returns JWT tokens |
| POST | `/logout/` | Blacklist refresh token |
| POST | `/otp/send/` | Send OTP to phone |
| POST | `/otp/verify/` | Verify OTP |
| GET/PATCH | `/profile/` | View/update profile |
| GET/PATCH | `/profile/landlord/` | Landlord profile |
| POST | `/profile/upload-id/` | Upload national ID |

### Listings (`/api/listings/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Browse all verified listings |
| GET | `/<id>/` | View single listing |
| POST | `/<id>/contact/` | Track contact click |
| GET | `/my/` | My listings (landlord) |
| POST | `/create/` | Create listing (landlord) |
| PUT/PATCH | `/<id>/edit/` | Edit listing |
| POST | `/<id>/taken/` | Mark as taken |
| DELETE | `/<id>/delete/` | Delete listing |
| POST | `/<id>/photos/` | Upload photo |
| POST | `/<id>/save/` | Save/unsave listing |
| GET | `/saved/` | My saved listings |
| POST | `/<id>/report/` | Report fake listing |
| GET | `/estates/` | Search estates |
| GET | `/counties/` | List counties |

**Search & Filter params:**
```
?search=rongai
?min_rent=5000&max_rent=15000
?house_type=1br
?bedrooms=2
?estate=Rongai
?town=Nairobi
?water_included=true
?ordering=-rent_monthly
```

### Verification (`/api/verification/`)
| Method | Endpoint | Who |
|--------|----------|-----|
| GET | `/queue/` | Admin — see pending verifications |
| POST | `/<id>/assign/` | Admin — assign to field agent |
| POST | `/<id>/report/` | Field agent — submit field report |
| POST | `/<id>/photos/` | Field agent — upload visit photos |
| POST | `/<id>/approve/` | Admin — approve listing → goes LIVE |
| POST | `/<id>/reject/` | Admin — reject with reason |
| GET | `/listing/<listing_id>/status/` | Landlord — check status |

### Payments (`/api/payments/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Payment history |
| POST | `/initiate/` | Initiate M-Pesa STK push |
| POST | `/mpesa/callback/` | M-Pesa webhook (Safaricom calls this) |
| GET | `/<id>/` | Payment detail |

**Payment types:**
- `listing_fee` — KES 500 per listing
- `listing_fee_premium` — KES 2,000 per listing
- `subscription` — KES 3,000/month (unlimited listings)
- `featured` — KES 1,000 featured boost (14 days)

---

## 6. Admin Panel

Access at `/admin/` with your superuser credentials.

**Key actions available:**
- ✅ Approve listings (mark as verified + live)
- ❌ Reject listings with reason
- ⭐ Feature listings for 14 days
- 🔍 Manage verification queue
- 👤 Verify landlord IDs
- 📊 View all payments & receipts
- 🚩 Investigate reports

---

## 7. Deploy to Railway (Free Tier Available)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Add PostgreSQL
railway add

# Set environment variables
railway variables set SECRET_KEY=... DB_HOST=... (etc)

# Deploy
railway up
```

Or use **Render.com** — also free tier, excellent for Django.

---

## Architecture Flow

```
Landlord submits listing
        ↓
Signal auto-creates VerificationRequest (status: queued)
        ↓
Landlord pays listing fee via M-Pesa STK Push
        ↓
M-Pesa callback confirms payment
        ↓
Admin assigns to field agent
        ↓
Field agent visits house → submits report + photos
        ↓
Admin approves → Listing goes LIVE with ✅ Verified badge
        ↓
Tenants browse, contact landlord directly
```

---

## Tech Contacts for Kenya Setup
- **Africa's Talking**: africastalking.com (SMS & WhatsApp, free sandbox)
- **M-Pesa Daraja**: developer.safaricom.co.ke (free sandbox with test STK push)
- **PostgreSQL on Railway**: free 500MB included

---

Built for Kenya 🇰🇪 by NyumbaDirectly
