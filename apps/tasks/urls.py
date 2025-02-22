from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tasks/', views.task_list, name='task_list'),
    # path('results/', views.home, name='user_results'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path(
        'exam/',
        include(
            [
                path('run/<int:task_id>/', views.exam_run, name='exam_run'),
                path('question/<str:question_type>/<int:question_id>/', views.exam_question, name='exam_question'),
                path(
                    'incorrect-word-answer/<int:question_id>/<int:letter_index>/',
                    views.exam_question_incorrect_word_answer,
                    name='exam_question_incorrect_word_answer',
                ),
                path('results/', views.exam_list, name='exam_list'),
                path('results/<int:exam_id>/', views.exam_results, name='exam_results'),
            ]
        ),
    ),
]
