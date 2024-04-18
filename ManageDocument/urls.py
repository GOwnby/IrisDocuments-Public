from django.urls import path

from . import views

urlpatterns = [
    path('Upload/', views.uploaded, name='UploadDocument'),
    path('Delete/<str:requestID>/', views.DeleteDraft, name="DeleteDraft"),
    path('DeleteTemplate/<str:requestID>/', views.DeleteTemplate, name="DeleteDraft"),
    path('UploadTemplate/', views.uploadedTemplate, name='UploadDocument'),
    path('<str:requestID>/', views.Document, name='SignDocument'),
    path('<str:requestID>/CreateAccount/', views.DocumentNewAccount, name="SignDocumentNewAccount"),
    path('<str:requestID>/Submission/', views.SignedDocumentSubmission, name="SignedDocumentSubmission"),
    path('<str:requestID>/verified/', views.ManageDocument, name='ManageDocument'),
    path('<str:requestID>/Audit/', views.ViewAudit, name='ViewAudit'),
    path('<str:requestID>/Audit/Download/', views.DownloadAudit, name='DownloadAudit'),
    path('<str:requestID>/Document/Download/', views.DownloadDocument, name='DownloadDocument'),
    path('<str:requestID>/Document/DownloadAdditional/', views.DownloadAdditional, name='DownloadAdditional'),
    path('<str:requestID>/verified/<str:templateID>/', views.ManageDocumentWithTemplate, name='ManageDocument'),
    path('<str:requestID>/EditTemplate/', views.ManageTemplate, name="ManageTemplate"),
    path('Editor/<str:requestID>/<str:usersAdded>/', views.PdfEditor, name='EditDocument'),
    path('Editor/<str:requestID>/<str:usersAdded>/Notify/', views.PdfEditorNotify, name='EditDocumentNotify'),
    path('Editor/<str:requestID>/<str:usersAdded>/<str:sendDate>/', views.PdfEditorLater, name='EditDocumentLater'),
    path('Editor/<str:requestID>/<str:usersAdded>/<str:sendDate>/Notify/', views.PdfEditorLaterNotify, name='EditDocumentLaterNotify'),
    path('Edited/<str:requestID>/<str:templateID>/<str:usersAdded>/', views.PdfWithTemplateEditor, name='EditDocumentWithTemplate'),
    path('Edited/<str:requestID>/<str:templateID>/<str:usersAdded>/Notify/', views.PdfWithTemplateEditorNotify, name='EditDocumentWithTemplateNotify'),
    path('TemplateEditor/<str:requestID>/<str:usersAdded>/', views.PdfTemplateEditor, name='EditDocument'),
    path('DocumentSent/Later/<str:requestID>/<str:userData>/', views.addUsersToDocumentLater, name='addUsersToDocumentLater'),
    path('DocumentSent/Later/<str:requestID>/<str:userData>/<str:textData>/', views.addUsersToDocumentWithTextLater, name='addUsersToDocumentWithTextLater'),
    path('DocumentSent/Later/<str:requestID>/<str:userData>/<str:textData>/<str:brandData>/', views.addUsersToDocumentWithTextAndBrandLater, name='addUsersToDocumentWithTextAndBrandLater'),
    path('DocumentSent/<str:requestID>/<str:userData>/', views.addUsersToDocument, name='addUsersToDocument'),
    path('DocumentSent/<str:requestID>/<str:userData>/<str:textData>/', views.addUsersToDocumentWithText, name='addUsersToDocumentWithText'),
    path('DocumentSent/<str:requestID>/<str:userData>/<str:textData>/<str:brandData>/', views.addUsersToDocumentWithTextAndBrand, name='addUsersToDocumentWithTextAndBrand'),
    path('FinalizeTemplate/<str:requestID>/<str:userData>/', views.addUsersToTemplate, name='addUsersToTemplate'),
    path('FinalizeTemplate/<str:requestID>/<str:userData>/<str:textData>/', views.addUsersToTemplateWithText, name='addUsersToTemplateWithText'),
    path('FinalizeTemplate/<str:requestID>/<str:userData>/<str:textData>/<str:brandData>/', views.addUsersToTemplateWithTextAndBrand, name='addUsersToTemplateWithTextAndBrand')
]