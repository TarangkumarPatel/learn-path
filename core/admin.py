from django.contrib import admin

from .models import (
    Assessment,
    AssessmentResult,
    ContentBlock,
    Course,
    CourseLesson,
    Curriculum,
    Lesson,
    LearningGoal,
    Question,
    Subject,
    Tag,
    Topic,
    UserCourseEnrollment,
    UserCourseProgress,
    UserLessonProgress,
    UserTopicProgress,
)


admin.site.site_header = 'LearnPath Admin'
admin.site.site_title = 'LearnPath Admin'
admin.site.index_title = 'Manage courses, content, and learners'


# lets you edit content blocks directly on the lesson page instead of navigating away
class ContentBlockInline(admin.StackedInline):
    model = ContentBlock
    extra = 1
    ordering = ['order']


# stacked inline here because lessons have enough fields that tabular gets cramped
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'curriculum', 'duration_minutes', 'order')
    list_filter = ('curriculum',)
    search_fields = ('title', 'description')
    inlines = [ContentBlockInline]


# tabular is fine here, lessons don't have that many fields
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ['order']


# date_hierarchy is really handy for spotting when curricula were created in bulk
@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'estimated_hours', 'is_published', 'created_at')
    list_filter = ('level', 'is_published', 'tags')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)
    inlines = [LessonInline]
    list_editable = ('is_published',)
    date_hierarchy = 'created_at'
    list_per_page = 20


# simple model, just needs search so other admins can use autocomplete on it
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)


# keeping it minimal, admins rarely need to touch topics outside of the course page
class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = ('title', 'order')
    ordering = ('order',)


# slug is prepopulated so admins don't have to type it manually
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


# autocomplete on subject saves a lot of time when there are many subjects
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'level', 'estimated_hours', 'is_published', 'created_at')
    list_filter = ('subject', 'level', 'is_published')
    search_fields = ('title', 'description', 'subject__name')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('subject',)
    inlines = [TopicInline]
    list_editable = ('is_published',)


# is_preview is important to get right so free users don't accidentally see paid content
class CourseLessonInline(admin.TabularInline):
    model = CourseLesson
    extra = 1
    fields = ('title', 'duration_minutes', 'order', 'is_preview')
    ordering = ('order',)


# correct_option is shown inline so it's easy to spot misconfigured questions at a glance
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('prompt', 'correct_option', 'order')
    ordering = ('order',)


# prerequisites use filter_horizontal since a topic can have many, and picking
# them from a plain multi-select would get unwieldy fast
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    filter_horizontal = ('prerequisites',)
    inlines = [CourseLessonInline]


@admin.register(CourseLesson)
class CourseLessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'duration_minutes', 'order', 'is_preview')
    list_filter = ('is_preview', 'topic__course')
    search_fields = ('title', 'content')


# questions are managed inline on the assessment; no need for a standalone
# top-level view of them
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'passing_score', 'is_active', 'created_at')
    list_filter = ('is_active', 'course')
    search_fields = ('title', 'description', 'course__title')
    inlines = [QuestionInline]


# results are a submission log, not something admins hand-author, so nothing
# here is editable — this is a read-only view for reviewing learner outcomes
@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'score', 'passed', 'submitted_at')
    list_filter = ('passed', 'assessment__course')
    search_fields = ('user__username', 'user__name', 'assessment__title')
    date_hierarchy = 'submitted_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'course', 'status', 'progress_percentage', 'target_date')
    list_filter = ('status', 'course')
    search_fields = ('title', 'user__username', 'user__name')


@admin.register(UserCourseEnrollment)
class UserCourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'is_active', 'enrolled_at')
    list_filter = ('is_active', 'course')
    search_fields = ('user__username', 'user__name', 'course__title')


@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'completion_percentage', 'last_accessed_at')
    list_filter = ('status', 'course')
    search_fields = ('user__username', 'user__name', 'course__title')


@admin.register(UserTopicProgress)
class UserTopicProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'completion_percentage', 'completed_at')
    list_filter = ('topic__course',)
    search_fields = ('user__username', 'user__name', 'topic__title')


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'status', 'completion_percentage', 'last_accessed_at')
    list_filter = ('status', 'lesson__topic__course')
    search_fields = ('user__username', 'user__name', 'lesson__title')
