from django.db import migrations, models


def copy_existing_collaborators(apps, schema_editor):
    Note = apps.get_model("notes", "Note")
    NoteCollaborator = apps.get_model("notes", "NoteCollaborator")

    for note in Note.objects.all().prefetch_related("collaborators"):
        for user in note.collaborators.all():
            NoteCollaborator.objects.get_or_create(
                note_id=note.id,
                user_id=user.id,
                defaults={"access_level": "view"},
            )


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0004_note_collaborators"),
        ("users", "0003_user_otp_code_user_otp_expires_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="NoteCollaborator",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("access_level", models.CharField(choices=[("view", "Can view"), ("edit", "Can edit")], default="view", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("note", models.ForeignKey(on_delete=models.deletion.CASCADE, to="notes.note")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, to="users.user")),
            ],
            options={
                "ordering": ["-updated_at"],
                "unique_together": {("note", "user")},
            },
        ),
        migrations.RunPython(copy_existing_collaborators, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="note",
            name="collaborators",
        ),
        migrations.AddField(
            model_name="note",
            name="collaborators",
            field=models.ManyToManyField(blank=True, related_name="shared_notes", through="notes.NoteCollaborator", to="users.user"),
        ),
    ]