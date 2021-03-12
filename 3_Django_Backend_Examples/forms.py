
# AN EXAMPLE OF FORMS IN DJANGO WHICH IS WRITTEN USING DJANGO CRISPY
# FORMS A THRID PARTY DJANGO PACKAGE THAT REDUCES THE NEED TO WRITE
# LARGE HTML CODE FOR FORM HANDLING

from django import forms
from django.utils.translation import ugettext_lazy as _
from models import Profile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout, Submit, \
    Button, Field, MultiField
from crispy_forms.bootstrap import TabHolder, Tab, AccordionGroup, \
    Accordion, InlineRadios, InlineCheckboxes, FormActions


class RegistrationForm(forms.ModelForm):

    username = forms.RegexField(
        regex=r'^\w+$',
        widget=forms.TextInput(attrs=dict(required=True, max_length=30)),
        label=_("Username"),
        error_messages={'invalid': _(
            "This value must contain only letters, numbers and underscores."
        )})
    email = forms.EmailField(
        widget=forms.TextInput(attrs=dict(required=True, max_length=30)),
        label=_("Email address"))
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs=dict(
            required=True, max_length=30, render_value=False)),
        label=_("Password"))
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs=dict(
            required=True, max_length=30, render_value=False)),
        label=_("Password (again)"))

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.common_layout = Layout(
            MultiField(
                "<h5>Registration is free. Start by giving us your e-mail \
                address, and we'll send you instructions on how to continue.\
                We will not spam you or give your e-mail address to anybody.\
                </h5>"),
            MultiField("<h4>Personal Info</h4>"),
            'username',
            'password1',
            'password2',
            'company_name',
            MultiField("<h4>Contact Info</h4>"),
            'email',
            'website',
            'phone_number',
            'address',
            'city',
            'region',
            'country',
            'postal_code',
            FormActions(
                Submit('save', 'Validate & Submit'),
                Button('cancel', 'Cancel', onclick="window.history.back()")
            ),
        )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(self.common_layout, css_class='col-md-6'),
                css_class="row"
            )
        )

    def clean_username(self):
        username_exists = Profile.objects.filter(
            username__iexact=self.cleaned_data['username']).count()
        if username_exists:
            raise forms.ValidationError(_(
                "The username already exists. Please try another one."))
        return self.cleaned_data["username"]

    def clean_email(self):
        email_exists = Profile.objects.filter(
            email__iexact=self.cleaned_data['email']).count()
        if email_exists:
            raise forms.ValidationError(_(
                "The email already exists. Please try another one."))
        return self.cleaned_data["email"]


    def clean(self):
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_(
                    "The two password fields did not match."))
        return self.cleaned_data

    class Meta:
        model = Profile
        exclude = ("groups", "user_permissions",
                   "last_login", "date_joined", "currency", "title",
                   "password", "site", "is_staff", "is_active", "is_superuser")
