from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_healthrecord_age_healthrecord_confidence_score_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='healthrecord',
            old_name='confidence_score',
            new_name='confidence',
        ),
        migrations.RemoveField(
            model_name='healthrecord',
            name='patient',
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health_records', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='gender',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='age',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='bp_systolic',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='bp_diastolic',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='sugar_level',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='cholesterol',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='heart_rate',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='bmi',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='symptom_fever',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='symptom_cough',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='symptom_fatigue',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='symptom_headache',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='symptom_chest_pain',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='symptom_breathlessness',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='symptom_sweating',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='symptom_nausea',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='predicted_disease',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='healthrecord',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterModelTable(
            name='healthrecord',
            table='health_record',
        ),
        migrations.AlterModelOptions(
            name='healthrecord',
            options={'ordering': ['-created_at']},
        ),
    ]
