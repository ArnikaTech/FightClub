"""Shared tenant and branch access rules for club-scoped data."""
from django.db.models import Q

from .models import Club


def managed_clubs_for(user):
    """Branches a user may administer; platform owners retain support access."""
    if not user.is_authenticated:
        return Club.objects.none()
    if user.is_super_manager:
        return Club.objects.all()

    return Club.objects.filter(
        Q(
            organization__memberships__user=user,
            organization__memberships__is_active=True,
            organization__memberships__role='manager',
            organization__is_active=True,
        )
        | Q(
            memberships__user=user,
            memberships__is_active=True,
            memberships__role='manager',
            organization__is_active=True,
        )
    ).distinct()


def teaching_clubs_for(user):
    """Branches where the user has an active instructor/assistant membership."""
    if not user.is_authenticated:
        return Club.objects.none()
    if user.is_super_manager:
        return Club.objects.all()
    return Club.objects.filter(
        memberships__user=user,
        memberships__is_active=True,
        memberships__role__in=('instructor', 'assistant'),
        organization__is_active=True,
    ).distinct()


def can_manage_clubs(user):
    return user.is_authenticated and (user.is_super_manager or managed_clubs_for(user).exists())
