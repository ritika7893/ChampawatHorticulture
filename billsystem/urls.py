from django.urls import path
from .views import DownloadMultipleReceiptsAPIView,UpdateBillingReportAPIView,BillingItemBulkUpload, BillingItemList,BillingReportList,NurseryPhysicalAPIView,NurseryPhysicalRecipientAPIView,RegUserPasswordUpdateAPIView,NurseryFinancialAPIView,BillingFormFilterAPIView,reguser_list,DemandGenerationAPIView,DemandByCenterAPIView,LoginAPIView,GetVikasKhandByCenterAPIView, UpdateBillingItemQuantity,CenterComponentDetailListAPIView,SchemeCreateAPIView,ComponentInvestmentCreateAPIView,BeneficiaryRegistrationAPIView,get_bank_details

urlpatterns = [
    path("billing-items/", BillingItemList.as_view(), name="billing-items"),
    path('login/',LoginAPIView.as_view(),name='login'),
    path("registration-items-upload/", BillingItemBulkUpload.as_view()),
    path("update-billing-item/",UpdateBillingItemQuantity.as_view(),name="update-billing-item"),
    path("report-billing-items/", BillingReportList.as_view(), name="billing-items"),
    path("center-components-list/", CenterComponentDetailListAPIView.as_view(), name="center-component-list"),
    path("component-list/", ComponentInvestmentCreateAPIView.as_view(), name="create_component_investment"),
    path("scheme-list/", SchemeCreateAPIView.as_view(), name="create_scheme"),
    path("component-list/", ComponentInvestmentCreateAPIView.as_view(), name="create_component_investment"),
    path("beneficiaries-registration/", BeneficiaryRegistrationAPIView.as_view(), name="beneficiary_registration"),
    path('get-bank-details/', get_bank_details, name='get-bank-details'),
    path("get-vikas-khand-by-center/", GetVikasKhandByCenterAPIView.as_view(),name="get_vikas_khand_by_center"),
    path("billing-form-filters/", BillingFormFilterAPIView.as_view(), name="billing_form_filters"),
    path("center-password-change/", RegUserPasswordUpdateAPIView.as_view(),name="center-password"),
    path("reguser-list/", reguser_list, name="reguser_list"),
    path("demand-generation/", DemandGenerationAPIView.as_view(), name="demand-generation"),
    path("demand-by-center/", DemandByCenterAPIView.as_view(), name="demand-by-center"),
    path("nursery-financial/", NurseryFinancialAPIView.as_view(), name="nursery-financial"),   
    path("nursery-physical/", NurseryPhysicalAPIView.as_view(), name="nursery-physical"),
    path("nursery-physical-recipients/", NurseryPhysicalRecipientAPIView.as_view(), name="nursery-physical-recipients"),
    path("billing-report/update/",UpdateBillingReportAPIView.as_view(),name="billing-report-update",),
    path("download-multiple-receipts/",DownloadMultipleReceiptsAPIView.as_view(),name="download-multiple-receipts",),
    
]