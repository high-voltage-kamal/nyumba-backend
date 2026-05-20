from django.urls import path
from . import views

urlpatterns = [
    # Public browse
    path("", views.ListingListView.as_view(), name="listing-list"),
    path("<uuid:pk>/", views.ListingDetailView.as_view(), name="listing-detail"),
    path("<uuid:pk>/contact/", views.track_contact_click, name="listing-contact"),

    # Landlord: manage listings
    path("my/", views.MyListingsView.as_view(), name="my-listings"),
    path("create/", views.ListingCreateView.as_view(), name="listing-create"),
    path("<uuid:pk>/edit/", views.ListingUpdateView.as_view(), name="listing-edit"),
    path("<uuid:pk>/taken/", views.mark_listing_taken, name="listing-taken"),
    path("<uuid:pk>/delete/", views.delete_listing, name="listing-delete"),

    # Photos
    path("<uuid:pk>/photos/", views.upload_photo, name="photo-upload"),
    path("<uuid:listing_pk>/photos/<int:photo_pk>/", views.delete_photo, name="photo-delete"),

    # Tenant actions
    path("<uuid:pk>/save/", views.toggle_save_listing, name="listing-save"),
    path("saved/", views.SavedListingsView.as_view(), name="saved-listings"),
    path("<uuid:pk>/report/", views.report_listing, name="listing-report"),

    # Location data
    path("estates/", views.list_estates, name="list-estates"),
    path("counties/", views.list_counties, name="list-counties"),
]
