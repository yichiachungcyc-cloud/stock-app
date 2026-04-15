# 📊 Stock Investment Tracker App

A lightweight web application for recording, editing, and managing stock transactions, built with a simple and scalable architecture using Streamlit and Google Sheets.
---
## 🚀 Overview

This project is designed as a **practical investment tracking tool** that allows users to manage stock transactions in an intuitive interface, while leveraging cloud storage for persistence.

It demonstrates the ability to build a complete data-driven application, including UI, data processing, and external API integration.

---
## ✨ Key Features

* 🧾 **Transaction Recording**

  * Record BUY / SELL stock trades
  * Store stock ID, price, quantity, and notes

* ✏️ **Interactive Table Editing**

  * Edit transactions directly in the UI using an editable table
  * Toggle between view mode and edit mode

* 💾 **Cloud Data Storage**

  * Persist data using Google Sheets as a lightweight backend
  * Manual save control to prevent accidental overwrites

* 🔐 **Authentication System**

  * Simple login system using Streamlit secrets
  * Session-based access control

* 📊 **Portfolio Summary**

  * Total investment and sell tracking
  * Automatic calculation of transaction amounts

* 📈 **Real-Time Market Data**

  * Fetch live stock prices using yfinance
---
## 🏗️ Architecture
```
   id="arch1"
        User (Browser)
              │
              ▼
      Streamlit Application
              │
      ┌───────┴────────┐
      ▼                ▼
 Google Sheets     External API
   (Storage)        (Market Data)
---

## ⚙️ Tech Stack

* **Language**: Python
* **Framework**: Streamlit
* **Data Processing**: pandas
* **Cloud Storage**: Google Sheets (via gspread)
* **Market Data API**: yfinance

---
## 🔐 Security Considerations

* Credentials are securely managed using `.streamlit/secrets.toml`
* No sensitive information is exposed in the source code
* Google service account is used for controlled data access

---
## 💡 Design Highlights

* Designed with **dual-mode editing** to avoid unintended data overwrite
* Uses **Google Sheets as a serverless backend**, reducing infrastructure complexity
* Implements **clean data pipeline**:
* Data retrieval → Cleaning → Type conversion → UI rendering

---
## 📸 Demo
![App Screenshot](screenshot.png)

---
## 📦 Installation & Run
```bash id="run1"
pip install -r requirements.txt
streamlit run app.py
```

---
## 🎯 What This Project Demonstrates

* Building a complete **end-to-end application** using Python
* Designing **interactive user interfaces**
* Integrating **cloud-based data storage**
* Handling **real-time external data**
* Implementing **basic authentication and state management**

---
## 🔮 Future Improvements

* Multi-user data isolation
* Database integration (PostgreSQL / Firebase)
* Advanced portfolio analytics
* Mobile-friendly UI improvements
---

## 👤 Author
Alison Chung
