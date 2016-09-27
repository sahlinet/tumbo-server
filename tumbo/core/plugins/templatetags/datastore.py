from django import template

register = template.Library()

@register.assignment_tag(takes_context=True)
def data_for_user(context):
    datastore = context['datastore']
    if not context['user']:
        return None
    return datastore.filter("user_id", str(context['user']['id']), read=True)
