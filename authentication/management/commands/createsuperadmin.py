from django.core.management.base import BaseCommand
from authentication.models import InterfaceUser


class Command(BaseCommand):
    help = 'Create a new superadmin'

    def handle(self, *args, **options):
        name = input('Enter name for the superadmin user: ')
        email = input('Enter email for the superadmin user: ')
        password = input('Enter password for the superadmin user: ')

        try:
            superadmin_user = InterfaceUser.objects.create_superadmin(email, name, password)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Superadmin user {superadmin_user.name} ({superadmin_user.email}) created successfully'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superadmin user: {e}'))