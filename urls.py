from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [	path("", views.index, name="home"),
    			path("index.html", views.index, name="index"),
	            path("UserLogin", views.UserLogin, name="UserLogin"),
                path("register", views.register, name="register"),
				path("UserLoginAction", views.UserLoginAction, name="UserLoginAction"),
                path("dashboard", views.dashboard, name="dashboard"),  # New dashboard route
    			path("logout", views.user_logout, name="logout"), 
                path('search', views.search_onion_links, name='search_onion_links'),
                path("most-words-analysis/", views.MostWords, name="most_words_analysis"),
                path('view-all-crawled/', views.ViewAllCrawled, name='ViewAllCrawled'),
                path("category-analysis/", views.category_analysis, name="category_analysis"),
                path('crawled-detail/<int:site_id>/', views.CrawledDetail, name='CrawledDetail'),
            
    			path("onion/", views.view_onion_data, name="view_onion_data"),
                path("onion_detail/<int:onion_id>/", views.onion_detail, name="onion_detail"),  # ✅ Fetch all .onion URLs

				path("CrawlWeb", views.CrawlWeb, name="CrawlWeb"),
				path("get_crawled_data", views.get_crawled_data, name="get_crawled_data"),
				path("CrawlWebAction", views.CrawlWebAction, name="CrawlWebAction"),
				path("TextExtraction", views.TextExtraction, name="TextExtraction"),
				path("Category", views.Category, name="Category"),
				path("MostWords", views.MostWords, name="MostWords"),
		    ]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)