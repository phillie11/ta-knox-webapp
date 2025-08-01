# Custom template tags to fix filtering issues
# Create this file: tenders/templatetags/tender_filters.py

from django import template

register = template.Library()

@register.filter
def get_high_score_recommendations(recommendations):
    """Get recommendations with score >= 80"""
    return recommendations.filter(suitability_score__gte=80)

@register.filter
def dict_items(dictionary):
    """Get items from a dictionary for template iteration"""
    if isinstance(dictionary, dict):
        return dictionary.items()
    return []

@register.simple_tag
def recommendation_count_by_score(recommendations, min_score):
    """Count recommendations above a certain score"""
    try:
        return recommendations.filter(suitability_score__gte=min_score).count()
    except:
        return 0

@register.filter
def is_list(value):
    """Check if the value is a list or tuple"""
    return isinstance(value, (list, tuple))

@register.filter
def is_string(value):
    """Check if the value is a string"""
    return isinstance(value, str)

@register.filter
def replace(value, arg):
    """
    Replace occurrences of arg[0] with arg[1] in value
    Usage: {{ value|replace:"old,new" }}
    """
    if not arg or ',' not in arg:
        return value

    old, new = arg.split(',', 1)
    return str(value).replace(old, new)

@register.filter
def dict_get(dictionary, key):
    """
    Get a value from a dictionary by key
    Usage: {{ dict|dict_get:"key" }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def format_key(value):
    """
    Format a dictionary key for display (replace underscores with spaces, title case)
    Usage: {{ key|format_key }}
    """
    return str(value).replace('_', ' ').title()

@register.filter
def pprint(value):
    """
    Pretty print a value (useful for debugging)
    Usage: {{ value|pprint }}
    """
    import pprint
    return pprint.pformat(value)

@register.filter
def smart_truncate(value, length=100):
    """
    Truncate text smartly at word boundaries
    Usage: {{ text|smart_truncate:150 }}
    """
    if len(str(value)) <= length:
        return value

    truncated = str(value)[:length]
    # Find the last space to avoid cutting words
    last_space = truncated.rfind(' ')
    if last_space > length * 0.8:  # Only if the space is reasonably close to the end
        truncated = truncated[:last_space]

    return truncated + '...'

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary or list
    Usage: {{ dict|get_item:"key" }}
    """
    try:
        if isinstance(dictionary, dict):
            return dictionary.get(key)
        elif isinstance(dictionary, (list, tuple)):
            return dictionary[int(key)]
        else:
            return getattr(dictionary, key, None)
    except (ValueError, IndexError, TypeError):
        return None

@register.simple_tag
def get_dict_item(dictionary, key):
    """
    Template tag version of get_item
    Usage: {% get_dict_item dict "key" %}
    """
    return get_item(dictionary, key)