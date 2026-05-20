from django.urls import path
from . import views

urlpatterns = [
    path("", views.PaymentHistoryView.as_view(), name="payment-history"),
    path("initiate/", views.initiate_payment, name="initiate-payment"),
    path("mpesa/callback/", views.mpesa_callback, name="mpesa-callback"),
    path("<uuid:pk>/", views.payment_detail, name="payment-detail"),
]
