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


# prerequisites use filter_
