'''Context Processors for Nuit'''
from django.conf import settings

def nuit(request):

    context = {
        'NUIT_APPLICATIONS': getattr(settings, 'NUIT_APPLICATIONS', None),
        'NUIT_GLOBAL_TITLE': getattr(settings, 'NUIT_GLOBAL_TITLE', None),
        'NUIT_LARGE_LOGO': getattr(settings, 'NUIT_LARGE_LOGO', None),
        'NUIT_SMALL_LOGO': getattr(settings, 'NUIT_SMALL_LOGO', None),
    }

    return context
