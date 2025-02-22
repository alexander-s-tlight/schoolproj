from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

from django.core.paginator import Paginator

from apps.tasks.forms import ExamOptionsQuestionForm
from apps.tasks.services.selectors.tasks import exam_get_prev_and_next_question, exam_get_questions
from apps.tasks.services.tasks import exam_create_by_task, exam_options_question_incorrect_word_answer_set

from .models import EXAM_QUESTION_MODEL_BY_TYPE, ExamIncorrectWordQuestion, QuestionTypes, Task, UserExam


def home(request: HttpRequest) -> HttpResponse:
    """Домашняя страница."""
    auth_form = AuthenticationForm(request, data=request.POST or None)

    if auth_form.is_valid():
        user = auth_form.get_user()
        login(request, user)

        return redirect('task_list')

    return render(request, 'tasks/home.html', context={'auth_form': auth_form})


@login_required
def task_list(request: HttpRequest) -> HttpResponse:
    """Страница со списком задач."""
    tasks_list = Task.objects.all().order_by('id')

    paginator = Paginator(tasks_list, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tasks/task_list.html', {'page_obj': page_obj})


def task_detail(request: HttpRequest, task_id: int) -> HttpResponse:
    """Страница с информацией о задании."""
    task = get_object_or_404(Task, id=task_id)

    return render(request, 'tasks/task_detail.html', {'task': task})


def exam_run(request: HttpRequest, task_id: int) -> HttpResponse:
    """Запускает испытание, перенаправляет на страницу выполнения первого задания."""
    task = get_object_or_404(Task, id=task_id)
    _x, first_exam_question = exam_create_by_task(task=task, user=request.user)

    if first_exam_question:
        return redirect('exam_question', first_exam_question.QUESTION_TYPE, first_exam_question.id)

    return redirect('homepage')


def exam_question(request: HttpRequest, question_type: str, question_id: int) -> HttpResponse:
    """Страница с вопросом испытания."""
    if question_type not in QuestionTypes:
        raise Http404

    exam_question_model = EXAM_QUESTION_MODEL_BY_TYPE[question_type]
    exam_question = get_object_or_404(exam_question_model, id=question_id)

    exam_question_form = None
    if question_type == QuestionTypes.OPTIONS:
        exam_question_form = ExamOptionsQuestionForm(request.POST or None, instance=exam_question)

        if request.POST and exam_question_form.is_valid():
            exam_question_form.save()

            _x, next_question = exam_get_prev_and_next_question(question=exam_question)

            if next_question:
                return redirect('exam_question', next_question.QUESTION_TYPE, next_question.id)

            return redirect('exam_results', exam_question.exam_id)

    context = {
        'QuestionTypes': QuestionTypes,
        'exam_question': exam_question,
        'exam_question_form': exam_question_form,
    }

    return render(request, 'tasks/exam_question.html', context)


def exam_question_incorrect_word_answer(request: HttpRequest, question_id: int, letter_index: int) -> HttpResponse:
    """Фиксация ответа на вопрос с некорректным словом."""
    exam_question = get_object_or_404(ExamIncorrectWordQuestion, id=question_id)
    exam_options_question_incorrect_word_answer_set(question=exam_question, letter_index=letter_index)

    _x, next_question = exam_get_prev_and_next_question(question=exam_question)

    if next_question:
        return redirect('exam_question', next_question.QUESTION_TYPE, next_question.id)

    return redirect('exam_results', exam_question.exam_id)


def exam_results(request, exam_id: int):
    """Страница с результатами испытания."""
    exam = get_object_or_404(UserExam, id=exam_id)

    context = {
        'QuestionTypes': QuestionTypes,
        'exam': exam,
        'exam_questions': exam_get_questions(exam=exam),
    }

    return render(request, 'tasks/exam_results.html', context=context)


def exam_list(request: HttpRequest) -> HttpResponse:
    """Страница со списком испытаний."""
    exams = UserExam.objects.filter(user=request.user).order_by('-created_at')

    paginator = Paginator(exams, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tasks/exam_list.html', {'page_obj': page_obj, 'exams': exams})
