from django import template

register = template.Library()

@register.assignment_tag(takes_context=True)
def data_for_user(context):
    datastore = context['datastore']
    for data in datastore.all():
        print data.data['testid']
        try:
            print data.data['user_id']
        except:
            pass
    print "ID: "+str(context['user'].authprofile.internalid)
    return datastore.filter("user_id", str(context['user'].authprofile.internalid), read=True)
