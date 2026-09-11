from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import (
    Assessment,
    AssessmentResult,
    Course,
    Curriculum,
    LearningGoal,
    Lesson,
    Question,
    Subject,
    Tag,
    Topic,
    UserCourseEnrollment,
    UserCourseProgress,
)
from .forms import SignUpForm


User = get_user_model()

# --- 1. MODEL TESTS ---
class ModelTests(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name='Python')
        self.curriculum = Curriculum.objects.create(
            title='Django Basics',
            description='Learn Django architecture.',
            level='beginner',
            estimated_hours=10
        )
        self.lesson = Lesson.objects.create(
            curriculum=self.curriculum,
            title='Introduction to Models',
            order=1
        )

    def test_tag_str(self):
        self.assertEqual(str(self.tag), 'Python')

    def test_curriculum_str(self):
        self.assertEqual(str(self.curriculum), 'Django Basics')

    def test_lesson_str(self):
        self.assertEqual(str(self.lesson), 'Django Basics - Introduction to Models')

# --- 2. FORM TESTS ---
class SignUpFormTests(TestCase):
    def test_valid_signup_form(self):
        data = {
            'name': 'Tarang',
            'username': 'newuser',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid())
        
        # Test the custom save method that extracts the first name
        user = form.save()
        self.assertEqual(user.first_name, 'Tarang')
        self.assertEqual(user.username, 'newuser')

    def test_invalid_signup_form_mismatched_passwords(self):
        data = {
            'name': 'Tarang',
            'username': 'newuser',
            'password1': 'strongpass123',
            'password2': 'differentpass'
        }
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

