# MongoDB Admin User Setup Script

## Create Default Admin User

Run this in MongoDB shell or MongoDB Compass:

```javascript
// Switch to database
use fmcg_mastering

// Create ADMIN_USERS collection and add default admin
db.ADMIN_USERS.insertOne({
  email: "admin@fmcg.com",
  password: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfQPBya6xu",  // Admin@123
  name: "Admin User",
  role: "administrator",
  created_at: new Date(),
  last_login: null
})
```

## Default Credentials

- **Email:** `admin@fmcg.com`
- **Password:** `Admin@123`

## Add Additional Admin Users

To add more admin users, first hash the password using Python:

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("YourPassword123")
print(hashed)
```

Then insert into MongoDB:

```javascript
db.ADMIN_USERS.insertOne({
  email: "newadmin@fmcg.com",
  password: "PASTE_HASHED_PASSWORD_HERE",
  name: "New Admin",
  role: "administrator",
  created_at: new Date(),
  last_login: null
})
```

## Verify Admin Users

```javascript
// List all admin users
db.ADMIN_USERS.find({}, { password: 0 }).pretty()

// Count admin users
db.ADMIN_USERS.countDocuments()
```

## Security Notes

- ✅ Passwords are hashed with bcrypt (cost factor: 12)
- ✅ No plain text passwords stored
- ✅ JWT tokens expire in 24 hours
- ✅ No registration endpoint (admins added manually only)
- ⚠️ Change default password after first login
