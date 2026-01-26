from django import forms


class GradeCalculatorForm(forms.Form):
    max_points = forms.FloatField(label="Max Points", min_value=0)

    rounding_option = forms.TypedChoiceField(
        label="Rounding Option",
        choices=[(1, "Full number"), (2, "Decimal number")],
        widget=forms.RadioSelect,
        coerce=int,  # self-note> Converts the selected value to an integer
        initial=1,
    )
