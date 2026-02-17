from django import forms
from django.utils.translation import gettext_lazy as _


class GradeCalculatorForm(forms.Form):
    max_points = forms.FloatField(label=_("Max Points"), min_value=0)

    rounding_option = forms.TypedChoiceField(
        label=_("Rounding option"),
        choices=[(1, _("Full number")), (2, _("Decimal number"))],
        widget=forms.RadioSelect,
        coerce=int,  # self-note> Converts the selected value to an integer
        initial=1,
    )
