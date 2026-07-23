# 📚 Book Review System
*A 4th Semester Project Submission*

The **Book Review System** is a responsive, web-based platform featuring a modern Glassmorphism UI design. It consists of a Django RESTful API backend communicating with a vanilla HTML5/CSS3/JavaScript frontend and backed by a MySQL database.

---

## 🌟 Key Features

### 👤 User Module
- **Security & Registration**: Create accounts securely with validation.
- **Token-Based Authentication**: Secure login using encrypted Django Timestamp signers (no session cookies, pure token authentication via headers).
- **Interactive Books Directory**: Search for books by title, author, or genre.
- **Detailed Book Reviews**: Rate books out of 5 and write review comments.
- **Review CRUD Actions**: Edit or delete your own reviews.
- **User Profile Dashboard**: View personal statistics (total reviews written, books read, average rating given, helpful votes mock).

### 👑 Admin Module
- **Dynamic Analytics Dashboard**: Visual summary cards of books count, user count, review count, and reviews posted today.
- **Activity Log Feed**: Dynamic chronological feed of registrations and review postings.
- **Book Management**: Full CRUD actions for books (add, view, edit details, clear published dates, or delete books).
- **User Moderation**: Manage system users (view profile stats, suspend/activate accounts, delete users).
- **Review Moderation**: Moderate reviews (list reviews, read full comments, delete inappropriate or spam reviews).

---

## 🛠️ Technology Stack
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism layout, modern color palette), ES6 JavaScript (asynchronous `fetch` APIs).
- **Backend**: Django 5.x, custom Python middleware, Token Token-auth mechanisms, PyMySQL connection adapter, CORS headers.
- **Database**: MySQL.

---

## 🚀 Setting Up the Project

### Prerequisites
1. **Python 3.10+** installed on your system.
2. **MySQL Server** running (e.g., via XAMPP, WAMP, or standalone MySQL).
3. **Visual Studio Code** (recommended editor).

---

### Step 1: Database Setup
1. Open your MySQL client (or PHPMyAdmin) and create a database named `book_review_system`:
   ```sql
   CREATE DATABASE book_review_system;
   ```
2. Import the database schema from the provided `users.sql` file:
   ```bash
   mysql -u root -p book_review_system < users.sql
   ```
   *(Note: The default database configurations in `Backend/book_review/settings.py` are set to `USER: 'root'` and `PASSWORD: 'root'` on `127.0.0.1:3306`)*

---

### Step 2: Backend Setup
1. Open a terminal in the `Backend` directory.
2. The virtual environment `.venv` is pre-configured. Activate it:
   - **Windows (PowerShell)**: `.\.venv\Scripts\Activate.ps1`
   - **Windows (CMD)**: `.\.venv\Scripts\activate.bat`
   - **macOS/Linux**: `source .venv/bin/activate`
3. Run migrations to initialize default tables:
   ```bash
   python manage.py migrate
   ```
4. Start the Django API server:
   ```bash
   python manage.py runserver 8000
   ```

---

### Step 3: Frontend Setup
1. Open a new terminal in the `frontend` directory.
2. Start a local HTTP server to host the static files:
   ```bash
   python -m http.server 8080
   ```
3. Open your browser and navigate to:
   ```text
   http://localhost:8080/user/index.html
   ```

---

## ⚡ 1-Click Launch via Visual Studio Code
If you are running the project in **Visual Studio Code**:
1. Open the project folder `Book Review` in VS Code.
2. Go to the **Run and Debug** tab (or press `Ctrl+Shift+D`).
3. Select **"Launch BookReview App (Both)"** from the dropdown menu.
4. Press the green **Play** button (or press `F5`).
*VS Code will automatically spin up the Django backend (port 8000) and the Frontend web server (port 8080) simultaneously.*

---

## 🔑 Default Test Accounts
Use these pre-configured credentials to evaluate the system (passwords are set to `password123`):

| Role | Email | Password | Description |
|---|---|---|---|
| **Admin** | `admin@example.com` | `password123` | Full administrative privileges to dashboard, user control, review deletion. |
| **User** | `john@example.com` | `password123` | Standard user for browsing and leaving book reviews. |
| **User** | `jane@example.com` | `password123` | Standard user. |
