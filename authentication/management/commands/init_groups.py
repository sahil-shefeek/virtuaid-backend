from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Create a new group and add users to it'

    def handle(self, *args, **options):
        superadmin_group, created = Group.objects.get_or_create(name='SuperAdmin')
        if created:
            self.stdout.write(self.style.SUCCESS('SuperAdmin user group initialised successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS('SuperAdmin user group already exists.'))
        admin_group, created = Group.objects.get_or_create(name='Admin')
        if created:
            self.stdout.write(self.style.SUCCESS('Admin user group initialised successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS('Admin user group already exists.'))
        manager_group, created = Group.objects.get_or_create(name='Manager')
        if created:
            self.stdout.write(self.style.SUCCESS('Manager group initialised successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS('Manager group already exists.'))
            superadmin_group.permissions.add(
                Permission.objects.get(codename='add_interfaceuser'),
                Permission.objects.get(codename='change_interfaceuser'),
                Permission.objects.get(codename='view_interfaceuser'),
                Permission.objects.get(codename='add_resident'),
                Permission.objects.get(codename='change_resident'),
                Permission.objects.get(codename='view_resident'),
                Permission.objects.get(codename='add_carehomes'),
                Permission.objects.get(codename='change_carehomes'),
                Permission.objects.get(codename='view_carehomes'),
                Permission.objects.get(codename='add_carehomemanagers'),
                Permission.objects.get(codename='change_carehomemanagers'),
                Permission.objects.get(codename='delete_carehomemanagers'),
                Permission.objects.get(codename='view_carehomemanagers'),
                Permission.objects.get(codename='view_feedback'),
                Permission.objects.get(codename='view_reports'),

            )

        admin_group.permissions.add(
            Permission.objects.get(codename='add_interfaceuser'),
            Permission.objects.get(codename='change_interfaceuser'),
            Permission.objects.get(codename='view_interfaceuser'),
            Permission.objects.get(codename='delete_interfaceuser'),
            Permission.objects.get(codename='add_resident'),
            Permission.objects.get(codename='change_resident'),
            Permission.objects.get(codename='delete_resident'),
            Permission.objects.get(codename='view_resident'),
            Permission.objects.get(codename='view_resident'),
            Permission.objects.get(codename='view_carehomes'),
            Permission.objects.get(codename='add_carehomemanagers'),
            Permission.objects.get(codename='change_carehomemanagers'),
            Permission.objects.get(codename='delete_carehomemanagers'),
            Permission.objects.get(codename='view_carehomemanagers'),
            Permission.objects.get(codename='add_feedback'),
            Permission.objects.get(codename='view_feedback'),
            Permission.objects.get(codename='add_reports'),
            Permission.objects.get(codename='view_reports'),
        )

        manager_group.permissions.add(
            Permission.objects.get(codename='add_feedback'),
            Permission.objects.get(codename='view_feedback'),
            Permission.objects.get(codename='view_interfaceuser'),
            Permission.objects.get(codename='change_interfaceuser'),
            Permission.objects.get(codename='add_resident'),
            Permission.objects.get(codename='change_resident'),
            Permission.objects.get(codename='delete_resident'),
            Permission.objects.get(codename='view_resident'),
            Permission.objects.get(codename='view_reports'),
        )

        self.stdout.write(self.style.SUCCESS('User-group permissions initialised successfully.'))
