from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from .models import vehicle
from .forms import VehicleForm


def create_view(request):
    context = {}
    form = VehicleForm(request.POST or None)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect("/")

    context['form'] = form
    return render(request, "create_view.html", context)


def list_view(request):
    context = {}
    context["dataset"] = vehicle.objects.all()
    return render(request, "list_view.html", context)


def update_view(request, id):
    context = {}
    obj = get_object_or_404(vehicle, id=id)

    form = VehicleForm(request.POST or None, instance=obj)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect("/")

    context["form"] = form
    return render(request, "update_view.html", context)

def delete_view(request, id):
    context = {}
    obj = get_object_or_404(vehicle, id=id)

    if request.method == "POST":
        obj.delete()
        return HttpResponseRedirect("/")

    return render(request, "delete_view.html", context)
