def is_required_form_field(field):
    from wtforms.validators import Required
    for validator in field.validators:
        if isinstance(validator, Required):
            return True
    return False
