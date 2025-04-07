# Testing Guide for VirtuAid

## User Creation in Tests

VirtuAid uses a custom user model with three specific roles:
- SuperAdmin: Use `InterfaceUser.objects.create_superadmin(...)`
- Admin: Use `InterfaceUser.objects.create_admin(...)`
- Manager: Use `InterfaceUser.objects.create_manager(...)`

**Do NOT use `User.objects.create_user()` - it is not supported.**

### Example:

```python
from authentication.models import InterfaceUser
from authentication.test_utils import VirtuAidTestCase

class MyTestCase(VirtuAidTestCase):
    def setUp(self):
        # Create users with proper role-based methods
        self.superadmin = InterfaceUser.objects.create_superadmin(
            email="superadmin@example.com",
            name="Super Admin",
            password="password123"
        )
        
        self.admin_user = InterfaceUser.objects.create_admin(
            email="admin@example.com",
            name="Admin User",
            password="password123"
        )
        
        self.manager_user = InterfaceUser.objects.create_manager(
            email="manager@example.com",
            name="Manager User",
            password="password123"
        )
```

## Fixing Database Connection Issues

To prevent the "database is being accessed by other users" error, all test classes should extend from `VirtuAidTestCase` instead of Django's `TestCase`:

```python
from authentication.test_utils import VirtuAidTestCase

class MyTestCase(VirtuAidTestCase):
    # Your test code here
```
