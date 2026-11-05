from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import LearningGoal

# using get_user_model() instead of importing User directly so this works
# even if someone swaps in a custom user model later
User = get_user_model()


class SignUpForm(UserCreationForm):
    # we need the user's name too, not just username
    name = forms.CharField(max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('name', 'username', 'password1', 'password2')

    def save(self, commit=True):
        # don't hit the database yet, we still need to set the name
        user = super().save(commit=False)

        # trim any accidental spaces the user might have typed
        cleaned_name = self.cleaned_data['name'].strip()

        # first_name is Django's built-in field, always safe to set
        user.first_name = cleaned_name

        # some custom user models have a separate 'name' field, handle that too
        if hasattr(user, 'name'):
            user.name = cleaned_name

        if commit:
            user.save()

        return user


class LearningGoalForm(forms.ModelForm):
    # without this override the date input is just a plain text box, not great UX
    target_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = LearningGoal
        fields = ('title', 'description', 'course', 'target_date')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # a goal doesn't have to be tied to a course
        self.fields['course'].required = False

        # no point showing unpublished courses in the dropdown
        self.fields['course'].queryset = self.fields['course'].queryset.filter(is_published=True)

        if user is not None:
            # only show courses this user is actually enrolled in
            # distinct() is needed here because the enrollment join can produce duplicates
            self.fields['course'].queryset = self.fields['course'].queryset.filter(
                enrollments__user=user,
                enrollments__is_active=True,
            ).distinct()

    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')

        # a goal with a deadline that already passed doesn't make much sense
        if target_date and target_date < date.today():
            raise forms.ValidationError("Target date can't be in the past.")

        return target_date


class LearningGoalProgressForm(forms.ModelForm):
    # kept intentionally small — this form is just for marking progress, nothing else
    class Meta:
        model = LearningGoal
        fields = ('status', 'progress_percentage')
