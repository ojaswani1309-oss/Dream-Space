from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

urlpatterns = [
    path("admin/", admin.site.urls),
    path("forgot-password/", auth_views.PasswordResetView.as_view(
        template_name="forgot_password.html", success_url=reverse_lazy("password_reset_done")),
        name="forgot_password"),
    path("forgot-password/sent/", auth_views.PasswordResetDoneView.as_view(
        template_name="reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="reset_confirm.html", success_url=reverse_lazy("password_reset_complete")),
        name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="reset_complete.html"), name="password_reset_complete"),
    path("", include("core.urls")),
]
