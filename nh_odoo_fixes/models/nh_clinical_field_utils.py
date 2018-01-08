# -*- coding: utf-8 -*-
from openerp.models import AbstractModel, MAGIC_COLUMNS


class FieldUtils(AbstractModel):
    """
    Provides helpful methods for dealing with fields.
    """
    _name = 'nh.clinical.field_utils'

    @staticmethod
    def get_field_names(record):
        """
        Gets all the field names for the record excluding 'magic' fields like
        `create_date` that Odoo puts on every record.

        :return: List of 'normal' field names.
        :rtype: list
        """
        field_names = [field_name for field_name in record._columns.keys()
                       if field_name not in MAGIC_COLUMNS]
        return field_names

    @staticmethod
    def get_field_names_to_validate(record):
        """
        Get field names that do not follow the naming convention
        {field_name}_minimum or {field_name}_maximum. Those fields are used
        for validating the other fields which are returned by this method.

        :param record:
        :return: Names of fields that need to be validated.
        :rtype: list
        """
        field_names = FieldUtils.get_field_names(record)
        field_names_to_validate = [field_name for field_name in field_names
                                   if 'minimum' not in field_name
                                   and 'maximum' not in field_name]
        return field_names_to_validate
