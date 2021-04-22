# Create your models here.
from django.db import models
from nacl_encrypted_fields import fields


class VCBEDBVaccinatieEvent(models.Model):
    # In vcbe_db.vaccinatie_event, used for citizen step 1.
    # Filled by RIVM

    # Assuming sensitive data is encrypted. This table is read only by the 'minous' user
    bsn_external = fields.NaClCharField(max_length=64)
    bsn_internal = fields.NaClCharField(max_length=64)
    payload = fields.NaClCharField(max_length=2048)
    version_cims = models.CharField(max_length=10)
    version_vcbe = models.CharField(max_length=10)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'vaccinatie_event'


CHANNEL_CHOICES = [
    ('cims', 'cims'),
    ('ggd', 'ggd'),
]


class VCBEDBVaccinatieEventLog(models.Model):
    # Insert and Select only table

    created_date = models.DateField()
    bsn_external = fields.NaClCharField(max_length=64)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'vaccinatie_event_logging'
