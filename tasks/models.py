from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from django.utils import timezone


EXAM_QUESTION_MODEL_BY_TYPE = SimpleLazyObject(
    lambda: {x.QUESTION_TYPE: x for x in (ExamIncorrectWordQuestion, ExamOptionsQuestion)}
)


class Task(models.Model):
    """Задание."""

    title = models.CharField(verbose_name='название задачи', max_length=255)
    description = models.TextField(verbose_name='описание задачи')
    created_at = models.DateTimeField(verbose_name='дата добавления', auto_now_add=True)
    max_questions_count = models.PositiveIntegerField(
        verbose_name='максимальное количество вопросов в испытании', default=1
    )

    class Meta:
        """Настройки модели."""

        verbose_name = 'задание'
        verbose_name_plural = 'задания'
        ordering = ('id',)

    def __str__(self):
        """Строковое представление объекта."""
        return self.title


class QuestionTypes(models.TextChoices):
    """Типы вопросов в задании или испытании."""

    INCORRECT_WORD = 'incorrectword', 'Вопрос c неправильной буквой в слове'
    OPTIONS = 'options', 'Вопрос с вариантами ответа'


class IncorrectWordQuestionBase(models.Model):
    """Базовая модель вопроса c неправильной буквой в слове."""

    QUESTION_TYPE = QuestionTypes.INCORRECT_WORD

    correct_word = models.CharField(verbose_name='правильная форма слова', max_length=255)
    incorrect_word = models.CharField(verbose_name='форма слова с ошибкой', max_length=255)
    incorrect_letter_index = models.IntegerField(verbose_name='номер неправильной буквы')

    class Meta:
        """Настройки модели."""

        abstract = True


class IncorrectWordQuestionBlank(IncorrectWordQuestionBase):
    """Заготовка вопроса c неправильной буквой в слове."""

    task = models.ForeignKey(Task, verbose_name='задание', on_delete=models.CASCADE)

    class Meta:
        """Настройки модели."""

        verbose_name = 'вопрос с неправильной буквой в слове'
        verbose_name_plural = 'вопросы с неправильной буквой в слове'
        ordering = ('id',)

    def clean(self) -> None:
        """Очищает и проверяет данные модели."""
        if self.correct_word == self.incorrect_word:
            raise ValidationError('Формы слова должны отличаться')

        for iter_num, (char1, char2) in enumerate(zip(self.correct_word, self.incorrect_word, strict=False), start=1):
            if char1 != char2:
                self.incorrect_letter_index = iter_num
                break

    def __str__(self):
        """Строковое представление объекта."""
        return f'Вопрос c неправильной буквой № {self.id}: {self.correct_word}'


class OptionsQuestionBase(models.Model):
    """Базовая модель вопроса с вариантами ответа."""

    QUESTION_TYPE = QuestionTypes.OPTIONS

    question = models.CharField(verbose_name='вопрос', max_length=255, default='')
    option1 = models.CharField(verbose_name='первый вариант ответа', max_length=255, default='')
    option1_is_true = models.BooleanField(verbose_name='первый вариант ответа верный')
    option2 = models.CharField(verbose_name='второй вариант ответа', max_length=255, default='')
    option2_is_true = models.BooleanField(verbose_name='второй вариант ответа верный')
    option3 = models.CharField(verbose_name='третий вариант ответа', max_length=255, default='')
    option3_is_true = models.BooleanField(verbose_name='третий вариант ответа верный')

    class Meta:
        """Настройки модели."""

        abstract = True


class OptionsQuestionBlank(OptionsQuestionBase):
    """Заготовка вопроса с вариантами ответа."""

    OPTION_AND_ANSWER_PAIR_FIELDS = (
        ('option1', 'option1_is_true'),
        ('option2', 'option2_is_true'),
        ('option3', 'option3_is_true'),
    )

    task = models.ForeignKey(Task, verbose_name='задание', on_delete=models.CASCADE)

    class Meta:
        """Настройки модели."""

        verbose_name = 'вопрос с вариантами ответа'
        verbose_name_plural = 'вопросы с вариантами ответа'
        ordering = ('id',)

    def clean(self) -> None:
        """Очищает и проверяет данные модели."""
        if not (self.option1_is_true or self.option2_is_true or self.option3_is_true):
            raise ValidationError('Все варианты ответов не могут быть неправильными')

        for option_field, answer_field in self.OPTION_AND_ANSWER_PAIR_FIELDS:
            if getattr(self, answer_field) and not getattr(self, option_field):
                raise ValidationError('Пустой вопрос не может быть правильным')

    def __str__(self):
        """Строковое представление объекта."""
        return f'Вопрос с вариантами ответа № {self.id}: {self.question[:10]}'


