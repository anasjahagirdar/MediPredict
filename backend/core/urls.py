from django.urls import path

from .views import (
    DashboardRiskTrendView,
    DashboardScanHistoryView,
    DashboardSummaryView,
    DashboardSymptomFrequencyView,
    DownloadReportView,
    LoginView,
    LogoutView,
    PredictDiseaseView,
    RefreshView,
    RegisterView,
)


urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/token/refresh/', RefreshView.as_view(), name='auth-token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('predict/', PredictDiseaseView.as_view(), name='predict'),
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('dashboard/risk-trend/', DashboardRiskTrendView.as_view(), name='dashboard-risk-trend'),
    path('dashboard/symptom-frequency/', DashboardSymptomFrequencyView.as_view(), name='dashboard-symptom-frequency'),
    path('dashboard/scan-history/', DashboardScanHistoryView.as_view(), name='dashboard-scan-history'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('history/', DashboardScanHistoryView.as_view(), name='history'),
    path('dashboard/stats/', DashboardSummaryView.as_view(), name='dashboard-stats'),
    path('reports/download/<int:record_id>/', DownloadReportView.as_view(), name='report-download'),
]
