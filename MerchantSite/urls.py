from django.contrib import admin
from django.urls import path,include
from MerchantSite.views import CreateTenantView,AddCustomerDetails,SeedKnowledgeBaseView,ChannelSeederView,CustomerSeederView,CustomUserSeederView,TicketSeederView,SendEmailAPIView,UpdateUserEmailView

urlpatterns = [
    # path('addMerchant/',create_tenant),
    path('create-tenant/', CreateTenantView.as_view(), name='create-tenant'),
    path('add-customer/',AddCustomerDetails.as_view()),
    path('merchant-sedding/',CustomerSeederView.as_view()),
    path('customUser-seeding/',CustomUserSeederView.as_view()),
    path('customUser-EmailUpdate/',UpdateUserEmailView.as_view()),
    path('sendMail/',SendEmailAPIView.as_view()),
    path('ticket-seeding/',TicketSeederView.as_view()),
    path('channel-seeding/',ChannelSeederView.as_view()),
    path('knowledgebase-seeding/',SeedKnowledgeBaseView.as_view()),





]
