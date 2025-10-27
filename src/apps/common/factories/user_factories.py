import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    is_staff = False
    is_superuser = False
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "password123"
        self.set_password(password)
        if create:
            self.save()
