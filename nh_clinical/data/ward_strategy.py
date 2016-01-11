# coding=utf-8


class WardStrategy(object):

    def __init__(self, patients, risk_distribution, partial_news_per_patient):
        # list of Patient objects
        self.patients = patients
        # {'high': 0, 'medium': 0, 'low': 0, 'none': 0}
        self.risk_distribution = risk_distribution
        # int
        self.partial_news_per_patient = partial_news_per_patient


class Patient(object):

    def __init__(self, placement_id, patient_id, spell_activity_id,
                 bell_location_id, date_terminated):
        self.placement_id = placement_id
        self.patient_id = patient_id
        self.spell_activity_id = spell_activity_id
        self.bed_location_id = bell_location_id
        self.date_terminated = date_terminated

