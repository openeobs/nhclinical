``nh_clinical.api``
===================

.. automodule:: api
    :members:

    .. autoclass:: nh_clinical_api(orm.AbstractModel)

        .. automethod:: update(self, cr, uid, hospital_number, data, context=None)
        .. automethod:: register(self, cr, uid, hospital_number, data, context=None)
        .. automethod:: admit(self, cr, uid, hospital_number, data, context=None)
        .. automethod:: admit_update(self, cr, uid, hospital_number, data, context=None)
        .. automethod:: cancel_admit(self, cr, uid, hospital_number, context=None)
        .. automethod:: discharge(self, cr, uid, hospital_number, data, context=None)
        .. automethod:: cancel_discharge(self, cr, uid, hospital_number, context=None)
        .. automethod:: merge(self, cr, uid, hospital_number, data, context=None)
        .. automethod:: transfer(self, cr, uid, hospital_number, data, context=None)
        .. automethod:: cancel_transfer(self, cr, uid, hospital_number, context=None)
