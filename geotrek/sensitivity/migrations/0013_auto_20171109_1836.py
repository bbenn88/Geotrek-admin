# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sensitivity', '0012_auto_20171108_1715'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='species',
            table='s_b_espece_ou_suite_zone_regl',
        ),
    ]