# --- 3. GENERAL VIEW TESTS ---
class GeneralViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='strong-pass-123')

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        self.assertContains(response, 'Welcome to LearnPath')
        self.assertContains(response, 'Create Account')

    def test_signup_view_get(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/signup.html')

    def test_signup_redirects_authenticated_user(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('signup'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_renders_for_logged_in_user(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/dashboard.html')

# --- 4. CURRICULUM BROWSER TESTS (Merged) ---
class CurriculumBrowserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='strong-pass-123')
        self.tag = Tag.objects.create(name='Backend')
        
        # Your original setup item
        self.basic_curr = Curriculum.objects.create(
            title='Python Basics',
            description='Intro curriculum',
            level='beginner',
            estimated_hours=5,
            is_published=True,
        )
        
        # Additional item for testing filters
        self.adv_curr = Curriculum.objects.create(
            title='Advanced Django',
            description='Deep dive into Django.',
            level='advanced',
            estimated_hours=12,
            is_published=True
        )
        self.adv_curr.tags.add(self.tag)

        self.api_curr = Curriculum.objects.create(
            title='API Design',
            description='Design reliable APIs.',
            level='intermediate',
            estimated_hours=3,
            is_published=True,
        )

    # Your original test
    def test_curriculum_browser_requires_login(self):
        response = self.client.get(reverse('curriculum_browser'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    # Your original test
    def test_curriculum_browser_renders_for_logged_in_user(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('curriculum_browser'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/curriculum_browser.html')
        self.assertContains(response, 'Python Basics')

    # New Filter Tests
    def test_curriculum_browser_search_filter(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('curriculum_browser'), {'q': 'Deep dive'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Advanced Django')
        self.assertNotContains(response, 'Python Basics')

    def test_curriculum_browser_tag_filter(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('curriculum_browser'), {'tag': self.tag.id})
        self.assertContains(response, 'Advanced Django')
        self.assertNotContains(response, 'Python Basics')

    def test_curriculum_browser_level_filter(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('curriculum_browser'), {'level': 'beginner'})
        self.assertContains(response, 'Python Basics')
        self.assertNotContains(response, 'Advanced Django')

    def test_curriculum_browser_sorts_by_newest(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('curriculum_browser'), {'sort': 'newest'})
        curricula = list(response.context['curricula'])
        self.assertEqual(curricula[0], self.api_curr)
        self.assertEqual(curricula[1], self.adv_curr)
        self.assertEqual(curricula[2], self.basic_curr)

    def test_curriculum_browser_sorts_by_title(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('curriculum_browser'), {'sort': 'title'})
        curricula = list(response.context['curricula'])
        self.assertEqual(curricula[0], self.api_curr)
        self.assertEqual(curricula[1], self.adv_curr)
        self.assertEqual(curricula[2], self.basic_curr)

    def test_curriculum_browser_sorts_by_time(self):
        self.client.login(username='tester', password='strong-pass-123')
        response = self.client.get(reverse('curriculum_browser'), {'sort': 'time'})
        curricula = list(response.context['curricula'])
        self.assertEqual(curricula[0], self.api_curr)
        self.assertEqual(curricula[1], self.basic_curr)
        self.assertEqual(curricula[2], self.adv_curr)



# from django.test import TestCase
# from django.urls import reverse
# from django.contrib.auth.models import User

# from .models import Curriculum


# class CurriculumBrowserTests(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username='tester', password='strong-pass-123')
#         Curriculum.objects.create(
#             title='Python Basics',
#             description='Intro curriculum',
#             level='beginner',
#             estimated_hours=5,
#             is_published=True,
#         )

#     def test_curriculum_browser_requires_login(self):
#         response = self.client.get(reverse('curriculum_browser'))
#         self.assertEqual(response.status_code, 302)
#         self.assertIn(reverse('login'), response.url)

#     def test_curriculum_browser_renders_for_logged_in_user(self):
#         self.client.login(username='tester', password='strong-pass-123')
#         response = self.client.get(reverse('curriculum_browser'))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'core/curriculum_browser.html')
#         self.assertContains(response, 'Python Basics')


class DashboardFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner', password='strong-pass-123', name='Learner One')
        self.subject = Subject.objects.create(name='Programming', slug='programming')
        self.course = Course.objects.create(
            subject=self.subject,
            title='Python Foundations Sprint',
            slug='python-foundations-sprint',
            level='beginner',
            estimated_hours=8,
            is_published=True,
        )
        Topic.objects.create(course=self.course, title='Syntax', order=1)
        Topic.objects.create(course=self.course, title='Loops', order=2)
        UserCourseEnrollment.objects.create(user=self.user, course=self.course)
        UserCourseProgress.objects.create(
            user=self.user,
            course=self.course,
            completion_percentage=50,
            status='in_progress',
        )
        self.available_course = Course.objects.create(
            subject=self.subject,
            title='JavaScript Basics',
            slug='javascript-basics',
            level='beginner',
            estimated_hours=5,
            is_published=True,
        )
        Topic.objects.create(course=self.available_course, title='Variables and Types', order=1)
        Topic.objects.create(course=self.available_course, title='DOM Events', order=2)

    def test_dashboard_creates_learning_goal(self):
        self.client.login(username='learner', password='strong-pass-123')
        response = self.client.post(
            reverse('dashboard'),
            {
                'title': 'Finish Python Foundations',
                'description': 'Reach the final module this week.',
                'course': self.course.id,
                'target_date': '2026-04-30',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        goal = LearningGoal.objects.get(user=self.user, title='Finish Python Foundations')
        self.assertEqual(goal.course, self.course)
        self.assertEqual(goal.status, 'not_started')

    def test_dashboard_renders_learning_goals_and_course_metrics(self):
        LearningGoal.objects.create(
            user=self.user,
            course=self.course,
            title='Complete core Python topics',
            progress_percentage=50,
            status='in_progress',
        )

        self.client.login(username='learner', password='strong-pass-123')
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Complete core Python topics')
        self.assertContains(response, 'Python Foundations Sprint')
        self.assertContains(response, 'Courses Enrolled')
        self.assertContains(response, 'Topics Remaining')

    def test_update_learning_goal_marks_completed(self):
        goal = LearningGoal.objects.create(
            user=self.user,
            title='Master Python basics',
            status='in_progress',
            progress_percentage=60,
        )

        self.client.login(username='learner', password='strong-pass-123')
        response = self.client.post(
            reverse('update_learning_goal', args=[goal.id]),
            {
                f'goal-{goal.id}-status': 'completed',
                f'goal-{goal.id}-progress_percentage': 80,
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'completed')
        self.assertEqual(goal.progress_percentage, 100)

    def test_enroll_course_creates_enrollment_and_progress(self):
        self.client.login(username='learner', password='strong-pass-123')
        response = self.client.post(reverse('enroll_course', args=[self.available_course.id]))

        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(
            UserCourseEnrollment.objects.filter(
                user=self.user,
                course=self.available_course,
                is_active=True,
            ).exists()
        )
        progress = UserCourseProgress.objects.get(user=self.user, course=self.available_course)
        self.assertEqual(progress.completion_percentage, 0)
        self.assertEqual(progress.status, 'not_started')

    def test_dashboard_browse_shows_course_outline(self):
        self.client.login(username='learner', password='strong-pass-123')
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'JavaScript Basics')
        self.assertContains(response, 'Variables and Types')
        self.assertContains(response, 'DOM Events')


class AssessmentFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='quizuser', password='strong-pass-123', name='Quiz User')
        self.subject = Subject.objects.create(name='Data', slug='data')
        self.course = Course.objects.create(
            subject=self.subject,
            title='SQL Basics',
            slug='sql-basics',
            level='beginner',
            estimated_hours=6,
            is_published=True,
        )
        self.assessment = Assessment.objects.create(
            course=self.course,
            title='SQL Entry Assessment',
            passing_score=50,
            is_active=True,
        )
        self.question_one = Question.objects.create(
            assessment=self.assessment,
            prompt='Which keyword retrieves data?',
            option_a='SELECT',
            option_b='DELETE',
            option_c='DROP',
            option_d='ALTER',
            correct_option='A',
            order=1,
        )
        self.question_two = Question.objects.create(
            assessment=self.assessment,
            prompt='Which clause filters rows?',
            option_a='ORDER BY',
            option_b='GROUP BY',
            option_c='WHERE',
            option_d='JOIN',
            correct_option='C',
            order=2,
        )

    def test_assessment_submission_creates_result(self):
        self.client.login(username='quizuser', password='strong-pass-123')
        response = self.client.post(
            reverse('assessment_detail', args=[self.assessment.id]),
            {
                f'question_{self.question_one.id}': 'A',
                f'question_{self.question_two.id}': 'B',
            },
        )

        self.assertEqual(response.status_code, 200)
        result = AssessmentResult.objects.get(user=self.user, assessment=self.assessment)
        self.assertEqual(result.correct_answers, 1)
        self.assertEqual(result.total_questions, 2)
        self.assertEqual(result.score, 50)
        self.assertTrue(result.passed)
        self.assertContains(response, 'Assessment Submitted')

    def test_dashboard_shows_assessment_result(self):
        AssessmentResult.objects.create(
            user=self.user,
            assessment=self.assessment,
            score=100,
            correct_answers=2,
            total_questions=2,
            passed=True,
            answers={str(self.question_one.id): 'A', str(self.question_two.id): 'C'},
        )

        self.client.login(username='quizuser', password='strong-pass-123')
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'SQL Entry Assessment')
        self.assertContains(response, '100% score')
