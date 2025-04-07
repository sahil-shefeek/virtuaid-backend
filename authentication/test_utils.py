from django.test import TestCase
from django.db import connections

class VirtuAidTestCase(TestCase):
    """
    Base test case for VirtuAid tests that ensures proper database connection cleanup
    """
    
    def tearDown(self):
        # Close DB connections to prevent "database is being accessed by other users" errors
        for conn in connections.all():
            conn.close()
        super().tearDown()
    
    @staticmethod
    def fix_user_creation(test_class, user_refs=None):
        """
        Helper method to update test references to use correct user model.
        Call this in setUp() of test classes that use User.objects.create_user.
        
        Example:
            def setUp(self):
                # normal setup code...
                self.fix_user_creation(self, ['superadmin', 'admin_user', 'manager_user', 'regular_user'])
        """
        from authentication.models import InterfaceUser
        test_class.User = InterfaceUser
        
        # Patch the model references if specific ones are provided
        if user_refs and isinstance(user_refs, list):
            for attr in user_refs:
                if hasattr(test_class, attr):
                    # Convert any existing User.objects.create_user references to use proper role methods
                    if attr == 'superadmin':
                        role_method = 'create_superadmin'
                    elif attr.startswith('admin'):
                        role_method = 'create_admin'
                    elif attr.startswith('manager'):
                        role_method = 'create_manager'
                    else:
                        role_method = 'create_user'
                    
                    # Update reference to use proper method
                    attr_val = getattr(test_class, attr)
                    if hasattr(attr_val, 'get_role_display'):
                        # This assumes your model has a role field or similar 
                        # that would return the appropriate role string
                        setattr(test_class, attr, getattr(InterfaceUser.objects, role_method)(
                            email=attr_val.email,
                            name=attr_val.name,
                            password='password123'  # You may need to adjust this
                        ))
