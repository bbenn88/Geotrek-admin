from django.contrib import admin

from caminae.maintenance.models import (
        Contractor, InterventionStatus, InterventionType, InterventionDisorder,
        ProjectType, ProjectDomain, InterventionJob,
)

class InterventionStatusAdmin(admin.ModelAdmin):
    list_display = ('status',)
    search_fields = ('status', )


class InterventionTypeAdmin(admin.ModelAdmin):
    list_display = ('type',)
    search_fields = ('type',)


class InterventionDisorderAdmin(admin.ModelAdmin):
    list_display = ('disorder',)
    search_fields = ('disorder',)


class InterventionJobAdmin(admin.ModelAdmin):
    list_display = ('job', 'cost',)
    search_fields = ('job',)


admin.site.register(Contractor)
admin.site.register(InterventionStatus, InterventionStatusAdmin)
admin.site.register(InterventionType, InterventionTypeAdmin)
admin.site.register(InterventionDisorder, InterventionDisorderAdmin)
admin.site.register(InterventionJob, InterventionJobAdmin)
admin.site.register(ProjectType)
admin.site.register(ProjectDomain)