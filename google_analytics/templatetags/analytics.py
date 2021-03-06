from django import template
from django.conf import settings
from django.db import models
from django.contrib.sites.models import Site

from django.template import Context, loader


register = template.Library()
Analytics = models.get_model('googleanalytics', 'analytics')

def do_get_analytics(parser, token):
    contents = token.split_contents()
    tag_name = contents[0]
    template_name = 'google_analytics/%s_template.html' % tag_name
    if len(contents) == 2:
        # split_contents() knows not to split quoted strings.
        code = contents[1]
    elif len(contents) == 1:
        code = None

    if not code:
        current_site = Site.objects.get_current()
    else:
        if not (code[0] == code[-1] and code[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
        code = code[1:-1]
        current_site = None

    return AnalyticsNode(current_site, code, template_name)

class AnalyticsNode(template.Node):
    def __init__(self, site=None, code=None, template_name='google_analytics/analytics_template.html'):
        self.site = site
        self.code = code
        self.template_name = template_name

    def render(self, context):
        content = ''
        if self.site:
            code_set = self.site.analytics_set.all()
            if code_set:
                code = code_set[0].analytics_code
            else:
                return ''
        elif self.code:
            code = self.code
        else:
            return ''

        if code.strip() != '':

            d = {'track_page_load_time': getattr(settings,
                                                 "GOOGLE_ANALYTICS_TRACK_PAGE_LOAD_TIME",
                                                 False)
                 }

            code = code.split()
            for key, value in zip(filter(lambda x: code.index(x) % 2 == 0, code),
                                  filter(lambda x: code.index(x) % 2 == 1, code)):
                d['analytics_'+key] = value
            else:
                d['analytics_code'] = code[0]

            t = loader.get_template(self.template_name)
            c = Context(d)

            return t.render(c)
        else:
            return ''

register.tag('analytics', do_get_analytics)
register.tag('analytics_async', do_get_analytics)
