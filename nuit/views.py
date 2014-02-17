from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Q

class SearchableListView(ListView):
    search_fields = ()

    def get_context_data(self, **kwargs):
        context = super(SearchableListView, self).get_context_data(**kwargs)
        if self.search_fields:
            context['search'] = True
            q = self.request.GET.get('q')
            if q:
                context['search_query'] = q
        return context

    def get_queryset(self):
        queryset = super(SearchableListView, self).get_queryset()
        if self.search_fields:
            q = self.request.GET.get('q')
            if q is None:
                return queryset
            queryset = self.search_queryset(queryset, q)
        return queryset

    def search_queryset(self, queryset, search_term):
        query = Q()
        for field in self.search_fields:
            lookup = 'icontains'
            if not isinstance(field, basestring):
                field, lookup = field
            query = query | Q(**{'%s__%s' % (field, lookup): search_term})
        return queryset.filter(query)
