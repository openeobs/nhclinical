from openerp.osv import orm, fields, osv


class test_activity_data_model(orm.Model):
    _name = 'test.activity.data.model'
    _inherit=['t4.activity.data']
    
    _columns = {
        'field1': fields.text('Field1')
        
    }

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