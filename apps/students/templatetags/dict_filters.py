from django import template

import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key)
    return None

@register.filter
def safe_json(data):
    return json.dumps([{'phone': c.phone, 'label': c.label or c.get_contact_type_display()} for c in data], ensure_ascii=False)
