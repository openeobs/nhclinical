from openerp.tests.common import TransactionCase


class TestGetSpellActivityByPatientId(TransactionCase):
    """
    Test that get_spell_activity_by_patient_id is returning the spell
    activity for the supplied patient ID
    """

    def setUp(self):
        super(TestGetSpellActivityByPatientId, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.spell_model = self.env['nh.clinical.spell']
        self.test_utils.admit_and_place_patient()
        self.test_utils.copy_instance_variables(self)

    def test_returns_spell_activity_when_one_spell(self):
        """
        Test that when patient only has one spell it returns the
        spell_activity_id for that
        """
        spell_activity = \
            self.spell_model.get_spell_activity_by_patient_id(self.patient.id)
        self.assertEqual(spell_activity.id, self.spell_activity.id)

    def test_returns_spell_activity_when_multiple(self):
        """
        Test that when patient has multiple spells it retuns the
        spell_activity_id for the latest spell
        """
        self.test_utils.discharge_patient()
        new_spell = self.test_utils.admit_patient()
        spell_activity = \
            self.spell_model.get_spell_activity_by_patient_id(self.patient.id)
        self.assertEqual(spell_activity.id, new_spell.activity_id.id)
