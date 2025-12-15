from django import forms
from django.contrib.auth.models import User
from .models import DeliveryPerson

class DeliveryPersonForm(forms.ModelForm):
    class Meta:
        model = DeliveryPerson
        fields = ['user', 'phone', 'active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # show only non-superuser regular accounts as options
        self.fields['user'].queryset = User.objects.filter(is_staff=False)
