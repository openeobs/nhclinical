__author__ = 'colinwren'
from openerp.http import *
from openerp.tests.common import SingleTransactionCase
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

class TestCookieFix(SingleTransactionCase):

    def setUp(self):
        """ Set up an werkzeug environment so we can create the root odoo server
        app and send Response objects through it
        :return:
        """
        env_build = EnvironBuilder(method='GET', path='/web/database/selector')
        self.env = env_build.get_environ()
        self.req = Request(self.env)
        res_txt = '<html><head><title>Test</title></head><body>' + \
                  'Test</body></html>'
        self.result = res_txt

    def test_nh_cookie_fix(self):
        """ Using an instance of the app with the cookie fix applied and get a
        response using the usual database way of working
        :return:
        """
        root = Root()
        self.req.app = root
        explicit_session = root.setup_session(self.req)
        root.setup_db(self.req)
        root.setup_lang(self.req)
        request = root.get_request(self.req)

        def _dispatch_nodb():
            try:
                func, arguments = root.nodb_routing_map.bind_to_environ(
                    request.httprequest.environ).match()
            except werkzeug.exceptions.HTTPException, e:
                return request._handle_exception(e)
            request.set_handler(func, arguments, "none")
            result = request.dispatch()
            return result

        with request:
            result = _dispatch_nodb()
        response = root.get_response(request, result, explicit_session)
        cookie = [h for h in response.headers if h[0] == 'Set-Cookie'][0]
        cookies = [l for l in cookie[1].split('; ')]
        cookie_data = [kv.split('=') for kv in cookies]
        cookie_age = [int(c[1]) for c in cookie_data if c[0] == 'Max-Age'][0]
        self.assertEqual(cookie_age, 3600*12,
                         'Our cookie fix is not functioning as expected')

    def test_original_cookie_fix(self):
        """ Using an instance of the app with the original cookie fix applied
        and get a response using the usual database way of working
        :return:
        """
        root = openerp.http.OldRoot()
        self.req.app = root
        explicit_session = root.setup_session(self.req)
        root.setup_db(self.req)
        root.setup_lang(self.req)
        request = root.get_request(self.req)

        def _dispatch_nodb():
            try:
                func, arguments = root.nodb_routing_map.bind_to_environ(
                    request.httprequest.environ).match()
            except werkzeug.exceptions.HTTPException, e:
                return request._handle_exception(e)
            request.set_handler(func, arguments, "none")
            result = request.dispatch()
            return result

        with request:
            result = _dispatch_nodb()
        response = root.get_response(request, result, explicit_session)
        cookie = [h for h in response.headers if h[0] == 'Set-Cookie'][0]
        cookies = [l for l in cookie[1].split('; ')]
        cookie_data = [kv.split('=') for kv in cookies]
        cookie_age = [int(c[1]) for c in cookie_data if c[0] == 'Max-Age'][0]
        err = 'Original cookie fix is not functioning as expected'
        self.assertNotEqual(cookie_age, 3600*12, err)

    def test_sending_string_response(self):
        """ Sending a base string as a response and expecting it to be converted
        to a response with cookie set to cookie fix time
        :return:
        """
        root = Root()
        self.req.app = root
        explicit_session = root.setup_session(self.req)
        root.setup_db(self.req)
        root.setup_lang(self.req)
        request = root.get_request(self.req)
        result = 'This is an example basestring response'
        response = root.get_response(request, result, explicit_session)
        cookie = [h for h in response.headers if h[0] == 'Set-Cookie'][0]
        cookies = [l for l in cookie[1].split('; ')]
        cookie_data = [kv.split('=') for kv in cookies]
        cookie_age = [int(c[1]) for c in cookie_data if c[0] == 'Max-Age'][0]
        err = 'Our cookie fix is not converting basestring as expected'
        self.assertEqual(cookie_age, 3600*12, err)

    # def test_sending_odoo_qweb_template_response(self):
    #     """ Sending a response that is a 'qweb template' via a Odoo Response
    #     instance and making sure no exception is thrown and response has cookie
    #     fix time
    #     :return:
    #     """
    #     env_build = EnvironBuilder(method='GET', path='/web/report')
    #     env = env_build.get_environ()
    #     env['REMOTE_ADDR'] = env.get('REMOTE_ADDR', '127.0.0.1')
    #     req = Request(env)
    #     root = Root()
    #     # root.__call__(env, Response('hi'))
    #     req.app = root
    #     explicit_session = root.setup_session(req)
    #     root.setup_db(req)
    #     root.setup_lang(req)
    #
    #     request = root.get_request(req)
    #     request.session.authenticate(self.registry.db_name, 'winifred',
    #                                      'winifred')
    #
    #
    #     with request:
    #
    #     response = root.get_response(request, result, explicit_session)
    #     self.assertEqual(response.text, 'This is a test',
    #                      'Qweb template did not render properly')
    #     cookie = [h for h in response.headers if h[0] == 'Set-Cookie'][0]
    #     cookies = [l for l in cookie[1].split('; ')]
    #     cookie_data = [kv.split('=') for kv in cookies]
    #     cookie_age = [int(c[1]) for c in cookie_data if c[0] == 'Max-Age'][0]
    #     err = 'Our cookie fix is not working with Odoo Response instance'
    #     self.assertEqual(cookie_age, 3600*12, err)