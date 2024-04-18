from django import forms
from django.db.models import JSONField
from ManageDocument import models as DocumentModels

from django.forms import ModelChoiceField

class MyModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "My Object #%i" % obj.id

class AccessAccounts(forms.Form):
    username = JSONField()
    email = JSONField()
    permissions = JSONField()

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'id':'NewDocumentTitle'}))
    docFile = forms.FileField(widget=forms.FileInput(attrs={'id':'NewDocumentFileInput'}), required=False)
    template = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'id':'NewTemplateInput'}), required=False)

    def __init__(self, *args, **kwargs):
        templates = kwargs.pop('templates', ())
        super().__init__(*args, **kwargs)
        self.fields['template'].choices = templates

    def clean(self):
        file = self.cleaned_data.get('docFile')
        template = self.cleaned_data.get('template')
        if not file and (template == 'None'):
            raise forms.ValidationError('Please enter a file or choose a template')
        return self.cleaned_data

class UploadFilesForm(forms.Form):
    title = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'id':'NewDocumentTitle'}))
    docFile = forms.FileField(widget=forms.FileInput(attrs={'id':'NewDocumentFileInput'}), required=False)
    template = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'id':'NewTemplateInput'}), required=False)
    additionalFile = forms.FileField(widget=forms.FileInput(attrs={'id':'AdditionalFileInput'}), required=False)

    def __init__(self, *args, **kwargs):
        templates = kwargs.pop('templates', ())
        super().__init__(*args, **kwargs)
        self.fields['template'].choices = templates

    def clean(self):
        file = self.cleaned_data.get('docFile')
        template = self.cleaned_data.get('template')
        if not file and (template == 'None'):
            raise forms.ValidationError('Please enter a file or choose a template')
        return self.cleaned_data



class UploadTemplateForm(forms.Form):
    title = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'id':'NewDocumentTitle'}), required=True)
    docFile = forms.FileField(widget=forms.FileInput(attrs={'id':'NewTemplateFileInput'}), required=True)


CHOICES = [('View','View'),
            ('Sign','Sign'),
            ('Edit','Edit')]

class AddUserToFile(forms.Form):
    name = forms.CharField(max_length=50)
    choice = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)

class AlertForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(), required=False)
    time = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'id':'TimeField'}), required=False)
    allTime = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'id':'AllTimeField'}), required=False)
    ampm = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'id':'ampm'}), required=False)
    alert = forms.CharField(widget=forms.Textarea(attrs={'id':'alert'}), required=True)

    def __init__(self, *args, **kwargs):
        timeChoices = kwargs.pop('timeChoices', ())
        allTimeChoices = kwargs.pop('allTimeChoices', ())
        ampmChoices = kwargs.pop('ampmChoices', ())
        super(AlertForm, self).__init__(*args, **kwargs)
        self.fields['time'].choices = timeChoices
        self.fields['allTime'].choices = allTimeChoices
        self.fields['ampm'].choices = ampmChoices
        import datetime
        thisDate = datetime.datetime.now()
        currentDate = str(thisDate.year) + '-' + str(thisDate.month) + '-' + str(thisDate.day)
        if (thisDate.month + 6) > 12:
            maxDate = str(thisDate.year + 1) + '-' + str((thisDate.month + 6) - 12) + '-' + str(thisDate.day)
        else:
            maxDate = str(thisDate.year) + '-' + str(thisDate.month + 6) + '-' + str(thisDate.day)
        self.fields['date'] = forms.DateField(widget=forms.SelectDateWidget(attrs={'id':'DateField', 'min':currentDate, \
            'max':maxDate, 'value':currentDate}), required=False)

    def clean(self):
        return self.cleaned_data