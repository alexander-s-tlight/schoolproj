from tasks.models import ExamIncorrectWordQuestion, ExamOptionsQuestion, UserExam


def exam_get_questions(exam: UserExam) -> None:
    """Возвращает последовательность вопросов в испытании."""
    return sorted(
        [
            *exam.examincorrectwordquestion_set.all(),
            *exam.examoptionsquestion_set.all(),
        ],
        key=lambda x: x.created_at,
    )


def exam_get_prev_and_next_question(
    *, question: ExamIncorrectWordQuestion | ExamOptionsQuestion
) -> tuple[
    ExamIncorrectWordQuestion | ExamOptionsQuestion | None, ExamIncorrectWordQuestion | ExamOptionsQuestion | None
]:
    """Возвращает предыдущий и следующий вопрос испытания."""
    all_questions = exam_get_questions(question.exam)

    try:
        question_index = all_questions.index(question)
    except ValueError:
        return None, None

    return (
        all_questions[question_index - 1] if question_index > 1 else None,
        all_questions[question_index + 1] if question_index + 1 < len(all_questions) else None,
    )
