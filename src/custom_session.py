import requests
from http.cookies import SimpleCookie

class CustomSession(requests.Session):
    def get_cookie_header_value(self, header_value):
        cookies = {}
        if not header_value:
            return cookies
            
        # Handle comma-separated cookies
        cookie_strings = [h.strip() for h in header_value.split(',')]
        
        for cookie_str in cookie_strings:
            cookie = SimpleCookie()
            try:
                cookie.load(cookie_str)
                for key, morsel in cookie.items():
                    cookies[key] = morsel.value
            except:
                continue
                
        return cookies

    def merge_cookies(self, response):
        # Get Set-Cookie header - CaseInsensitiveDict uses get()
        cookie_header = response.headers.get('Set-Cookie')
        if cookie_header:
            cookies = self.get_cookie_header_value(cookie_header)
            for key, value in cookies.items():
                self.cookies.set(key, value)

    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        self.merge_cookies(response)
        return response