class UserExam(models.Model):
    """
    Испытание, которое проходит пользователь.

    В испытании фиксируются версии текстов вопросов и вариантов, существующих
    на момент прохождения испытания.
    """

    user = models.ForeignKey(User, verbose_name='экзаменуемый', on_delete=models.PROTECT)
    created_at = models.DateTimeField(verbose_name='дата добавления', auto_now_add=True)
    started_at = models.DateTimeField(verbose_name='дата начала', null=True, blank=True)
    finished_at = models.DateTimeField(verbose_name='дата завершения', null=True, blank=True)

    class Meta:
        """Настройки модели."""

        verbose_name = 'испытание'
        verbose_name_plural = 'испытания'
        ordering = ('id',)


class ExamQuestionFinishedMixin(models.Model):
    """Примесь для общей логики завершения ответа на вопрос."""

    finished_at = models.DateTimeField(verbose_name='дата завершения', null=True, blank=True)

    class Meta:
        """Настройки модели."""

        abstract = True

    @property
    def is_finished(self) -> bool:
        """Ответ дан."""
        return self.finished_at is not None

    def _finished_clean(self) -> None:
        """Проверка вопроса в испытании на завершенность."""
        if self.is_finished:
            raise ValidationError('На вопрос был получен ответ ранее. Обновление невозможно.')

    def set_finished_at(self):
        """Заполняет дату ответа на вопрос."""
        self.finished_at = timezone.now()


class ExamIncorrectWordQuestion(ExamQuestionFinishedMixin, IncorrectWordQuestionBase):
    """Вопрос в испытании c неправильной буквой."""

    exam = models.ForeignKey(UserExam, verbose_name='испытание', on_delete=models.PROTECT)
    created_at = models.DateTimeField(verbose_name='дата добавления', auto_now_add=True)
    selected_letter_index = models.IntegerField(
        verbose_name='выбранный номер неправильной буквы', null=True, blank=True
    )

    class Meta:
        """Настройки модели."""

        verbose_name = 'вопрос в испытании c неправильной буквой'
        verbose_name_plural = 'вопросы в испытаниях c неправильной буквой'
        ordering = ('id',)

    def clean(self) -> None:
        """Проверяет данные модели."""
        self._finished_clean()

        if self.selected_letter_index is not None:
            self.set_finished_at()

    @property
    def answer_is_correct(self) -> bool:
        """Ответ верный."""
        return self.incorrect_letter_index == self.selected_letter_index


class ExamOptionsQuestion(ExamQuestionFinishedMixin, OptionsQuestionBase):
    """Вопрос в испытании с вариантами ответа."""

    exam = models.ForeignKey(UserExam, verbose_name='испытание', on_delete=models.PROTECT)
    created_at = models.DateTimeField(verbose_name='дата добавления', auto_now_add=True)
    selected_option1_is_true = models.BooleanField(verbose_name='первый вариант ответа верный', null=True, blank=True)
    selected_option2_is_true = models.BooleanField(verbose_name='второй вариант ответа верный', null=True, blank=True)
    selected_option3_is_true = models.BooleanField(verbose_name='третий вариант ответа верный', null=True, blank=True)

    class Meta:
        """Настройки модели."""

        verbose_name = 'вопрос в испытании c выбором варианта ответа'
        verbose_name_plural = 'вопросы в испытании c выбором варианта ответа'
        ordering = ('id',)

    def clean(self) -> None:
        """Проверяет данные модели."""
        self._finished_clean()

        if any(
            [
                self.selected_option1_is_true is not None,
                self.selected_option2_is_true is not None,
                self.selected_option3_is_true is not None,
            ]
        ):
            self.set_finished_at()

    @property
    def answer_is_correct(self) -> bool:
        """Ответ верный."""
        return all(
            [
                self.selected_option1_is_true == self.option1_is_true,
                self.selected_option2_is_true == self.option2_is_true,
                not self.option3 or self.selected_option3_is_true == self.option3_is_true,
            ]
        )
