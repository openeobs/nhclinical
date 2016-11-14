# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.osv.fields import many2many


def new_set(self, cr, model, id, name, values, user=None, context=None):
    if not context:
        context = {}
    if not values:
        return
    rel, id1, id2 = self._sql_names(model)
    obj = model.pool[self._obj]
    for act in values:
        if not (isinstance(act, list) or isinstance(act, tuple)) or not act:
            continue
        if act[0] == 0:
            idnew = obj.create(cr, user, act[2], context=context)
            cr.execute('insert into '+rel+' ('+id1+','+id2+') values (%s,%s)',
                       (id, idnew))
        elif act[0] == 1:
            obj.write(cr, user, [act[1]], act[2], context=context)
        elif act[0] == 2:
            obj.unlink(cr, user, [act[1]], context=context)
        elif act[0] == 3:
            cr.execute(
                'delete from '+rel+' where '+id1+'=%s and '+id2+'=%s',
                (id, act[1])
            )
        elif act[0] == 4:
            # following queries are in the same transaction
            # so should be relatively safe
            cr.execute(
                'SELECT 1 FROM '+rel+' WHERE '+id1+' = %s and '+id2+' = %s',
                (id, act[1])
            )
            if not cr.fetchone():
                cr.execute(
                    'insert into '+rel+' ('+id1+','+id2+') values (%s,%s)',
                    (id, act[1])
                )
        elif act[0] == 5:
            cr.execute('delete from '+rel+' where ' + id1 + ' = %s', (id,))
        elif act[0] == 6:

            d1, d2, tables = obj.pool.get('ir.rule').domain_get(
                cr, user, obj._name, context=context)
            if d1:
                d1 = ' and ' + ' and '.join(d1)
            else:
                d1 = ''
            cr.execute(
                'delete from '+rel+' where '+id1+'=%s AND ' +
                id2+' IN (SELECT '+rel+'.'+id2+' FROM '+rel+', ' +
                ','.join(tables)+' WHERE '+rel+'.'+id1+'=%s AND '+rel+'.' +
                id2+' = '+obj._table+'.id '+d1+')', [id, id]+d2)
            # NHC BEGIN
            # Original: for act_nbr in act[2]
            # duplicate ids have to be removed
            for act_nbr in set(act[2]):
                # NHC END
                cr.execute(
                    'insert into '+rel+' ('+id1+','+id2+') values (%s, %s)',
                    (id, act_nbr)
                )


many2many.set = new_set
