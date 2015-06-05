__author__ = 'colinwren'
from openerp.http import *
from openerp.tests.common import SingleTransactionCase
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

class TestCookieFix(SingleTransactionCase):

    def setUp(self):
        env_build = EnvironBuilder(method='GET', path='/web/database/selector')
        self.env = env_build.get_environ()
        self.req = Request(self.env)
        res_txt = '<html><head><title>Test</title></head><body>Test</body></html>'
        self.result = res_txt


    def test_nh_cookie_fix(self):
        root = Root()
        self.req.app = root
        explicit_session = root.setup_session(self.req)
        root.setup_db(self.req)
        root.setup_lang(self.req)
        request = root.get_request(self.req)

        def _dispatch_nodb():
            try:
                func, arguments = root.nodb_routing_map.bind_to_environ(request.httprequest.environ).match()
            except werkzeug.exceptions.HTTPException, e:
                return request._handle_exception(e)
            request.set_handler(func, arguments, "none")
            result = request.dispatch()
            return result


        with request:
            result = _dispatch_nodb()
        response = root.get_response(request, result, explicit_session)
        cookie = [h for h in response.headers if h[0] == 'Set-Cookie'][0]
        cookie_data = [kv.split('=') for kv in [l for l in cookie[1].split('; ')]]
        cookie_age = [int(c[1]) for c in cookie_data if c[0] == 'Max-Age'][0]
        self.assertEqual(cookie_age, 3600*12, 'Our cookie fix is not functioning as expected')

    def test_original_cookie_fix(self):
        root = openerp.http.OldRoot()
        self.req.app = root
        explicit_session = root.setup_session(self.req)
        root.setup_db(self.req)
        root.setup_lang(self.req)
        request = root.get_request(self.req)

        def _dispatch_nodb():
            try:
                func, arguments = root.nodb_routing_map.bind_to_environ(request.httprequest.environ).match()
            except werkzeug.exceptions.HTTPException, e:
                return request._handle_exception(e)
            request.set_handler(func, arguments, "none")
            result = request.dispatch()
            return result


        with request:
            result = _dispatch_nodb()
        response = root.get_response(request, result, explicit_session)
        cookie = [h for h in response.headers if h[0] == 'Set-Cookie'][0]
        cookie_data = [kv.split('=') for kv in [l for l in cookie[1].split('; ')]]
        cookie_age = [int(c[1]) for c in cookie_data if c[0] == 'Max-Age'][0]
        self.assertNotEqual(cookie_age, 3600*12, 'Original cookie fix is not functioning as expected')



