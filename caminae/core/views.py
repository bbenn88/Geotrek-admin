from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_control, cache_page
from django.views.generic.detail import DetailView, BaseDetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib import messages

from djgeojson.views import GeoJSONLayerView

from caminae.authent.decorators import path_manager_required, same_structure_required
from caminae.common.views import JSONResponseMixin, json_django_dumps, HttpJSONResponse
from .models import Path
from .forms import PathForm
from .filters import PathFilter
from . import graph as graph_lib



class ElevationProfile(JSONResponseMixin, BaseDetailView):
    """Extract elevation profile from a path and return it as JSON"""

    model = Path

    def get_context_data(self, **kwargs):
        """
        Put elevation profile into response context.
        """
        p = self.get_object()
        return {'profile': p.get_elevation_profile()}


class PathLayer(GeoJSONLayerView):
    model = Path
    fields = ('name', 'valid',)
    srid = settings.MAP_SRID
    # precision = 4
    # simplify = 0.5

    @method_decorator(cache_page(60, cache="fat"))  #TODO: use settings
    @method_decorator(cache_control(max_age=3600*24))   #TODO: use settings
    def dispatch(self, *args, **kwargs):
        return super(PathLayer, self).dispatch(*args, **kwargs)


class ModuleList(ListView):
    """
    
    A generic view list web page.
    
    model = None
    filterform = None
    fields = []
    """
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ModuleList, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ModuleList, self).get_context_data(**kwargs)
        context.update(**dict(
            model=self.model,
            datatables_ajax_url=self.model.get_jsonlist_url(),
            filterform=self.filterform(None, queryset=self.get_queryset()),
            fields=self.fields,
            generic_detail_url=self.model.get_generic_detail_url(),
        ))
        return context


class ModuleJsonList(JSONResponseMixin, ModuleList):
    """
    Return path related datas (belonging to the current user) as a JSON
    that will populate a dataTable.

    TODO: provide filters, pagination, sorting etc.
          At the moment everything (except the first listing) is done client side
    """
    # aaData is the key looked up by dataTables
    data_table_name = 'aaData'

    def get_context_data(self, **kwargs):
        """
        override the most important part of JSONListView... (paginator)
        """
        queryset = kwargs.pop('object_list')
        # Filter queryset from possible serialized form
        queryset = self.filterform(self.request.GET or None, queryset=queryset)
        # Build list with fields
        map_obj_pk = []
        data_table_rows = []
        for obj in queryset:
            columns = []
            for field in self.fields:
                columns.append(getattr(obj, field + '_display', getattr(obj, field)))
            data_table_rows.append(columns)
            map_obj_pk.append(obj.pk)

        context = {
            self.data_table_name: data_table_rows,
            'map_obj_pk': map_obj_pk,
        }
        return context


class ModuleDetail(DetailView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ModuleDetail, self).dispatch(*args, **kwargs)

    def can_edit(self):
        return False

    def get_context_data(self, **kwargs):
        context = super(ModuleDetail, self).get_context_data(**kwargs)
        context['can_edit'] = self.can_edit()
        return context


class ModuleCreate(CreateView):
    def form_valid(self, form):
        messages.success(self.request, _("Created"))
        return super(ModuleCreate, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Your form contains errors"))
        return super(ModuleCreate, self).form_invalid(form)

    def get_success_url(self):
        return self.get_object().get_detail_url()

    def get_context_data(self, **kwargs):
        context = super(ModuleCreate, self).get_context_data(**kwargs)
        name = self.model._meta.verbose_name
        if hasattr(name, '_proxy____args'):
            name = name._proxy____args[0]  # untranslated
        context['object_type'] = name.lower()
        # Whole "add" phrase translatable, but not catched  by makemessages
        context['add_msg'] = _("Add a new %s" % context['object_type'])
        return context


class PathList(ModuleList):
    model = Path
    filterform = PathFilter
    fields = ['name', 'date_update', 'length', 'trail']


class PathJsonList(ModuleJsonList, PathList):
    pass


class PathDetail(ModuleDetail):
    model = Path

    def can_edit(self):
        return self.request.user.profile.is_path_manager and \
               self.get_object().same_structure(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(PathDetail, self).get_context_data(**kwargs)
        context['profile'] = self.get_object().get_elevation_profile()
        return context


class PathCreate(ModuleCreate):
    model = Path
    form_class = PathForm

    @method_decorator(path_manager_required('core:path_list'))
    def dispatch(self, *args, **kwargs):
        return super(PathCreate, self).dispatch(*args, **kwargs)


class PathUpdate(UpdateView):
    model = Path
    form_class = PathForm
    context_object_name = 'path'

    @method_decorator(path_manager_required('core:path_detail'))
    @same_structure_required('core:path_detail')
    def dispatch(self, *args, **kwargs):
        return super(PathUpdate, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _("Saved"))
        return super(PathUpdate, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("You form contains errors"))
        return super(PathUpdate, self).form_invalid(form)

    def get_success_url(self):
        return reverse('core:path_detail', kwargs={'pk': self.object.pk})


class PathDelete(DeleteView):
    model = Path
    context_object_name = 'path'
    success_url = reverse_lazy('core:path_list')

    @method_decorator(path_manager_required('core:path_detail'))
    @same_structure_required('core:path_detail')
    def dispatch(self, *args, **kwargs):
        return super(PathDelete, self).dispatch(*args, **kwargs)


@login_required
def get_graph_json(request):
    def path_modifier(path):
        return { "pk": path.pk, "length": path.length }

    graph = graph_lib.graph_of_qs_optimize(Path.objects.all(), value_modifier=path_modifier)
    json_graph = json_django_dumps(graph)

    return HttpJSONResponse(json_graph)


home = PathList.as_view()
