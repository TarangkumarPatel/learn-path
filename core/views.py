from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LearningGoalForm, LearningGoalProgressForm, SignUpForm
from .models import Assessment, AssessmentResult, Course, Curriculum, LearningGoal, Tag, UserCourseEnrollment, UserCourseProgress


def home(request):
    return render(request, 'core/home.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()

    return render(request, 'core/signup.html', {'form': form})


@login_required
def dashboard(request):
    if request.method == 'POST':
        goal_form = LearningGoalForm(request.POST, user=request.user)
        if goal_form.is_valid():
            learning_goal = goal_form.save(commit=False)
            learning_goal.user = request.user
            learning_goal.save()
            return redirect('dashboard')
    else:
        goal_form = LearningGoalForm(user=request.user)

    enrollments = list(
        UserCourseEnrollment.objects.filter(user=request.user, is_active=True)
        .select_related('course', 'course__subject')
        .order_by('course__title')
    )
    course_progress_records = {
        progress.course_id: progress
        for progress in UserCourseProgress.objects.filter(user=request.user).select_related('course')
    }

    enrolled_courses = []
    completed_courses = []
    topics_remaining_count = 0
    for enrollment in enrollments:
        course = enrollment.course
        progress = course_progress_records.get(course.id)
        completion_percentage = progress.completion_percentage if progress else 0
        status = progress.status if progress else 'not_started'
        topic_count = course.topics.count()
        topics_remaining = max(0, topic_count - round(topic_count * completion_percentage / 100))
        course.summary = {
            'progress': completion_percentage,
            'status': status,
            'topic_count': topic_count,
            'topics_remaining': topics_remaining,
        }
        topics_remaining_count += topics_remaining
        if completion_percentage >= 100 or status == 'completed':
            completed_courses.append(course)
        else:
            enrolled_courses.append(course)

    available_courses = list(
        Course.objects.filter(is_published=True)
        .exclude(enrollments__user=request.user, enrollments__is_active=True)
        .annotate(topic_count=Count('topics', distinct=True))
        .select_related('subject')
        .prefetch_related('topics')
        .order_by('title')[:6]
    )

    assessments = list(
        Assessment.objects.filter(is_active=True)
        .select_related('course', 'course__subject')
        .annotate(question_count=Count('questions'))
        .order_by('course__title', 'title')
    )
    latest_results = list(
        AssessmentResult.objects.filter(user=request.user)
        .select_related('assessment', 'assessment__course', 'assessment__course__subject')
        .order_by('-submitted_at')[:5]
    )
    latest_result_by_assessment = {}
    for result in latest_results:
        latest_result_by_assessment.setdefault(result.assessment_id, result)
    for assessment in assessments:
        assessment.latest_result = latest_result_by_assessment.get(assessment.id)

    learning_goals = list(
        LearningGoal.objects.filter(user=request.user)
        .select_related('course', 'course__subject')
        .order_by('status', 'target_date', '-created_at')
    )
    for goal in learning_goals:
        goal.progress_form = LearningGoalProgressForm(instance=goal, prefix=f'goal-{goal.pk}')

    top_progress_course = None
    all_tracked_courses = enrolled_courses + completed_courses
    if all_tracked_courses:
        top_progress_course = max(all_tracked_courses, key=lambda course: course.summary['progress'])

    notifications = []
    if enrolled_courses:
        notifications.append(
            f"Continue {enrolled_courses[0].title} ({enrolled_courses[0].summary['progress']}% complete)."
        )
    active_goals = [goal for goal in learning_goals if goal.status != 'completed']
    if active_goals:
        notifications.append(f"You have {len(active_goals)} active learning goals in progress.")
    if assessments:
        notifications.append(f"{len(assessments)} assessments are available in the quiz center.")
    if not notifications:
        notifications.append('Start by enrolling in a course or creating a learning goal.')

    context = {
        'goal_form': goal_form,
        'enrolled_courses': enrolled_courses,
        'completed_courses': completed_courses,
        'available_courses': available_courses,
        'courses_enrolled_count': len(enrollments),
        'courses_completed_count': len(completed_courses),
        'topics_remaining_count': topics_remaining_count,
        'top_progress_course': top_progress_course,
        'notifications': notifications,
        'assessments': assessments,
        'latest_results': latest_results,
        'learning_goals': learning_goals,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def assessment_detail(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.filter(is_active=True).select_related('course', 'course__subject').prefetch_related('questions'),
        pk=assessment_id,
    )
    questions = list(assessment.questions.all())
    latest_result = (
        AssessmentResult.objects.filter(user=request.user, assessment=assessment)
        .order_by('-submitted_at')
        .first()
    )
    submitted_result = None

    if request.method == 'POST' and questions:
        submitted_answers = {}
        correct_answers = 0
        for question in questions:
            submitted_answer = request.POST.get(f'question_{question.id}', '').upper()
            if submitted_answer in {'A', 'B', 'C', 'D'}:
                submitted_answers[str(question.id)] = submitted_answer
            if submitted_answer == question.correct_option:
                correct_answers += 1

        total_questions = len(questions)
        score = round((correct_answers / total_questions) * 100) if total_questions else 0
        submitted_result = AssessmentResult.objects.create(
            user=request.user,
            assessment=assessment,
            score=score,
            correct_answers=correct_answers,
            total_questions=total_questions,
            passed=score >= assessment.passing_score,
            answers=submitted_answers,
        )
        latest_result = submitted_result

    context = {
        'assessment': assessment,
        'questions': questions,
        'latest_result': latest_result,
        'submitted_result': submitted_result,
    }
    return render(request, 'core/assessment_detail.html', context)


@login_required
def enroll_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course.objects.filter(is_published=True), pk=course_id)
        with transaction.atomic():
            enrollment, created = UserCourseEnrollment.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={'is_active': True},
            )
            if not created and not enrollment.is_active:
                enrollment.is_active = True
                enrollment.save(update_fields=['is_active'])

            UserCourseProgress.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={'completion_percentage': 0, 'status': 'not_started'},
            )
    return redirect('dashboard')


