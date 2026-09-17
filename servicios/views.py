from django.shortcuts import render, get_object_or_404
from .models import Servicio, multimediaServicio, servicioInsumo
from .forms import CrearNewServicio, addMultimediaServicio, addServicioInsumo

# Create your views here.

def servicios_view(request):
    servicios = Servicio.objects.all()
    return render(request, 'servicios/servicios.html', {'servicios': servicios})

def servicio_datalle_view(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    multimedia = multimediaServicio.objects.filter(servicio=servicio)
    insumos = servicioInsumo.objects.filter(servicio=servicio)
    return render(request, 'servicios/servicio_detalle.html', {'servicio': servicio, 'multimedia': multimedia, 'insumos': insumos})

def servicios_por_categoria_view(request, categoria):
    servicios = Servicio.objects.filter(categoria=categoria)
    return render(request, 'servicios/servicios_por_categoria.html', {'servicios': servicios, 'categoria': categoria})


#Revisar y cambiar por forms.py
def crear_servicio_view(request):
    if request.method == 'GET':
        return render(request, "layouts/servicio/crear_servicio.html", {'form' : CrearNewServicio})
    else: 
        Servicio.objects.create(nombre = request.POST('nombre'), categoria = request.POST('categoria'), descripcion = request.POST('descripcion'), duracion=request.POST('descripcion'), precio=request.POST('precio'), estado=request.POST('estado'), servicio_id = "") #establecer que se envie el id del servicio respectivo
