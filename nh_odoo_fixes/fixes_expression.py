# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.osv.expression import (OR_OPERATOR, AND_OPERATOR, ExtendedLeaf,
                                    create_substitution_leaf, MAGIC_COLUMNS,
                                    normalize_domain, TRUE_LEAF, traceback,
                                    FALSE_LEAF, select_from_where,
                                    NEGATIVE_TERM_OPERATORS,
                                    select_distinct_from_where_not_null)
from openerp.osv import fields
import logging

_logger = logging.getLogger()
# ----------------------------------------
# Parsing
# ----------------------------------------


def _quote(to_quote):
    if '"' not in to_quote:
        return '"%s"' % to_quote
    return to_quote


def parse(self, cr, uid, context):
    """ Transform the leaves of the expression

        The principle is to pop elements from a leaf stack one at a time.
        Each leaf is processed. The processing is a if/elif list of various
        cases that appear in the leafs (many2one, function fields, ...).
        Two things can happen as a processing result:
        - the leaf has been modified and/or new leafs have to be introduced
          in the expression; they are pushed into the leaf stack, to be
          processed right after
        - the leaf is added to the result

        Some internal var explanation:
            :var obj working_model: model object, model containing the field
                (the name provided in the left operand)
            :var list field_path: left operand seen as a path
                 (foo.bar -> [foo, bar])
            :var obj relational_model: relational model of a field (field._obj)
                ex: res_partner.bank_ids -> res.partner.bank
    """

    def to_ids(value, relational_model, context=None, limit=None):
        """
        Normalize a single id or name, or a list of those,
        into a list of ids
        :param {int,long,basestring,list,tuple} value:
            if int, long -> return [value]
            if basestring, convert it into a list of basestrings, then
            if list of basestring ->
                perform a name_search on relational_model for each name
                return the list of related ids
        """
        names = []
        if isinstance(value, basestring):
            names = [value]
        elif value and isinstance(value, (tuple, list)) and \
                all(isinstance(item, basestring) for item in value):
            names = value
        elif isinstance(value, (int, long)):
            return [value]
        if names:
            name_get_list = [name_get[0] for name in names for name_get in
                             relational_model.name_search(
                                 cr, uid, name, [], 'ilike', context=context,
                                 limit=limit)]
            return list(set(name_get_list))
        return list(value)

    def child_of_domain(left, ids, left_model, parent=None, prefix='',
                        context=None):
        """
        Return a domain implementing the child_of operator for
        [(left,child_of,ids)], either as a range using the parent_left/right
        tree lookup fields (when available),
        or as an expanded [(left,in,child_ids)]
        """
        if left_model._parent_store and (not left_model.pool._init):
            # TODO: Improve joins implemented for many with '.', replace by:
            # doms += ['&',(prefix+'.parent_left','<',o.parent_right),
            # (prefix+'.parent_left','>=',o.parent_left)]
            doms = []
            for o in left_model.browse(cr, uid, ids, context=context):
                if doms:
                    doms.insert(0, OR_OPERATOR)
                doms += [AND_OPERATOR, ('parent_left', '<', o.parent_right),
                         ('parent_left', '>=', o.parent_left)]
            if prefix:
                return [(left, 'in', left_model.search(
                    cr, uid, doms, context=context))]
            return doms
        else:
            def recursive_children(ids, model, parent_field):
                if not ids:
                    return []
                ids2 = model.search(cr, uid, [(parent_field, 'in', ids)],
                                    context=context)
                return ids + recursive_children(ids2, model, parent_field)
            return [(left, 'in', recursive_children(
                ids, left_model, parent or left_model._parent_name))]

    def pop():
        """ Pop a leaf to process. """
        return self.stack.pop()

    def push(leaf):
        """ Push a leaf to be processed right after. """
        self.stack.append(leaf)

    def push_result(leaf):
        """ Push a leaf to the results. This leaf has been fully processed
            and validated. """
        self.result.append(leaf)

    self.result = []
    self.stack = [ExtendedLeaf(leaf, self.root_model)
                  for leaf in self.expression]
    # process from right to left; expression is from left to right
    self.stack.reverse()

    while self.stack:
        # Get the next leaf to process
        leaf = pop()

        # Get working variables
        working_model = leaf.model
        if leaf.is_operator():
            left, operator, right = leaf.leaf, None, None
        elif leaf.is_true_leaf() or leaf.is_false_leaf():
            # because we consider left as a string
            left, operator, right = ('%s' % leaf.leaf[0], leaf.leaf[1],
                                     leaf.leaf[2])
        else:
            left, operator, right = leaf.leaf
        field_path = left.split('.', 1)
        field = working_model._columns.get(field_path[0])
        # Neova Health BEGIN
        if not working_model._columns.get(field_path[0]) and \
                field_path[0] == 'id':
            # field 'id' normally is not in the _columns
            # the problem appeared with call
            # search('t4clinical.task.base', [
            # ('responsible_user_ids','in',uid)])
            # -- returned [], due to this issue was looking for
            # t4clinical.task.base ids in project.task ids
            field = fields.integer('fake id field. quick fix')
            field._obj = working_model._name
        # Neova Health END
        if field and field._obj:
            relational_model = working_model.pool.get(field._obj)
        else:
            relational_model = None

        # ----------------------------------------
        # SIMPLE CASE
        # 1. leaf is an operator
        # 2. leaf is a true/false leaf
        # -> add directly to result
        # ----------------------------------------

        if leaf.is_operator() or leaf.is_true_leaf() or leaf.is_false_leaf():
            push_result(leaf)

        # ----------------------------------------
        # FIELD NOT FOUND
        # -> from inherits'd fields -> work on the related model, and add
        #    a join condition
        # -> ('id', 'child_of', '..') -> use a 'to_ids'
        # -> but is one on the _log_access special fields, add directly to
        #    result
        # TODO: make these fields explicitly available in self.columns instead!
        # -> else: crash
        # ----------------------------------------

        elif not field and field_path[0] in working_model._inherit_fields:
            # comments about inherits'd fields
            #  { 'field_name': ('parent_model', 'm2o_field_to_reach_parent',
            #                    field_column_obj, origina_parent_model), ... }
            next_model = working_model.pool.get(
                working_model._inherit_fields[field_path[0]][0])
            leaf.add_join_context(
                next_model, working_model._inherits[next_model._name], 'id',
                working_model._inherits[next_model._name])
            push(leaf)

        elif left == 'id' and operator == 'child_of':
            ids2 = to_ids(right, working_model, context)
            dom = child_of_domain(left, ids2, working_model)
            for dom_leaf in reversed(dom):
                new_leaf = create_substitution_leaf(leaf, dom_leaf,
                                                    working_model)
                push(new_leaf)

        elif not field and field_path[0] in MAGIC_COLUMNS:
            push_result(leaf)

        elif not field:
            raise ValueError("Invalid field %r in leaf %r" % (left, str(leaf)))

        # ----------------------------------------
        # PATH SPOTTED
        # -> many2one or one2many with _auto_join:
        #    - add a join, then jump into linked field: field.remaining on
        #      src_table is replaced by remaining on dst_table,
        #      and set for re-evaluation
        #    - if a domain is defined on the field, add it into evaluation
        #      on the relational table
        # -> many2one, many2many, one2many: replace by an equivalent computed
        #    domain, given by recursively searching on the path's remaining
        # -> note: hack about fields.property should not be necessary anymore
        #    as after transforming the field, it will go through this loop
        #    once again
        # ----------------------------------------

        elif len(field_path) > 1 and field._type == 'many2one' and \
                field._auto_join:
            # res_partner.state_id = res_partner__state_id.id
            leaf.add_join_context(relational_model, field_path[0], 'id',
                                  field_path[0])
            push(create_substitution_leaf(
                leaf, (field_path[1], operator, right), relational_model))

        elif len(field_path) > 1 and field._type == 'one2many' and \
                field._auto_join:
            # res_partner.id = res_partner__bank_ids.partner_id
            leaf.add_join_context(relational_model, 'id', field._fields_id,
                                  field_path[0])
            domain = field._domain(working_model) if callable(field._domain) \
                else field._domain
            push(create_substitution_leaf(
                leaf, (field_path[1], operator, right), relational_model))
            if domain:
                domain = normalize_domain(domain)
                for elem in reversed(domain):
                    push(create_substitution_leaf(leaf, elem,
                                                  relational_model))
                push(create_substitution_leaf(leaf, AND_OPERATOR,
                                              relational_model))

        elif len(field_path) > 1 and field._auto_join:
            raise NotImplementedError('_auto_join attribute not supported on '
                                      'many2many field %s' % left)

        elif len(field_path) > 1 and field._type == 'many2one':
            right_ids = relational_model.search(
                cr, uid, [(field_path[1], operator, right)], context=context)
            leaf.leaf = (field_path[0], 'in', right_ids)
            push(leaf)

        # Making search easier when there is a left operand
        # as field.o2m or field.m2m
        elif len(field_path) > 1 and field._type in ['many2many', 'one2many']:
            right_ids = relational_model.search(
                cr, uid, [(field_path[1], operator, right)], context=context)
            table_ids = working_model.search(
                cr, uid, [(field_path[0], 'in', right_ids)],
                context=dict(context, active_test=False))
            leaf.leaf = ('id', 'in', table_ids)
            push(leaf)

        # -------------------------------------------------
        # FUNCTION FIELD
        # -> not stored: error if no _fnct_search,
        #    otherwise handle the result domain
        # -> stored: management done in the remaining of parsing
        # -------------------------------------------------

        elif isinstance(field, fields.function) and not field.store \
                and not field._fnct_search:
            # this is a function field that is not stored
            # the function field doesn't provide a search function and
            # doesn't store values in the database, so we must ignore it:
            # we generate a dummy leaf.
            leaf.leaf = TRUE_LEAF
            _logger.error(
                "The field '%s' (%s) can not be searched: non-stored "
                "function field without fnct_search",
                field.string, left)
            # avoid compiling stack trace if not needed
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug(''.join(traceback.format_stack()))
            push(leaf)

        elif isinstance(field, fields.function) and not field.store:
            # this is a function field that is not stored
            fct_domain = field.search(cr, uid, working_model, left,
                                      [leaf.leaf], context=context)
            if not fct_domain:
                leaf.leaf = TRUE_LEAF
                push(leaf)
            else:
                # we assume that the expression is valid
                # we create a dummy leaf for forcing the parsing of the
                # resulting expression
                for domain_element in reversed(fct_domain):
                    push(create_substitution_leaf(leaf, domain_element,
                                                  working_model))
                # self.push(
                # create_substitution_leaf(leaf, TRUE_LEAF, working_model))
                # self.push(
                # create_substitution_leaf(leaf, AND_OPERATOR, working_model))

        # -------------------------------------------------
        # RELATIONAL FIELDS
        # -------------------------------------------------

        # Applying recursivity on field(one2many)
        elif field._type == 'one2many' and operator == 'child_of':
            ids2 = to_ids(right, relational_model, context)
            if field._obj != working_model._name:
                dom = child_of_domain(left, ids2, relational_model,
                                      prefix=field._obj)
            else:
                dom = child_of_domain('id', ids2, working_model, parent=left)
            for dom_leaf in reversed(dom):
                push(create_substitution_leaf(leaf, dom_leaf, working_model))

        elif field._type == 'one2many':
            call_null = True

            if right is not False:
                if isinstance(right, basestring):
                    ids2 = [x[0] for x in relational_model.name_search(
                        cr, uid, right, [], operator, context=context,
                        limit=None)
                    ]
                    if ids2:
                        operator = 'in'
                else:
                    if not isinstance(right, list):
                        ids2 = [right]
                    else:
                        ids2 = right
                if not ids2:
                    if operator in ['like', 'ilike', 'in', '=']:
                        # no result found with given search criteria
                        call_null = False
                        push(create_substitution_leaf(leaf, FALSE_LEAF,
                                                      working_model))
                else:
                    ids2 = select_from_where(cr, field._fields_id,
                                             relational_model._table, 'id',
                                             ids2, operator)
                    if ids2:
                        call_null = False
                        o2m_op = 'not in' if operator in \
                            NEGATIVE_TERM_OPERATORS else 'in'
                        push(create_substitution_leaf(
                            leaf, ('id', o2m_op, ids2), working_model))

            if call_null:
                o2m_op = 'in' if operator in \
                    NEGATIVE_TERM_OPERATORS else 'not in'
                push(create_substitution_leaf(
                    leaf, ('id', o2m_op,
                           select_distinct_from_where_not_null(
                               cr, field._fields_id, relational_model._table)),
                    working_model))

        elif field._type == 'many2many':
            rel_table, rel_id1, rel_id2 = field._sql_names(working_model)
            # FIXME
            if operator == 'child_of':
                def _rec_convert(ids):
                    if relational_model == working_model:
                        return ids
                    return select_from_where(cr, rel_id1, rel_table, rel_id2,
                                             ids, operator)

                ids2 = to_ids(right, relational_model, context)
                dom = child_of_domain('id', ids2, relational_model)
                ids2 = relational_model.search(cr, uid, dom, context=context)
                push(create_substitution_leaf(leaf,
                                              ('id', 'in', _rec_convert(ids2)),
                                              working_model))
            else:
                call_null_m2m = True
                if right is not False:
                    if isinstance(right, basestring):
                        res_ids = [x[0] for x in relational_model.name_search(
                            cr, uid, right, [], operator, context=context)]
                        if res_ids:
                            operator = 'in'
                    else:
                        if not isinstance(right, list):
                            res_ids = [right]
                        else:
                            res_ids = right
                    if not res_ids:
                        if operator in ['like', 'ilike', 'in', '=']:
                            # no result found with given search criteria
                            call_null_m2m = False
                            push(create_substitution_leaf(leaf, FALSE_LEAF,
                                                          working_model))
                        else:
                            # operator changed because ids are directly related
                            # to main object
                            operator = 'in'
                    else:
                        call_null_m2m = False
                        m2m_op = 'not in' if operator in \
                            NEGATIVE_TERM_OPERATORS else 'in'
                        push(create_substitution_leaf(
                            leaf, ('id', m2m_op,
                                   select_from_where(
                                       cr, rel_id1, rel_table, rel_id2,
                                       res_ids, operator) or [0]),
                            working_model))

                if call_null_m2m:
                    m2m_op = 'in' if operator in \
                        NEGATIVE_TERM_OPERATORS else 'not in'
                    push(create_substitution_leaf(
                        leaf,
                        ('id', m2m_op, select_distinct_from_where_not_null(
                            cr, rel_id1, rel_table)), working_model))

        elif field._type == 'many2one':
            if operator == 'child_of':
                ids2 = to_ids(right, relational_model, context)
                if field._obj != working_model._name:
                    dom = child_of_domain(left, ids2, relational_model,
                                          prefix=field._obj)
                else:
                    dom = child_of_domain('id', ids2, working_model,
                                          parent=left)
                for dom_leaf in reversed(dom):
                    push(create_substitution_leaf(leaf, dom_leaf,
                                                  working_model))
            else:
                def _get_expression(relational_model, cr, uid, left, right,
                                    operator, context=None):
                    if context is None:
                        context = {}
                    c = context.copy()
                    c['active_test'] = False
                    # Special treatment to ill-formed domains
                    operator = (operator in ['<', '>', '<=', '>=']) and 'in' \
                        or operator

                    dict_op = {'not in': '!=', 'in': '=',
                               '=': 'in', '!=': 'not in'}
                    if isinstance(right, tuple):
                        right = list(right)
                    if (not isinstance(right, list)) and \
                            operator in ['not in', 'in']:
                        operator = dict_op[operator]
                    elif isinstance(right, list) and operator in ['!=', '=']:
                        # for domain (FIELD,'=',['value1','value2'])
                        operator = dict_op[operator]
                    res_ids = [x[0] for x in relational_model.name_search(
                        cr, uid, right, [], operator, limit=None, context=c)]
                    if operator in NEGATIVE_TERM_OPERATORS:
                        # TODO this should not be appended if False in 'right'
                        res_ids.append(False)
                    return left, 'in', res_ids
                # resolve string-based m2o criterion into IDs
                if isinstance(right, basestring) or right and \
                        isinstance(right, (tuple, list)) and \
                        all(isinstance(item, basestring) for item in right):
                    push(create_substitution_leaf(
                        leaf,
                        _get_expression(relational_model, cr, uid, left, right,
                                        operator, context=context),
                        working_model))
                else:
                    # right == [] or right == False and all other cases
                    # are handled by __leaf_to_sql()
                    push_result(leaf)

        # -------------------------------------------------
        # OTHER FIELDS
        # -> datetime fields: manage time part of the datetime
        #    field when it is not there
        # -> manage translatable fields
        # -------------------------------------------------

        else:
            if field._type == 'datetime' and right and len(right) == 10:
                if operator in ('>', '>='):
                    right += ' 00:00:00'
                elif operator in ('<', '<='):
                    right += ' 23:59:59'
                push(create_substitution_leaf(leaf, (left, operator, right),
                                              working_model))

            elif field.translate and right:
                need_wildcard = operator in ('like', 'ilike', 'not like',
                                             'not ilike')
                sql_operator = {'=like': 'like', '=ilike': 'ilike'}.get(
                    operator, operator)
                if need_wildcard:
                    right = '%%%s%%' % right

                inselect_operator = 'inselect'
                if sql_operator in NEGATIVE_TERM_OPERATORS:
                    # negate operator (fix lp:1071710)
                    if sql_operator[:3] == 'not':
                        sql_operator = sql_operator[4:]
                    else:
                        sql_operator = '='
                    inselect_operator = 'not inselect'

                unaccent = self._unaccent if sql_operator.endswith('like') \
                    else lambda x: x

                trans_left = unaccent('value')
                quote_left = unaccent(_quote(left))
                instr = unaccent('%s')

                if sql_operator == 'in':
                    # params will be flatten by to_sql() =>
                    # expand the placeholders
                    instr = '(%s)' % ', '.join(['%s'] * len(right))

                subselect = """(SELECT res_id
                                  FROM ir_translation
                                 WHERE name = %s
                                   AND lang = %s
                                   AND type = %s
                                   AND {trans_left} {operator} {right}
                               ) UNION (
                                SELECT id
                                  FROM "{table}"
                                 WHERE {left} {operator} {right}
                               )
                            """.format(trans_left=trans_left,
                                       operator=sql_operator, right=instr,
                                       table=working_model._table,
                                       left=quote_left)

                params = (
                    working_model._name + ',' + left,
                    context.get('lang') or 'en_US',
                    'model',
                    right,
                    right,
                )
                push(create_substitution_leaf(leaf, ('id', inselect_operator,
                                                     (subselect, params)
                                                     ), working_model))

            else:
                push_result(leaf)

    # ----------------------------------------
    # END OF PARSING FULL DOMAIN
    # -> generate joins
    # ----------------------------------------

    joins = set()
    for leaf in self.result:
        joins |= set(leaf.get_join_conditions())
    self.joins = list(joins)
# openerp.osv.expression.expression.parse = parse