@login_required
def update_learning_goal(request, goal_id):
    goal = get_object_or_404(LearningGoal, pk=goal_id, user=request.user)
    if request.method == 'POST':
        form = LearningGoalProgressForm(request.POST, instance=goal, prefix=f'goal-{goal.pk}')
        if form.is_valid():
            updated_goal = form.save(commit=False)
            if updated_goal.status == 'completed' and updated_goal.progress_percentage < 100:
                updated_goal.progress_percentage = 100
            elif updated_goal.progress_percentage == 100 and updated_goal.status != 'completed':
                updated_goal.status = 'completed'
            updated_goal.save()
    return redirect('dashboard')


@login_required
def curriculum_browser(request):
    curricula = Curriculum.objects.filter(is_published=True).prefetch_related('tags', 'lessons')

    # Search
    query = request.GET.get('q', '').strip()
    if query:
        curricula = curricula.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Filter by level
    level = request.GET.get('level', '')
    if level:
        curricula = curricula.filter(level=level)

    # Filter by tag
    tag_id = request.GET.get('tag', '')
    if tag_id:
        curricula = curricula.filter(tags__id=tag_id)

    sort = request.GET.get('sort', 'newest')
    sort_options = {
        'newest': '-created_at',
        'title': 'title',
        'time': 'estimated_hours',
    }
    curricula = curricula.order_by(sort_options.get(sort, '-created_at'))

    all_tags = Tag.objects.all()

    context = {
        'curricula': curricula,
        'all_tags': all_tags,
        'query': query,
        'selected_level': level,
        'selected_tag': tag_id,
        'selected_sort': sort if sort in sort_options else 'newest',
        'level_choices': [('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        'sort_choices': [('newest', 'Newest'), ('title', 'Title'), ('time', 'Shortest Time')],
    }
    return render(request, 'core/curriculum_browser.html', context)
