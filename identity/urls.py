from .views import auth, group, permission

urlpatterns = auth.urlpatterns + group.urlpatterns + permission.urlpatterns