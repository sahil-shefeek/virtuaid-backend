import uuid
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.conf import settings
from faker import Faker
from datetime import date, timedelta
from random import choice, randint
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files import File
import os
from residents.models import Associates
from carehomes.models import CareHomes
from carehomemanagers.models import CarehomeManagers
from feedbacks.models import Feedback
from reports.models import Reports

fake = Faker()
User = get_user_model()
DEFAULT_PASSWORD = 'Password@123'  # Alternatively fake.password() for a random one.


class Command(BaseCommand):
    help = 'Fill the database with mock data for CareHomes, Associates, Feedback, and Reports models'

    def create_mock_care_homes(self, number, create_new_managers=True):
        for _ in range(number):
            manager_name = fake.name()
            manager_email = fake.email()
            manager_password = DEFAULT_PASSWORD
            care_home_name = fake.company()
            admin_group = Group.objects.get(name='Admin')
            admin_user = choice(User.objects.filter(groups=admin_group))

            care_home = CareHomes.objects.create(
                name=care_home_name,
                address=fake.address(),
                code=care_home_name[0:3] + uuid.uuid4().hex[0:3],
                admin=admin_user
            )

            if create_new_managers:
                manager_user = User.objects.create_manager(
                    email=manager_email, name=manager_name, password=manager_password)
                try:
                    CarehomeManagers.objects.create(
                        carehome=care_home,
                        manager=manager_user,
                    )
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Could not create manager: {e}'))
            else:
                manager_group = Group.objects.get(name='Manager')
                potential_managers = User.objects.filter(groups=manager_group)
                manager_user = None
                for user in potential_managers:
                    if not CarehomeManagers.objects.filter(manager=user).exists():
                        manager_user = user
                        break
                if not manager_user:
                    self.stdout.write(
                        self.style.ERROR('No available manager found who is not already managing a care home.'))
                    continue

                if CarehomeManagers.objects.filter(carehome=care_home).count() >= 5:
                    self.stdout.write(self.style.ERROR(f'Care home {care_home.name} already has 5 managers.'))
                    continue
                else:
                    try:
                        CarehomeManagers.objects.create(
                            carehome=care_home,
                            manager=manager_user,
                        )
                    except ValidationError as e:
                        self.stdout.write(self.style.ERROR(f'Could not create manager: {e}'))

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created care home {care_home.name} with admin {admin_user.name} '
                    f'and manager {manager_user.name} ({manager_user.email})'
                )
            )

    def handle(self, *args, **options):
        self.stdout.write(self.style.ERROR(
            "***** Warning! *****\n\nMockify hasn't been updated to account for latest database changes. "
            "Running this command may cause unintended behavior.\n\n"
            "You can you use 'ctrl + c' to terminate the script.\n\n"))
        # Create CareHomes
        add_new_homes = input("Do you want to add new CareHomes? (yes/no): ").lower().strip()
        if add_new_homes not in ['yes', 'y', 'no', 'n']:
            self.stdout.write(self.style.ERROR('Invalid input. Please enter either "yes" or "no".'))
            return

        num_new_homes = -1
        if add_new_homes == 'yes' or 'y':
            try:
                num_new_homes = int(input("How many new CareHomes do you want to add? "))
                if num_new_homes < 0:
                    raise ValueError("Number of new CareHomes must be a non-negative integer.")
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f'Invalid input: {e}'))
                return

            create_managers = (
                input(
                    f"Would you like to create additional manager accounts for the new care homes?"
                    f"(yes/no): ").lower().strip()
            )
            if create_managers not in ['yes', 'y', 'no', 'n']:
                self.stdout.write(self.style.ERROR('Invalid input. Please enter either "yes" or "no".'))
                return

            if create_managers == 'yes' or 'y':
                self.create_mock_care_homes(num_new_homes)
                self.stdout.write(self.style.SUCCESS(f'Successfully filled the database with {num_new_homes} homes.'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        'Skipping the creation of new manager accounts. Assigning existing managers instead.')
                )
                self.create_mock_care_homes(num_new_homes, create_new_managers=False)
                self.stdout.write(self.style.SUCCESS(f'Successfully filled the database with {num_new_homes} homes.'))

        else:
            self.stdout.write(
                self.style.SUCCESS('Skipping the creation of new CareHomes.')
            )

        carehomes = CareHomes.objects.all()

        add_new_associates = input("Do you want to add new Resident entries? (Yes/No): ").lower().strip()
        if add_new_associates not in ['yes', 'y', 'no', 'n']:
            self.stdout.write(self.style.ERROR('Invalid input. Please enter either "Yes" "(Y/y)" or "No" "(N/n)".'))
            return

        # Create new Associates for existing CareHomes
        if add_new_associates == 'yes' or 'y':
            try:
                num_new_associates = int(input("How many new Resident entries do you want to add? "))
                if num_new_associates < 0:
                    raise ValueError("Number of new Resident must be a non-negative integer.")
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f'Invalid input: {e}'))
                return

            for _ in range(num_new_associates):
                Associates.objects.create(
                    name=fake.name(),
                    date_of_birth=fake.date_of_birth(minimum_age=40, maximum_age=90),
                    care_home=choice(carehomes),
                    created_by=choice(User.objects.filter(groups=Group.objects.get(name='Manager'))),
                )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully filled the database with {num_new_associates} residents.'))

        associates = Associates.objects.all()
        add_new_feedbacks = input("Do you want to add new Feedback entries? (Yes/No): ").lower().strip()
        if add_new_feedbacks not in ['yes', 'y', 'no', 'n']:
            self.stdout.write(self.style.ERROR('Invalid input. Please enter either "Yes" "(Y/y)" or "No" "(N/n)".'))
            return

        if add_new_feedbacks == 'yes' or 'y':
            try:
                num_new_feedbacks = int(input("How many new Feedback entries do you want to add? "))
                if num_new_feedbacks < 0:
                    raise ValueError("Number of new Feedback entries must be a non-negative integer.")
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f'Invalid input: {e}'))
                return

            for _ in range(num_new_feedbacks):
                Feedback.objects.create(
                    associate=choice(associates),
                    session_date=date.today() - timedelta(days=randint(1, 30)),
                    session_duration=randint(30, 120),
                    vr_experience=choice(["PHYSICAL", "COGNITIVE", "MINDFULNESS"]),
                    engagement_level=randint(1, 5),
                    satisfaction=randint(1, 5),
                    physical_impact=randint(1, 5),
                    cognitive_impact=randint(1, 5),
                    emotional_response=choice([
                        "RELAXATION", "HAPPINESS", "EXCITED", "PASSIONATE", "JOYFUL", "RELIEVED", "CALM", "CONTENT",
                        "SATISFIED", "CONFIDENT", "PROUD", "HOPEFUL", "BRAVE", "PEACEFUL", "SURPRISED", "ANGRY",
                        "ANNOYED",
                        "ANXIOUS", "DISAPPOINTED", "DRAINED", "FRUSTRATED", "HOPELESS", "SAD", "SCARED", "WORRIED"
                    ]),
                    feedback_notes=fake.text(),
                )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully filled the database with {num_new_feedbacks} Feedback entries.'))

        add_new_reports = input("Do you want to add new Report entries? (Yes/No): ").lower().strip()
        if add_new_reports not in ['yes', 'y', 'no', 'n']:
            self.stdout.write(self.style.ERROR('Invalid input. Please enter either "Yes" "(Y/y)" or "No" "(N/n)".'))
            return

        if add_new_reports == 'yes' or 'y':
            try:
                num_new_reports = int(input("How many new Report entries do you want to add? "))
                if num_new_reports < 0:
                    raise ValueError("Number of new Report entries must be a non-negative integer.")
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f'Invalid input: {e}'))
                return

            for _ in range(num_new_reports):
                # Specify the path to the sample PDF file
                pdf_path = os.path.join(settings.BASE_DIR, 'dummyfiles', 'sample.pdf')

                with open(pdf_path, 'rb') as pdf_file:
                    Reports.objects.create(
                        associate=choice(associates),
                        report_month=date.today() - timedelta(days=randint(1, 30)),
                        description=fake.text(),
                        pdf=File(pdf_file, name=f'{uuid.uuid4()}.pdf')
                    )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully filled the database with {num_new_reports} Report entries.'))

        self.stdout.write(self.style.SUCCESS('Successfully filled the database with mock data.'))
