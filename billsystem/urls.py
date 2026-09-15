from django.urls import path
from .views import VarietyDetailAPIView,UdyanCropStandardDetailAPIView,UdyanBillDetailAPIView,UdyanBillAPIView,UdyanCropStandardAPIView,DownloadMultipleReceiptsAPIView,UpdateBillingReportAPIView,BillingItemBulkUpload, BillingItemList,BillingReportList,NurseryPhysicalAPIView,NurseryPhysicalRecipientAPIView,RegUserPasswordUpdateAPIView,NurseryFinancialAPIView,BillingFormFilterAPIView,reguser_list,DemandGenerationAPIView,DemandByCenterAPIView,LoginAPIView,GetVikasKhandByCenterAPIView, UpdateBillingItemQuantity,CenterComponentDetailListAPIView,SchemeCreateAPIView,ComponentInvestmentCreateAPIView,BeneficiaryRegistrationAPIView,get_bank_details
from .views import CenterLinkAPIView, CenterLinkDetailAPIView,CenterLinkDetailCenterAPIView
from .views import (
    SalaryAttendanceReportAPIView,MonthAttendanceReportListAPIView,MonthAttendanceReportDetailAPIView,
    SalaryAttendanceReportDetailAPIView
)
from .views import (BootstrapAPIView,
        MasterSettingAPIView,
    
        CentreListAPIView,
        VarietyListAPIView,
    
        StandardListAPIView,
        StandardDetailAPIView,
    
        PurchaseListCreateAPIView,
        PurchaseDetailAPIView,
    
        AllocationListCreateAPIView,
        AllocationDetailAPIView,
    
        DistributionListCreateAPIView,
        DistributionDetailAPIView,
    )
from .views import (
    LibraryCategoryListCreateView,
    LibraryCategoryDetailView,
    LibraryDocumentListCreateView,
    LibraryDocumentDetailView,MonthReportListAPIView,MonthReportDetailAPIView,
)

from .views import (
    KisanApplicationAPIView,
    KisanPersonalLandDetailsUpdateAPIView,
    KisanPlanTechnicalBankUpdateAPIView,
    KisanApplicationDocumentsUpdateAPIView,
)

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
   
###OTHER PART################   
   
    path("udyan/crop-standards/",UdyanCropStandardAPIView.as_view(),name="udyan-crop-standards",),
    path("udyan/crop-standards/<int:pk>/",UdyanCropStandardDetailAPIView.as_view(),name="udyan-crop-standard-detail",),

    # Bills
    path("udyan/bills/",UdyanBillAPIView.as_view(),name="udyan-bills",),
    path("udyan/bills/<int:pk>/",UdyanBillDetailAPIView.as_view(),name="udyan-bill-detail",),
    path("kishanbeej/bootstrap/",BootstrapAPIView.as_view(),name="kishan-beej-bootstrap",),
    path("kishanbeej/master/",MasterSettingAPIView.as_view(),name="kishan-beej-master",),
    path("centres/",CentreListAPIView.as_view(),name="kishan-beej-centres",),
    path("kishanbeej/varieties/",VarietyListAPIView.as_view(),name="kishan-beej-varieties",), 
    path("kishanbeej/varieties/<int:pk>/",VarietyDetailAPIView.as_view(),name="kishan-beej-varieties",),
    path("kishanbeej/standards/",StandardListAPIView.as_view(),name="kishan-beej-standards",),
    path("kishanbeej/standards/<int:pk>/",StandardDetailAPIView.as_view(),name="kishan-beej-standard-detail",),
    path("kishanbeej/purchases/",PurchaseListCreateAPIView.as_view(),name="kishan-beej-purchases",),
    path("kishanbeej/purchases/<int:pk>/",PurchaseDetailAPIView.as_view(),name="kishan-beej-purchase-detail",),
    path("kishanbeej/allocations/",AllocationListCreateAPIView.as_view(),name="kishan-beej-allocations",),
    path("kishanbeej/allocations/<int:pk>/",AllocationDetailAPIView.as_view(),name="kishan-beej-allocation-detail",),
    path("kishanbeej/distributions/",DistributionListCreateAPIView.as_view(),name="kishan-beej-distributions",),
    path("kishanbeej/distributions/<int:pk>/",DistributionDetailAPIView.as_view(),name="kishan-beej-distribution-detail",),
    path("library/categories/",LibraryCategoryListCreateView.as_view(),name="library-categories"),
    path("library/categories/<int:pk>/",LibraryCategoryDetailView.as_view(),name="library-category-detail"),
    path("library/documents/",LibraryDocumentListCreateView.as_view(),name="library-documents"),
    path("library/documents/<int:pk>/",LibraryDocumentDetailView.as_view(),name="library-document-detail"),
    path("month-reports/",MonthReportListAPIView.as_view(),name="month-report-list"),
    path("month-reports/<int:pk>/",MonthReportDetailAPIView.as_view(),name="month-report-detail"),
    path("kisan-application/", KisanApplicationAPIView.as_view(), name="kisan-application"),
    path("kisan-personal-land-update/", KisanPersonalLandDetailsUpdateAPIView.as_view(), name="kisan-personal-land-update"),
    path("kisan-plan-technical-bank-update/", KisanPlanTechnicalBankUpdateAPIView.as_view(), name="kisan-plan-technical-bank-update"),
    path("kisan-application-documents-update/", KisanApplicationDocumentsUpdateAPIView.as_view(), name="kisan-application-documents-update"),
    path("center-links/",CenterLinkAPIView.as_view(),name="center-links"),
    path("center-links/<int:pk>/",CenterLinkDetailAPIView.as_view(),name="center-link-detail"),
    path("center-link-details/",CenterLinkDetailAPIView.as_view(),name="center-link-details"),
    path("center-link-details-bycenter/",CenterLinkDetailCenterAPIView.as_view(),name="center-link-detail"),
    path("center-link-details-bycenter/<int:pk>/",CenterLinkDetailCenterAPIView.as_view(),name="center-link-detail"),
    path("salary-attendance-reports/",SalaryAttendanceReportAPIView.as_view(),name="salary-attendance-reports"),
    path("salary-attendance-reports/<int:pk>/",SalaryAttendanceReportDetailAPIView.as_view(),name="salary-attendance-report-detail"),
    path("month-attendance-reports/",MonthAttendanceReportListAPIView.as_view(),name="month-attendance-reports"),
    path("month-attendance-reports/<int:pk>/",MonthAttendanceReportDetailAPIView.as_view(),name="month-attendance-report-detail"),
]
