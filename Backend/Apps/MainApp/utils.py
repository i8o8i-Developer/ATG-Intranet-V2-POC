def is_user_allowed(user, allowed_groups):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name__in=allowed_groups).exists()


def search_user(queryset, keyword=""):
    if not keyword:
        return queryset
    return queryset.filter(username__icontains=keyword) | queryset.filter(email__icontains=keyword)