import env

from ..constants import SYSTEM_ACTOR
from ..models import User


def ensure_root_user() -> None:
    username = env.ROOT_USERNAME
    password = env.ROOT_PASSWORD
    user = User.all_objects.filter(username=username).first()
    if user is None:
        User.objects.create_superuser(
            username=username,
            password=password,
            performed_by=SYSTEM_ACTOR,
        )
        return
    if user.is_deleted:
        user.restore()
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.save(performed_by=SYSTEM_ACTOR)
