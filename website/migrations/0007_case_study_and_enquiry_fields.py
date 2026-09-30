from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0006_contactmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="headline",
            field=models.CharField(blank=True, help_text="Case study headline. Falls back to the project name.", max_length=200),
        ),
        migrations.AddField(
            model_name="project",
            name="metrics",
            field=models.TextField(blank=True, help_text='One result per line, as "3.1×|Case intake per month".'),
        ),
        migrations.AddField(
            model_name="project",
            name="scope",
            field=models.CharField(blank=True, help_text="e.g. 'Platform, brand, training'.", max_length=120),
        ),
        migrations.AddField(
            model_name="project",
            name="stack",
            field=models.CharField(blank=True, help_text="e.g. 'Django, Postgres'.", max_length=120),
        ),
        migrations.AddField(
            model_name="project",
            name="summary",
            field=models.TextField(blank=True, help_text="Standfirst shown under the case study headline."),
        ),
        migrations.AddField(
            model_name="project",
            name="year",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="service",
            name="addon_factor",
            field=models.FloatField(default=1.0, help_text="How strongly quote add-ons move this service's estimate."),
        ),
        migrations.AddField(
            model_name="service",
            name="deliverable",
            field=models.CharField(blank=True, help_text="What the client ends up with.", max_length=120),
        ),
        migrations.AddField(
            model_name="service",
            name="highlights",
            field=models.TextField(blank=True, help_text="One highlight per line."),
        ),
        migrations.AddField(
            model_name="service",
            name="is_retainer",
            field=models.BooleanField(default=False, help_text="Priced monthly rather than per project."),
        ),
        migrations.AddField(
            model_name="service",
            name="price_from",
            field=models.PositiveIntegerField(default=0, help_text="Indicative starting price in thousands of KES. 0 hides pricing."),
        ),
        migrations.AddField(
            model_name="service",
            name="short_name",
            field=models.CharField(blank=True, help_text="Used in running copy, e.g. 'AI & automation'.", max_length=60),
        ),
        migrations.AddField(
            model_name="service",
            name="summary",
            field=models.TextField(blank=True, help_text="Plain-text pitch shown when the service is opened on the services page."),
        ),
        migrations.AddField(
            model_name="service",
            name="timeline",
            field=models.CharField(blank=True, help_text="e.g. '4–8 weeks'.", max_length=60),
        ),
        migrations.CreateModel(
            name="Enquiry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, max_length=120)),
                ("business", models.CharField(blank=True, max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("message", models.TextField()),
                ("scope_kind", models.CharField(blank=True, max_length=120)),
                ("scope_size", models.CharField(blank=True, max_length=120)),
                ("addons", models.CharField(blank=True, max_length=200)),
                ("estimate", models.CharField(blank=True, max_length=60)),
                ("preferred_slot", models.CharField(blank=True, max_length=60)),
                ("source", models.CharField(choices=[("quote", "Quote flow"), ("service", "Service page")], default="quote", max_length=20)),
                ("handled", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("service", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="enquiries", to="website.service")),
            ],
            options={
                "verbose_name_plural": "Enquiries",
                "ordering": ["-created_at"],
            },
        ),
    ]
