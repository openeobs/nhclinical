# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging
import mock
import openerp
import psycopg2
import werkzeug

from openerp.http import Root, Response
from openerp.modules.registry import RegistryManager
from openerp.tests import DB as DB_NAME
from openerp.tests.common import SingleTransactionCase
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request


_logger = logging.getLogger(__name__)


class TestCookieFix(SingleTransactionCase):

    def setUp(self):
        """
        Set up a Werkzeug environment, create the root Odoo's server app
        for sending Response objects through it.
        """
        env_build = EnvironBuilder(method='GET', path='/web/database/selector')
        self.env = env_build.get_environ()
        self.req = Request(self.env)

    def test_01_nh_cookie_fix(self):
        """Using an instance of the app with the cookie fix applied
        and get a response using the usual database way of working.
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

    def test_02_original_cookie_fix(self):
        """Using an instance of the app with the original cookie fix applied
        and get a response using the usual database way of working.
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

    def test_03_sending_string_response(self):
        """
        Sending a base string as a response and expecting it to be converted
        to a response with cookie set to cookie fix time.
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

    def test_04_sending_odoo_qweb_template_response(self):
        """
        Test that an Odoo's response is correctly processed
        and has our 'cookies time fix'.

        Send a 'qweb template' response via a Odoo's Response instance.
        Make sure that the Response.flatten() method is called
        and the response has our 'cookies time fix'.
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

        # Set the 'template' property
        # to make the object pass the 'is_qweb' check.
        result.template = 'fake_template'

        # Mock the Response.flatten() method
        # (it's not what is being tested here)
        # and check the mock has actually been called.
        def log_mock_called():
            _logger.debug(
                'Mock of Response.flatten() method called during the test')

        with mock.patch.object(Response, 'flatten',
                               side_effect=log_mock_called) as mock_method:
            response = root.get_response(request, result, explicit_session)

        mock_method.assert_any_call()

        # Assert that our response has the expected cookies, correctly set
        cookie = [h for h in response.headers if h[0] == 'Set-Cookie'][0]
        cookies = [l for l in cookie[1].split('; ')]
        cookie_data = [kv.split('=') for kv in cookies]
        cookie_age = [int(c[1]) for c in cookie_data if c[0] == 'Max-Age'][0]
        self.assertEqual(cookie_age, 3600*12,
                         'Our cookie fix is not functioning as expected')

    def test_05_raising_exception_during_qweb_response_rendering(self):
        """
        Test that an exception is raised during an Odoo's response processing.

        This test use a double 'mocking' strategy:
            - Python's mock library, to mock a method and make it returning
              the exception
            - Odoo's _patch_method(), to swap an Odoo's model's method
              with another custom-defined one
        """
        root = Root()
        self.req.app = root
        explicit_session = root.setup_session(self.req)
        self.req.session.db = DB_NAME  # put DB name into request session data
        root.setup_lang(self.req)
        request = root.get_request(self.req)

        self.assertIsNotNone(request.session.db,
                             'Database not in the request object. '
                             'Test aborted.')

        # Extract and hack part of the Odoo's Root.dispatch() method,
        # and use it to generate a valid Odoo's Response object.
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
            db = request.session.db
            if db:
                RegistryManager.check_registry_signaling(db)
                try:
                    with openerp.tools.mute_logger('openerp.sql_db'):
                        ir_http = request.registry['ir.http']
                except (AttributeError, psycopg2.OperationalError):
                    # psycopg2 error or attribute error while constructing
                    # the registry. That means the database probably does
                    # not exists anymore or the code doesnt match the db.
                    # Log the user out and fall back to nodb
                    request.session.logout()
                    result = _dispatch_nodb()
                else:
                    result = ir_http._dispatch()
                    RegistryManager.signal_caches_change(db)
            else:
                result = _dispatch_nodb()

            # Set the 'template' property to make the Response object
            # pass the 'is_qweb' check.
            result.template = 'fake_template'

            # Mock the Response.flatten() method
            # (because it's not what is being tested here)
            # and check that the mock has actually been called.
            def log_mock_called():
                _logger.debug(
                    'Mock of Response.flatten() method called during the test')
                raise Exception('Expected exception raised during the test.')

            # This method is called (by the Odoo's model)
            # instead of the 'swapped' one below.
            def mock_handle_exception(*args, **kwargs):
                e = args[1]
                return 'Exception: {}'.format(e)

            with mock.patch.object(Response, 'flatten',
                                   side_effect=log_mock_called) as mock_method:
                # Use Odoo's 'patching' way to swap a method,
                # called inside the get_response() method,
                # with another defined here above.
                request.registry['ir.http']._patch_method(
                    '_handle_exception', mock_handle_exception)

                # eventually run the method to test !
                response = root.get_response(request, result, explicit_session)

                # stop the Odoo's patcher
                request.registry['ir.http']._revert_method('_handle_exception')

        mock_method.assert_any_call()
        self.assertIn('Exception: Expected exception raised during the test.',
                      response.response)

        # Assert that our response has the expected cookies, correctly set
        cookie = [h for h in response.headers if h[0] == 'Set-Cookie'][0]
        cookies = [l for l in cookie[1].split('; ')]
        cookie_data = [kv.split('=') for kv in cookies]
        cookie_age = [int(c[1]) for c in cookie_data if c[0] == 'Max-Age'][0]
        self.assertEqual(cookie_age, 3600*12,
                         'Our cookie fix is not functioning as expected')
