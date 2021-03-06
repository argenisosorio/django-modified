import re

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin


class SecurityMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.sts_seconds = settings.SECURE_HSTS_SECONDS
        self.sts_include_subdomains = settings.SECURE_HSTS_INCLUDE_SUBDOMAINS
        self.content_type_nosniff = settings.SECURE_CONTENT_TYPE_NOSNIFF
        self.xss_filter = settings.SECURE_BROWSER_XSS_FILTER
        self.redirect = settings.SECURE_SSL_REDIRECT
        self.redirect_host = settings.SECURE_SSL_HOST
        self.redirect_exempt = [re.compile(r) for r in settings.SECURE_REDIRECT_EXEMPT]
        self.redirect_urls = [re.compile(r) for r in settings.SECURE_REDIRECT_URLS]
        self.get_response = get_response

    def process_request(self, request):
        path = request.path.lstrip("/")
        secure = False
        ignore = False
        if (self.redirect and not request.is_secure() and 
                any(pattern.search(path)
                        for pattern in self.redirect_exempt)):
            ignore = True
        if not ignore:
            if (self.redirect and not request.is_secure() and
                    any(pattern.search(path)
                       for pattern in self.redirect_urls)):
                secure = True
                return self._redirect(request, secure)
    
    def _redirect(self, request, secure):
         if secure:
             host = self.redirect_host or request.get_host()
             return HttpResponsePermanentRedirect(
                 "https://%s%s" % (host, request.get_full_path())
             )
         else:  
             host = self.redirect_host or request.get_host()
             return HttpResponsePermanentRedirect(
                 "http://%s%s" % (host, request.get_full_path())                                                                                                   
             )

    def process_response(self, request, response):
        if (self.sts_seconds and request.is_secure() and
                'strict-transport-security' not in response):
            sts_header = "max-age=%s" % self.sts_seconds

            if self.sts_include_subdomains:
                sts_header = sts_header + "; includeSubDomains"

            response["strict-transport-security"] = sts_header

        if self.content_type_nosniff and 'x-content-type-options' not in response:
            response["x-content-type-options"] = "nosniff"

        if self.xss_filter and 'x-xss-protection' not in response:
            response["x-xss-protection"] = "1; mode=block"

        return response

