from openerp.osv import orm, fields, osv


class test_activity_data_model(orm.Model):
    _name = 'test.activity.data.model'
    _inherit=['nh.activity.data']
    
    _columns = {
        'field1': fields.text('Field1')
        
    }
    
        
    def __init__(self, pool, cr):
        activity_model = pool['nh.activity']

        super(test_activity_data_model, self).__init__(pool, cr)
    
    _start_handler_event = False
    _complete_handler_event = False
    def handle_data_complete(self, cr, uid, event):
        self._complete_handler_event = event

    def handle_data_start(self, cr, uid, event):
        self._start_handler_event = event
        
#     def _register_hook(self, cr):
#         uid = 1
#         print "Post-LOAD TEST:"
#         activity_model = self.pool['nh.activity']
#         data_model = self.pool['nh.activity.data']
#         activity_id = data_model.create_activity(cr, uid, {}, {})
#         activity_model.start(cr, uid, activity_id)
#         activity_model.complete(cr, uid, activity_id)
#         import pdb; pdb.set_trace()
        

# class res_partner_mail(orm.Model):
#     # for some reason 'notification_email_send' getting removed from values in the middle of user.create() 
#     #_name = "res.partner"
#     _inherit = 'res.partner'
#     _mail_flat_thread = False
# 
#     _columns = {
#         'notification_email_send': fields.selection([
#             ('none', 'Never'),
#             ('email', 'Incoming Emails only'),
#             ('comment', 'Incoming Emails and Discussions'),
#             ('all', 'All Messages (discussions, emails, followed system notifications)'),
#             ], 'Receive Messages by Email', required=True,
#             help="Policy to receive emails for new messages pushed to your personal Inbox:\n"
#                     "- Never: no emails are sent\n"
#                     "- Incoming Emails only: for messages received by the system via email\n"
#                     "- Incoming Emails and Discussions: for incoming emails along with internal discussions\n"
#                     "- All Messages: for every notification you receive in your Inbox"),
#     }
#     _defaults = {
#         'notification_email_send': lambda *args: 'comment'
#     }