from django.contrib import admin

from apps.core.models import ConfigurationAutoPilot, JournalAuditAutoPilot

admin.site.site_header = "AutoPilot"
admin.site.site_title = "AutoPilot"
admin.site.index_title = "Pilotage de l'auto-école"


@admin.register(ConfigurationAutoPilot)
class ConfigurationAutoPilotAdmin(admin.ModelAdmin):
    list_display = ["etablissement", "devise", "fuseau_horaire", "duree_lecon_defaut_minutes"]
    list_filter = ["devise", "fuseau_horaire"]
    search_fields = ["etablissement__nom"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(JournalAuditAutoPilot)
class JournalAuditAutoPilotAdmin(admin.ModelAdmin):
    list_display = ["created_at", "action", "categorie", "utilisateur", "etablissement"]
    list_filter = ["action", "categorie", "created_at"]
    search_fields = ["action", "utilisateur__username", "entite_type"]
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in JournalAuditAutoPilot._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(admin.models.LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ["action_time", "user", "content_type", "object_repr", "action_flag"]
    list_filter = ["action_flag", "content_type"]
    search_fields = ["object_repr", "change_message"]
    date_hierarchy = "action_time"
    readonly_fields = [f.name for f in admin.models.LogEntry._meta.fields]
    list_select_related = ["user", "content_type"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
