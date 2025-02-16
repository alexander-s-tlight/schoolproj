from django import forms

from tasks.models import ExamOptionsQuestion


class ExamOptionsQuestionForm(forms.ModelForm):
    """Форма для сохранения ответа на вопрос с вариантами ответа."""

    class Meta:
        """Настройки формы."""

        model = ExamOptionsQuestion
        fields = (
            'selected_option1_is_true',
            'selected_option2_is_true',
            'selected_option3_is_true',
        )

        widgets = {
            'selected_option1_is_true': forms.CheckboxInput(),
            'selected_option2_is_true': forms.CheckboxInput(),
            'selected_option3_is_true': forms.CheckboxInput(),
        }
