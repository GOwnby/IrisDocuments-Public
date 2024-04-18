from django import forms

#DESIGNATION = [
#    ('Corporation','Corporation'),
#    ('Branch','Branch'),
#    ('Team','Team'),
#    ('User','User')
#]

class AccountForm(forms.Form):
    username = forms.CharField(label='Name', max_length=100, required=True, widget=forms.TextInput(attrs={'id':'NameEntry'}))
    email = forms.CharField(label='Email',  max_length=100, required=True, widget=forms.EmailInput(attrs={'id': 'EmailEntry'}))
    password = forms.CharField(label='Password', max_length=32, required=True, widget=forms.PasswordInput(attrs={'id': 'PasswordEntry'}))
    confirm_password = forms.CharField(label='Password', max_length=32, required=True, widget=forms.PasswordInput(attrs={'id': 'ConfirmPasswordEntry'}))

#marketing_list = forms.BooleanField(label='Would you like to opt-in to receive promotional offers from IrisDocuments.com ?')

class VerifyPasswordForm(forms.Form):
    username = forms.CharField(label='Name', max_length=100, required=True, widget=forms.TextInput(attrs={'id':'NameEntry'}))
    password = forms.CharField(label='Password', max_length=32, required=True, widget=forms.PasswordInput(attrs={'id': 'PasswordEntry'}))
    confirm_password = forms.CharField(label='Confirm Password', max_length=32, required=True, widget=forms.PasswordInput(attrs={'id': 'ConfirmPasswordEntry'}))

#marketing_list = forms.BooleanField(label='Would you like to opt-in to receive promotional offers from IrisDocuments.com ?', widget=forms.TextInput(attrs={'id': 'marketing_list','name':'marketing_list'}))


class UploadBrandForm(forms.Form):
    brandFile = forms.FileField(widget=forms.FileInput(), required=True)
#    extra_field_count = forms.CharField(widget=forms.HiddenInput())


#    #def __init__(self, *args, **kwargs):
#     #   extra_fields = kwargs.pop('extra', 0)
#
#    #   super(MyForm, self).__init__(*args, **kwargs)
#      #  self.fields['extra_field_count'].initial = extra_fields
#
#      #  limit = 12
#      #  for index in range(int(extra_fields)):
#      #      if index > limit:
#      #          break
#    #        # generate extra fields in the number specified via extra_fields
#     #       self.fields['extra_field_{index}'.format(index=index)] = forms.CharField(label='Organization Type', widget=forms.Select(choices=DESIGNATION))

