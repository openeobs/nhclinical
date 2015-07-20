from openerp.osv import orm, fields


class test_model_a(orm.Model):
    _name = 'test_model_a'

    _columns = {
        'name': fields.char(),
        'a_ids': fields.many2many('test_model_b', 'b_a_rel',
                                  'test_model_a_id', 'test_model_b_id')
    }

class test_model_b(orm.Model):
    _name = 'test_model_b'

    _columns = {
        'name': fields.char(),
    }
