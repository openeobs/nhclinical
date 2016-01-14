# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from mock import MagicMock
from openerp.tests.common import TransactionCase


class TestReadGroupFillResults(TransactionCase):

    def setUp(self):
        super(TestReadGroupFillResults, self).setUp()
        self.base_model = self.registry('test_model_a')

    def test_01_append_left_with_grouped_value_not_known_value(self):
        result, known_values = self.base_model._append_left(
            {'name': ['test']}, 'name', {}, [], 'name'
        )
        self.assertEquals(result, [{'name': ['test']}])
        self.assertEquals(known_values, {'test': {'name': ['test']}})

    def test_02_append_left_with_grouped_value_known_value(self):
        result, known_values = self.base_model._append_left(
            {'name': ['test']}, 'name',
            {'test': {'name': ['test']}}, [], 'name'
        )
        self.assertEquals(result, [])
        self.assertEquals(known_values, {'test': {'name': ['test']}})

    def test_03_append_right_with_grouped_value_not_known_value(self):
        domain = [('partner_id', '!=', 34)]
        result_template = {'name_count': 0}
        res = {
            'name_count': 0, 'name': ['name'],
            '__domain': [('name', '=', 'name'), ('partner_id', '!=', 34)]
        }
        test_result = [res]
        result, known_values = self.base_model._append_right(
            ['name'], 'name', {}, [], result_template, domain
        )
        self.assertEquals(result, test_result)
        self.assertEquals(known_values, {'name': res})

    def test_04_append_right_with_grouped_value_known_value(self):
        result, known_values = self.base_model._append_right(
            ['name'], 'name', {'name': 'test'}, [], {'name_count': 0}, [])
        self.assertEquals(result, [])
        self.assertEquals(known_values, {'name': 'test'})

    def test_05_append_all_returns_empty_list(self):
        cr, uid = self.cr, self.uid
        read_group_result = []
        all_groups = []
        all_group_tuples = None
        groupby = 'name'
        result_template = None
        domain = None
        count_field = None
        result = self.base_model._append_all(
            cr, uid, read_group_result, all_groups, all_group_tuples, groupby,
            result_template, domain, count_field
        )
        self.assertEquals(result, [])

    def test_06_append_all_when_left_side_is_not_tuple_or_list(self):
        cr, uid = self.cr, self.uid
        read_group_result = [{'name': ['value']}]
        all_groups = []
        all_group_tuples = {'value', ('name', 'value')}
        groupby = 'name'
        result_template = None
        domain = None
        count_field = 'count_key'
        self.base_model._append_left = MagicMock(
            return_value=([{'name': 'value'}], {'value': {'name': 'value'}})
        )

        result = self.base_model._append_all(
            cr, uid, read_group_result, all_groups, all_group_tuples, groupby,
            result_template, domain, count_field
        )
        self.assertEquals(result, [{'name': 'value'}])
        del self.base_model._append_left

    def test_07_append_all_when_left_side_is_None(self):
        cr, uid = self.cr, self.uid
        read_group_result = []
        all_groups = [['name']]
        all_group_tuples = {}
        groupby = 'name'
        result_template = None
        domain = None
        count_field = 'count_key'
        self.base_model._append_right = MagicMock(
            return_value=([], {'name': 'test'}))

        result = self.base_model._append_all(
            cr, uid, read_group_result, all_groups, all_group_tuples, groupby,
            result_template, domain, count_field
        )
        self.base_model._append_right.assert_called_with(
            ['name'], 'name', {}, [], None, None
        )
        self.assertEquals(result, [])
        del self.base_model._append_right

    def test_08_append_all_when_left_is_equal_to_right_side(self):
        cr, uid = self.cr, self.uid
        read_group_result = [{'name': ['test']}]
        all_groups = [['test']]
        all_group_tuples = {}
        groupby = 'name'
        result_template = None
        domain = None
        count_field = 'count_key'
        self.base_model._append_left = MagicMock(return_value=([], {}))

        result = self.base_model._append_all(
            cr, uid, read_group_result, all_groups, all_group_tuples, groupby,
            result_template, domain, count_field
        )
        self.base_model._append_left.assert_called_with(
            {'name': ['test']}, 'name', {}, [], 'count_key'
        )
        self.assertEquals(result, [])
        del self.base_model._append_left

    def test_append_all_when_left_and_right_calls_append_right_then_left(self):
        cr, uid = self.cr, self.uid
        read_group_result = [{'name': ['value']}]
        all_groups = [['name']]
        all_group_tuples = {'value', ('name', 'value')}
        groupby = 'name'
        result_template = None
        domain = None
        count_field = 'count_key'
        self.base_model._append_right = MagicMock(return_value=([], {}))

        result = self.base_model._append_all(
            cr, uid, read_group_result, all_groups, all_group_tuples, groupby,
            result_template, domain, count_field
        )
        self.base_model._append_right.assert_called_with(
            ['name'], 'name', {}, [], None, None
        )
        self.assertEquals(result, [{'name': ['value']}])
        del self.base_model._append_right

    def test_append_all_when_groupby_not_in_right_side_then_append_right(self):
        cr, uid = self.cr, self.uid
        read_group_result = [{'name': 'value'}]
        all_groups = [['name']]
        all_group_tuples = {'value': ('name', 'value')}
        groupby = 'name'
        result_template = {}
        domain = None
        count_field = 'count_key'
        self.base_model._append_right = MagicMock(return_value=([], {}))

        result = self.base_model._append_all(
            cr, uid, read_group_result, all_groups, all_group_tuples, groupby,
            result_template, domain, count_field
        )
        self.assertEquals(result, [{'name': ('name', 'value')}])
        self.base_model._append_right.assert_called_with(
            ['name'], 'name', {}, [], {}, None
        )
        del self.base_model._append_right

    def test_append_all_when_groupby_is_not_left_side_then_append_left(self):
        cr, uid = self.cr, self.uid
        read_group_result = [{'name': False}]
        all_groups = [['other']]
        all_group_tuples = {'other': ('other_1', 'other_2')}
        groupby = 'name'
        result_template = {}
        domain = None
        count_field = 'count_name'
        self.base_model._append_left = MagicMock(return_value=([], {}))
        self.base_model._append_right = MagicMock(return_value=([], {}))

        result = self.base_model._append_all(
            cr, uid, read_group_result, all_groups, all_group_tuples, groupby,
            result_template, domain, count_field
        )
        self.base_model._append_left.assert_called_with(
            {'name': False}, 'name', {}, [], 'count_name'
        )
        self.base_model._append_right.assert_called_with(
            ['other'], 'name', {}, [], {}, None
        )
        self.assertEquals(result, [])
        del self.base_model._append_left, self.base_model._append_right
