import openerp

def _read_group_fill_results(self, cr, uid, domain, groupby, remaining_groupbys,
                             aggregated_fields, count_field,
                             read_group_result, read_group_order=None, context=None):
    """Helper method for filling in empty groups for all possible values of
       the field being grouped by"""
    # self._group_by_full should map groupable fields to a method that returns
    # a list of all aggregated values that we want to display for this field,
    # in the form of a m2o-like pair (key,label).
    # This is useful to implement kanban views for instance, where all columns
    # should be displayed even if they don't contain any record.

    # Grab the list of all groups that should be displayed, including all present groups
    
    # NHC BEGIN
    # ORIGINAL: present_group_ids = [x[groupby][0] for x in read_group_result if x[groupby]]
    present_group_ids = [x[groupby] for x in read_group_result if x[groupby]]
    # NHC END
    all_groups,folded = self._group_by_full[groupby](self, cr, uid, present_group_ids, domain,
                                              read_group_order=read_group_order,
                                              access_rights_uid=openerp.SUPERUSER_ID,
                                              context=context)
    ##### NHC BEGIN
    all_group_tuples = {k: (k,v) for k, v in all_groups}
    #### NHC END
    result_template = dict.fromkeys(aggregated_fields, False)
    result_template[groupby + '_count'] = 0
    if remaining_groupbys:
        result_template['__context'] = {'group_by': remaining_groupbys}

    # Merge the left_side (current results as dicts) with the right_side (all
    # possible values as m2o pairs). Both lists are supposed to be using the
    # same ordering, and can be merged in one pass.
    result = []
    known_values = {}
    def append_left(left_side):
        grouped_value = left_side[groupby] and left_side[groupby][0]
        if not grouped_value in known_values:
            result.append(left_side)
            known_values[grouped_value] = left_side
        else:
            known_values[grouped_value].update({count_field: left_side[count_field]})
    def append_right(right_side):
        grouped_value = right_side[0]
        if not grouped_value in known_values:
            line = dict(result_template)
            line[groupby] = right_side
            line['__domain'] = [(groupby,'=',grouped_value)] + domain
            result.append(line)
            known_values[grouped_value] = line
    while read_group_result or all_groups:
        left_side = read_group_result[0] if read_group_result else None
        right_side = all_groups[0] if all_groups else None
        ##### NHC BEGIN
        if left_side and not isinstance(left_side[groupby], (tuple,list)):
            left_side[groupby] = all_group_tuples[left_side[groupby]]
        #### NHC END
        assert left_side is None or left_side[groupby] is False \
             or isinstance(left_side[groupby], (tuple,list)), \
            'M2O-like pair expected, got %r' % left_side[groupby]
        assert right_side is None or isinstance(right_side, (tuple,list)), \
            'M2O-like pair expected, got %r' % right_side
        if left_side is None:
            append_right(all_groups.pop(0))
        elif right_side is None:
            append_left(read_group_result.pop(0))
        elif left_side[groupby] == right_side:
            append_left(read_group_result.pop(0))
            all_groups.pop(0) # discard right_side
        elif not left_side[groupby] or not left_side[groupby][0]:
            # left side == "Undefined" entry, not present on right_side
            append_left(read_group_result.pop(0))
        else:
            append_right(all_groups.pop(0))

    if folded:
        for r in result:
            r['__fold'] = folded.get(r[groupby] and r[groupby][0], False)
    return result

openerp.models.BaseModel._read_group_fill_results = _read_group_fill_results