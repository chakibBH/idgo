from django.contrib import admin
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter
from django.utils.html import format_html
from datetime import datetime

from .models import Order
from .actions import download_csv

# def send_email(modeladmin, request, queryset):
#     queryset.update(status='p')
# send_email.short_description = "Mark selected stories as published"


class OrderAdmin(admin.ModelAdmin):

    list_display = ('date', 'applicant', 'email', 'organisation', 'terr', 'status')

    # ajout de l'email de l'utilisateur
    def email(self, obj):
        return format_html('<a href=\"mailto:{0}\">{0}</a>'.format(obj.applicant.email))
    email.short_description = 'E-mail'

    # ajout du nom du territoire de compétences

    def terr(self, obj):
        return obj.organisation.jurisdiction
    terr.short_description = 'Territoire de compétences'

    # action d'export en csv
    actions = [download_csv]
    download_csv.short_description = "Exporter en CSV"

    # filter by year of the orders
    class YearListFilter(admin.SimpleListFilter):

        title = ('année de la demande')
        parameter_name = 'year'

        def lookups(self, _request, _model_admin):
            year = 2018
            years = []
            while datetime(year, 1, 1) < datetime.now():
                years.append(year)
                year += 1

            return [(year, str(year)) for year in years]

        def queryset(self, request, queryset):
            if self.value() is not None:
                return queryset.filter(date__year=self.value())

    list_filter = (('organisation', RelatedDropdownFilter), YearListFilter,)


admin.site.register(Order, OrderAdmin)
