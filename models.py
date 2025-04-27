from django.db import models

class OnionSite(models.Model):
    url = models.URLField(unique=True, max_length=500)  # .onion link
    extracted_text = models.TextField(blank=True, null=True)  # Page text
    hyperlinks = models.JSONField(default=list)  # List of hyperlinks on the page
    keyword = models.CharField(max_length=100, blank=True, null=True)  # Keyword used for crawling
    crawl_date = models.DateTimeField(auto_now_add=True)  # Timestamp of crawl
    snapshot = models.ImageField(upload_to='snapshots/', blank=True, null=True)  # Screenshot of the page

    def __str__(self):
        return self.url
