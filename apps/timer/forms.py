from django import forms


class CountdownmForm(forms.Form):
    total_time = forms.TimeField(widget=forms.TimeInput(format="%H:%M:%S"))
