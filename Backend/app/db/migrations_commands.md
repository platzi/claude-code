# Platziflix Database Migrations

This document contains all the essential Alembic commands for managing database migrations in the Platziflix project.

## 📋 **Prerequisites**

- Make sure you're in the `/app` directory when running Alembic commands
- Ensure the database is running and accessible
- Configuration is located in `alembic.ini`

## 🔧 **Basic Migration Commands**

### Check Current Migration Status
```bash
cd /app && alembic current
```

### Show Migration History  
```bash
cd /app && alembic history --verbose
```

### Create New Migration (Manual)
```bash
cd /app && alembic revision -m "Description of changes"
```

### Create New Migration (Auto-generate)
```bash
cd /app && alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations (Upgrade to Latest)
```bash
cd /app && alembic upgrade head
```

### Apply Specific Migration
```bash
cd /app && alembic upgrade <revision_id>
```

### Rollback to Previous Migration
```bash
cd /app && alembic downgrade -1
```

### Rollback to Specific Migration
```bash
cd /app && alembic downgrade <revision_id>
```

### Rollback All Migrations
```bash
cd /app && alembic downgrade base
```

## 📊 **Information Commands**

### Show Pending Migrations
```bash
cd /app && alembic heads
```

### Show Current Branches
```bash
cd /app && alembic branches
```

### Show Migration Details
```bash
cd /app && alembic show <revision_id>
```

## 🎯 **Project-Specific Commands**

### Initial Database Setup (First Time)
```bash
cd /app && alembic upgrade head
```

### Reset Database (Development Only)
```bash
cd /app && alembic downgrade base
cd /app && alembic upgrade head
```

### Apply Migrations + Seed Data
```bash
cd /app && alembic upgrade head
cd /app && python db/seed.py
```

### Clear All Data (Keep Schema)
```bash
cd /app && python db/seed.py clear
```

## 🗃️ **Current Database Schema**

The initial migration (`d18a08253457`) creates the following tables:

### **teachers**
- `id` (Primary Key)
- `name` (String, required)
- `email` (String, unique, required)
- `created_at`, `updated_at`, `deleted_at` (Timestamps)

### **courses**
- `id` (Primary Key)
- `name` (String, required)
- `description` (Text, required)
- `thumbnail` (String, URL)
- `slug` (String, unique, required)
- `created_at`, `updated_at`, `deleted_at` (Timestamps)

### **lessons**
- `id` (Primary Key)
- `course_id` (Foreign Key → courses.id)
- `name` (String, required)
- `description` (Text, required)
- `slug` (String, required)
- `video_url` (String, URL)
- `created_at`, `updated_at`, `deleted_at` (Timestamps)

### **course_teachers** (Association Table)
- `course_id` (Foreign Key → courses.id)
- `teacher_id` (Foreign Key → teachers.id)
- Composite Primary Key

## 🚀 **Quick Start Guide**

1. **First time setup:**
   ```bash
   cd /app && alembic upgrade head
   cd /app && python db/seed.py
   ```

2. **After making model changes:**
   ```bash
   cd /app && alembic revision --autogenerate -m "Your change description"
   cd /app && alembic upgrade head
   ```

3. **If something goes wrong:**
   ```bash
   cd /app && alembic downgrade -1  # Go back one migration
   # Fix the issue, then
   cd /app && alembic upgrade head
   ```

## ⚠️  **Important Notes**

- Always backup your database before running migrations in production
- Review auto-generated migrations before applying them
- Use descriptive messages for migration commits
- Test migrations on development environment first
- The `deleted_at` field enables soft deletes across all entities
- All slugs should be URL-friendly and unique within their scope

## 🐛 **Troubleshooting**

### Connection Error
```bash
# Check if database is running
# Verify connection string in alembic.ini
# Ensure database exists
```

### Migration Conflicts
```bash
cd /app && alembic merge -m "Merge conflicting migrations"
cd /app && alembic upgrade head
```

### Reset Everything (Development Only)
```bash
cd /app && alembic downgrade base
cd /app && alembic upgrade head
cd /app && python db/seed.py
``` 