from django.contrib import admin

# Register your models here.


# class UserAdmin(AuthUserAdmin):
#     add_form = MyUserCreationForm
#     form = MyUserChangeForm
#     list_display = ['full_name', 'username', 'is_superuser', 'is_active']
#     list_display_links = ['username']
#     ordering = ['last_name', 'first_name']
#     prepopulated_fields = {'username': ['first_name', 'last_name']}
#     add_fieldsets = [
#         (None, {
#             'classes': ['wide'],
#             'fields': ['first_name', 'last_name', 'username', 'email']})]
#
#     def has_delete_permission(self, request, obj=None):
#         return False
#
#     def get_actions(self, request):
#         actions = super().get_actions(request)
#         if 'delete_selected' in actions:
#             del actions['delete_selected']
#         return actions
#
#     def full_name(self, obj):
#         return ' '.join((obj.last_name.upper(), obj.first_name.capitalize()))
#     full_name.short_description = 'Nom et prénom'
#
#
# admin.site.register(User, UserAdmin)
