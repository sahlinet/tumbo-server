from django import template

register = template.Library()

@register.assignment_tag(takes_context=True)
def data_for_user(context):
    datastore = context['datastore']
    return datastore.filter("user_id", str(context['user'].authprofile.internalid), read=True)
