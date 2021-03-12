# AN EXAMPLE OF LARGE FORM HANDLING INSIDE VIEW LAYER OF A DJANGO
# APP.

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
import json
import datetime

from ads.forms import ZoneForm
from ads.models import Zone
from ads.models import Promotion


def user_can_access_zone(fn):
    def wrapper(request, **kwargs):
        user_profile = request.user
        zid = kwargs.get('zid')
        filter_kwargs = {"pk": zid}
        if not request.user.is_superuser:
            filter_kwargs.update({"owner": user_profile})
        zone = None
        try:
            zone = Zone.objects.get(**filter_kwargs)
        except Zone.DoesNotExist:
            pass
        kwargs['zone'] = zone
        return fn(request, **kwargs)
    return wrapper


@login_required
@user_can_access_zone
def zone_form(request, ztype=None, zid=None, zone=None):
    if ztype not in ('banner', 'mobile', 'video'):
        raise Http404
    if zid:
        zone = get_object_or_404(Zone, pk=zid)
    else:
        zone = Zone()
    if request.method == "POST":
        form = ZoneForm(
            request.POST, user=request.user, ztype=ztype, instance=zone)
        if form.is_valid():
            zone.disabled = False
            zone.type = settings.AD_TYPES_LIST.index(ztype.capitalize())
            zone = form.save(commit=False)
            if not zid:
                zone.owner = request.user
            params = {}
            if ztype == "banner":
                params.update({"width": form.cleaned_data['dimensions'][0],
                               "height": form.cleaned_data['dimensions'][1]})
            elif ztype == "mobile":
                params.update({"width": form.cleaned_data['dimensions'][0],
                               "height": form.cleaned_data['dimensions'][1]})
            elif ztype == "video":
                params.update({})
            if form.cleaned_data["api"]:
                api_json = json.loads(form.cleaned_data["api"])
                params.update({"api": True})
                params.update(api_json)
            if form.cleaned_data["filter_list"]:
                params.update(
                    {"filter_list": [ii.id for ii in form.cleaned_data["filter_list"]]})
            if form.cleaned_data["block_list"]:
                params.update({"block_list": [ii.id for ii in form.cleaned_data["block_list"]]})
            zone.json = json.dumps(params)
            zone.save()
            if form.cleaned_data['backup']:
                promotion_params = {"backup": True}
                if ztype == "banner":
                    promotion_params.update(
                        {"function": "tag",
                         "html": form.cleaned_data["backup"]})
                elif ztype == "video":
                    promotion_params.update(
                        {"function": "vast_wrapper",
                         "ad_wrapper_url": form.cleaned_data["backup"]})
                promotion_json = json.dumps(promotion_params)
                if "backup_promotion_id" in params:
                    promotion = Promotion.objects.get(
                        id=params["backup_promotion_id"])
                else:
                    start = datetime.datetime.now().strftime('%Y-%m-%d')
                    end = (
                        datetime.datetime.now() + datetime.timedelta(5 * 365)
                    ).strftime('%Y-%m-%d')
                    promotion = Promotion.objects.create(
                        name=zone.name + " Backup",
                        type=zone.type,
                        start=start, end=end,
                        json=promotion_json,
                        owner=zone.owner)

                promotion.json = promotion_json
                promotion.save()
                zone_params = json.loads(zone.json)
                zone_params.update(
                    {"backup_promotion_id": promotion.id})
                zone.json = json.dumps(zone_params)
                zone.save()
            messages.success(request, "Zone successfully saved.")
            return HttpResponseRedirect(reverse('zones_list'))
        else:
            print form.errors
    else:
        form = ZoneForm(user=request.user, ztype=ztype, instance=zone)
    return render_to_response(
        'form.html', RequestContext(
            request, {
                'model_form': form,
                'model_form_name': '%s Zone' % (ztype.capitalize()),
                'model_form_icon': model_icon_dict[ztype]}))
