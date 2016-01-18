# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import openerp
from openerp.http import Response, request
from werkzeug import exceptions
from werkzeug.wrappers import Response as WerkzeugResponse


def get_response(self, httprequest, result, explicit_session):
    """
    Override Odoo's default 3 month cookie timeout with our own
    :param httprequest:  An instance of openerp.http.HttpRequest
    :param result: The result to return to the client from openerp.http.route
    :param explicit_session: optional openerp.http.Session
    :return : Returns the result response with a cookie that expires in x hours
    """
    if isinstance(result, Response) and result.is_qweb:
        try:
            result.flatten()
        except(Exception), e:
            if request.db:
                result = request.registry['ir.http']._handle_exception(e)
            else:
                raise

    if isinstance(result, basestring):
        response = WerkzeugResponse(result, mimetype='text/html')
    else:
        response = result

    if httprequest.session.should_save:
        self.session_store.save(httprequest.session)

    cookie_lifespan = 3600*12  # 12 hours, maybe set in config?

    if response.response and not \
            isinstance(response, exceptions.HTTPException):
        response.set_cookie('session_id', httprequest.session.sid,
                            max_age=cookie_lifespan)
    return response


openerp.http.OldRoot = type('Root', (object, ),
                            dict(openerp.http.Root.__dict__))
openerp.http.Root.get_response = get_response
