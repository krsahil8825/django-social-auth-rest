from django.contrib import admin
from django.contrib.auth import get_user_model

from .conf import ENABLED_PROVIDERS
from .models import SocialAccountLinked, SocialAccountProvider


User = get_user_model()


def user_admin_supports_autocomplete():
    """
    Return True if the registered User admin supports autocomplete.
    """

    try:
        user_admin = admin.site.get_model_admin(User)
    except admin.sites.NotRegistered:
        return False

    return bool(getattr(user_admin, "search_fields", None))


class ProviderFilter(admin.SimpleListFilter):
    title = "Provider"
    parameter_name = "provider"

    def lookups(self, request, model_admin):
        return [
            (
                choice.value,
                choice.label,
            )
            for choice in SocialAccountProvider
            if choice.value in ENABLED_PROVIDERS
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(provider=self.value())

        return queryset


@admin.register(SocialAccountLinked)
class SocialAccountLinkedAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_name",
        "user_email",
        "provider",
        "linked_at",
    )

    list_filter = (
        ProviderFilter,
        "linked_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "provider_user_id",
    )

    ordering = ("-linked_at",)

    list_per_page = 20

    list_select_related = ("user",)

    readonly_fields = (
        "provider_user_id",
        "linked_at",
    )

    if user_admin_supports_autocomplete():
        autocomplete_fields = ("user",)

    @admin.display(description="User Email", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description="User Name", ordering="user__username")
    def user_name(self, obj):
        return obj.user.username
