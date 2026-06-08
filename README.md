# Arnika - Comprehensive Martial Arts Club Management System 🥋

![Django](https://img.shields.io/badge/Django-6.0-green)
![Python](https://img.shields.io/badge/Python-3.14+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)

**Version:** 2.1  
**Date:** May 2026  
**Repository:** [github.com/4uth0r/FightClub](https://github.com/4uth0r/FightClub)

> 📖 [README in Persian (فارسی)](README-fa.md)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Installation](#installation)
- [User Roles](#user-roles)
- [Settings](#settings)
- [Demo](#demo)

---

## Overview

**Arnika** is a comprehensive web-based management system for martial arts clubs (Hapkido, Karate, Boxing, etc.). It enables complete management of students, classes, shifts, attendance, tuition fees, insurance, and parent communication.

### 🎯 Purpose
Replace paper-based and fragmented systems with a unified, fast, and reliable platform for daily club operations.

---

## Features

### 👥 Student Management
- **Registration** with National ID (unique) and Phone (shareable for siblings)
- **Complete Profile:** name, national ID, birth date (Jalali), address, belt, club, sport
- **Photo upload** by managers
- **Parent contacts:** multiple numbers with labels (father, mother, emergency)
- **Soft Delete** with recovery option
- **Search & Filter:** by name, club, sport, belt, insurance status

### 🏢 Club Management
- **Provinces & Cities:** hierarchical management (full CRUD)
- **Clubs:** create, edit, deactivate, view details
- **Coaches:** assign coaches to clubs with roles (manager/instructor/assistant)
- **Sports:** define various martial arts (Hapkido, Boxing, Karate)

### 📅 Classes & Shifts
- **Classes:** grouped by club, sport, and gender (Male/Female/Mixed)
- **Shifts:** define weekdays, start and end times
- **Enrollment:** register students in shifts with date and tuition fee
- **Hard Delete:** remove incorrect enrollments completely

### ✅ Attendance
- **Daily check-in** with shift selection
- **Custom date** for recording and editing
- **Warning icon** for previous session absence
- **Monthly history** with Jalali calendar (Desktop: table, Mobile: cards)
- **Filter:** year, month, shift, student

### 📊 Absence Tracking
- **Consecutive absences:** display number of missed sessions
- **Direct call button** to parents
- **Contact modal:** show all parent numbers with labels
- **Last attendance and absence** in card

### 💰 Financial Management
- **Tuition:** monthly recording with amount and date
- **Payment history** in student profile
- **Debtor icon** (⚠️) on student names
- **Alert** on detail page
- **Income & Expenses** (separate management)
- **Financial report** (total income - expenses = balance)

### 🛡️ Insurance
- **Register & renew** insurance with Jalali dates
- **Insurance history**
- **Status display:** active (remaining days), expired (red)
- **Warning** in profile and student list

### 📨 Internal Messaging
- **Inbox & Sent**
- **New message** to any user
- **Bulk message** to students, coaches, managers
- **Reply & Thread** view
- **Read/Unread status**

### 👑 User Roles
- **Super Manager:** full access to all sections
- **Club Manager:** manage own club, coaches, students
- **Student:** view profile, attendance history, payments

### 🎨 User Interface
- **Dark & Light theme** (toggle button)
- **Fully Responsive** (Mobile-First Design)
- **Select2** for searchable dropdowns
- **Toast** notifications
- **Glass-modal** forms
- **HTMX** for live updates (attendance)
- **Bootstrap 5 RTL** fully Persian

### ⚙️ Settings
- **Logo & Organization Name**
- **Phone & Central Address**
- **Social Networks** (add, edit, delete)
- **Content:** About Us, Membership Terms, Working Hours

---

## Project Structure
FightClub/
├── apps/
│   ├── accounts/      # Users, authentication, messages
│   ├── clubs/         # Provinces, cities, clubs, coaches, sports
│   ├── students/      # Students, classes, shifts, attendance, insurance
│   ├── finance/       # Tuition, income, expenses, reports
│   └── core/          # Site settings, social networks
├── templates/         # HTML templates
│   ├── partials/      # Sidebar, menu, modals, toast
│   ├── accounts/      # Landing, login, dashboard, profile
│   ├── students/      # Students, classes, attendance
│   ├── clubs/         # Clubs, coaches, provinces
│   ├── finance/       # Financial
│   └── core/          # Settings
├── static/
│   ├── css/           # app.css
│   ├── js/            # app.js
│   └── vendors/       # Bootstrap, Bootstrap Icons, Animate.css, HTMX, Select2
├── media/             # Uploaded files
├── config/            # Django settings
├── requirements.txt
└── manage.py

---

## Technologies

| Technology | Usage |
|------------|-------|
| **python 3.12+** | Programming Language |
| **django 6.0** | Main Framework |
| **pillow** | Image Processing |
| **django-jalali** | Jalali Calendar |
| **django-environ** | Environment Variables |
| **SQLite** | Database (upgradable to PostgreSQL) |
| **Bootstrap 5.3 RTL** | UI Framework |
| **Bootstrap Icons** | Icons |
| **Select2** | Searchable Dropdowns |
| **Animate.css** | Animations |
| **jQuery** | Select2 Dependency |

---

## Installation

### Prerequisites
- Python 3.10+
- pip or uv
- Git

### Steps

```bash
# Clone the repository
git clone https://github.com/4uth0r/FightClub.git
cd FightClub

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run
python manage.py runserver

Default Login

    URL: http://localhost:8000

    Login: with National ID and Password

    Admin Panel: http://localhost:8000/admin

User Roles
👑 Super Manager

    Full access to all sections

    Manage provinces, cities, clubs

    Assign coach and manager roles

    View all students, classes, financial data

🏢 Club Manager

    Manage own club

    Register and manage students

    Attendance, classes, shifts

    View club financial data

👤 Student

    View own profile

    Attendance history

    Tuition payment

    Messages

Settings

Settings section (Super Manager only) includes:

    Organization Name - displayed across all pages

    Logo - image upload

    Phone & Address - contact information

    Working Hours

    About Us - introduction text

    Membership Terms - rules

    Social Networks - add/remove links (Instagram, Telegram, WhatsApp, YouTube, Website)

License

MIT License - Free for commercial and personal use.
Developer

Hamid Reza Bardarani

Full Stack Developer
Email: [little4uth0r@gmail.com]
GitHub: github.com/4uth0r

Built with ❤️ for the Martial Arts Community
