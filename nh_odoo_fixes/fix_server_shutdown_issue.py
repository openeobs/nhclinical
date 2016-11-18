# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import errno
import platform
import socket

from openerp.service.server import CommonServer


def fixed_close_socket(self, sock):
    """ Closes a socket instance cleanly

    :param sock: the network socket to close
    :type sock: socket.socket
    """
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except socket.error, e:
        if e.errno == errno.EBADF:
            # Werkzeug > 0.9.6 closes the socket itself (see commit
            # https://github.com/mitsuhiko/werkzeug/commit/4d8ca089)
            return
        # On OSX, socket shutdowns both sides if any side closes it
        # causing an error 57 'Socket is not connected' on shutdown
        # of the other side (or something), see
        # http://bugs.python.org/issue4397
        # note: stdlib fixed test, not behavior
        if e.errno != errno.ENOTCONN or platform.system() not in ['Darwin',
                                                                  'Windows']:
            raise
    sock.close()


CommonServer.close_socket = fixed_close_socket
