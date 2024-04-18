from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse

class StaticViewSitemap(Sitemap):
    def items(self):
        return ['index','Contact','FAQ','SubmitTicket','GettingStarted','FreeForSigners','PlansAndPricing']
    def location(self, item):
        return reverse(item)