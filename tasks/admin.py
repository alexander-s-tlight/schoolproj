from django.contrib import admin
from .models import Task, IncorrectWordQuestionBlank, OptionsQuestionBlank


class IncorrectWordQuestionBlankInline(admin.TabularInline):
    """Настройка отображения модели IncorrectWordQuestionBlank."""

    model = IncorrectWordQuestionBlank
    extra = 1
    fields = ('correct_word', 'incorrect_word')


class OptionsQuestionBlankInline(admin.TabularInline):
    model = OptionsQuestionBlank
    extra = 1


class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    inlines = [IncorrectWordQuestionBlankInline, OptionsQuestionBlankInline]


admin.site.register(Task, TaskAdmin)
