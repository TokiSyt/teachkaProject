from django.conf import settings
from django.db import models

# Create your models here.


class GroupCreationModel(models.Model):
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    members_string = models.TextField(
        help_text='Comma-separated list of names. (f.e.: "Toki, Tina, Alice") |\n Avoid using the same name for different members',
        default="",
    )
    size = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        members = self.get_members_list()
        if not members:
            raise ValueError("You must provide at least one member.")
        self.size = len(members)
        super().save(*args, **kwargs)

    def get_members_list(self):
        return [
            member.strip()
            for member in self.members_string.replace("\n", ",").split(",")
            if member.strip()
        ]

    def sync_members(self):

        from apps.point_system.models import Member, FieldDefinition

        current_names = self.get_members_list()
        current_names_ordered = list(dict.fromkeys(current_names))
        
        existing_members = self.karma_members.all()

        for member in existing_members:
            if member.name not in current_names:
                member.delete()

        for name in current_names_ordered:
            member, created = Member.objects.get_or_create(group=self, name=name)
            
            if created:
                positive_fields = FieldDefinition.objects.filter(group=self, definition="positive")
                negative_fields = FieldDefinition.objects.filter(group=self, definition="negative")
                
                member.positive_data = {}
                for field in positive_fields:
                    member.positive_data[field.name] = 0 if field.type == "int" else ""
                    
                member.negative_data = {}
                for field in negative_fields:
                    member.negative_data[field.name] = 0 if field.type == "int" else ""
                    
                member.save()