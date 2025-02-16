import random

from django.contrib.auth.models import User
from django.db import transaction

from tasks.models import (
    ExamIncorrectWordQuestion,
    ExamOptionsQuestion,
    IncorrectWordQuestionBase,
    IncorrectWordQuestionBlank,
    OptionsQuestionBlank,
    Task,
    UserExam,
)


def exam_incorrect_word_question_create_from_blank(
    *, exam: UserExam, blank: IncorrectWordQuestionBlank, commit: bool = True
) -> ExamIncorrectWordQuestion:
    """Создает объект вопроса с неправильной буквой для испытания."""
    new_instance_data = {x.name: getattr(blank, x.name) for x in IncorrectWordQuestionBase._meta.get_fields()}

    new_instance = ExamIncorrectWordQuestion(exam=exam, **new_instance_data)

    if not commit:
        return new_instance

    new_instance.full_clean()
    new_instance.save()

    return new_instance


def exam_options_question_create_from_blank(
    *, exam: UserExam, blank: OptionsQuestionBlank, commit: bool = True
) -> ExamOptionsQuestion:
    """Создает объект вопроса с вариантами ответов для испытания."""
    new_instance = ExamOptionsQuestion(exam=exam, question=blank.question)

    acceptor_field_pairs = (
        ('option1', 'option1_is_true'),
        ('option2', 'option2_is_true'),
        ('option3', 'option3_is_true'),
    )

    donor_field_pairs = list(acceptor_field_pairs)
    random.shuffle(donor_field_pairs)
    # Отбросим поля с пустыми значениями.
    donor_field_pairs = [(x, y) for x, y in donor_field_pairs if getattr(blank, x)]

    for (acceptor_field1, acceptor_field2), (donor_field1, donor_field2) in zip(
        acceptor_field_pairs, donor_field_pairs, strict=False
    ):
        setattr(new_instance, acceptor_field1, getattr(blank, donor_field1))
        setattr(new_instance, acceptor_field2, getattr(blank, donor_field2))

    if not commit:
        return new_instance

    new_instance.full_clean()
    new_instance.save()

    return new_instance


@transaction.atomic
def exam_create_by_task(
    *, task: Task, user: User
) -> tuple[UserExam, ExamOptionsQuestion | ExamIncorrectWordQuestion | None]:
    """Создает испытание на основе задания."""
    exam = UserExam(user=user)
    # В текущей реализации дата начала совпадает с датой добавления.
    exam.started_at = exam.created_at
    exam.full_clean()
    exam.save()

    questions = [
        *task.incorrectwordquestionblank_set.all(),
        *task.optionsquestionblank_set.all(),
    ]

    random.shuffle(questions)

    first_exam_question = None
    for question in questions[: task.max_questions_count]:
        exam_question = (
            exam_options_question_create_from_blank(exam=exam, blank=question, commit=False)
            if isinstance(question, OptionsQuestionBlank)
            else exam_incorrect_word_question_create_from_blank(exam=exam, blank=question, commit=False)
        )
        exam_question.full_clean()
        exam_question.save()

        first_exam_question = first_exam_question or exam_question

    return exam, first_exam_question


def exam_options_question_incorrect_word_answer_set(*, question: ExamIncorrectWordQuestion, letter_index: int) -> None:
    """Фиксирует ответ на вопрос с некорректным словом."""
    question.selected_letter_index = letter_index
    question.full_clean()
    question.save(update_fields=['selected_letter_index', 'finished_at'])
