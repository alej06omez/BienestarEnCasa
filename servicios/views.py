from django.shortcuts import render, get_object_or_404, redirect
from .models import Servicio, multimediaServicio, servicioInsumo
from .forms import CrearNewServicio, addServicioMultimediaForm, addServicioInsumoForm
from datetime import timedelta

#<a href="{% url 'crear_servicio_view' %}" class="mi-boton">Crear Servicio</a>

# Create your views here.

def servicios_view(request):
    servicios = Servicio.objects.all()
    return render(request, 'layouts/mis_servicios.html', {'servicios': servicios})

def servicio_datalle_view(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    multimedia = multimediaServicio.objects.filter(servicio=servicio)
    insumos = servicioInsumo.objects.filter(servicio=servicio)
    return render(request, 'layouts/servicios/servicio_detalle.html', {'servicio': servicio, 'multimedia': multimedia, 'insumos': insumos})

def servicios_por_categoria_view(request, categoria):
    servicios = Servicio.objects.filter(categoria=categoria)
    return render(request, 'layouts/servicios_por_categoria.html', {'servicios': servicios, 'categoria': categoria})




#Revisar y cambiar por forms.py
def crear_servicio_view(request):

    if request.method == 'GET':
        return render(request, "layouts/servicios/crear_servicio.html", {'form' : CrearNewServicio})
    else: 
        duracion_str = request.POST.get('duracion')  # viene como string, ej: "30"
        duracion = timedelta(minutes=int(duracion_str))  # lo conviertes a timedelta
        Servicio.objects.create(nombre = request.POST.get('nombre'), 
                                categoria = request.POST.get('categoria'), 
                                descripcion = request.POST.get('descripcion'), duracion=duracion,
                                precio=request.POST.get('precio'), estado=request.POST.get('estado')) 
        return redirect('servicios')



def addServicioInsumo(request, servicio_id):
    if request.method == 'GET':
        form = addServicioInsumoForm(initial={'servicio': servicio_id})
        return render(request, "layouts/servicio/anadir_insumo.html", {'form': form})
    else:
        form = addServicioInsumoForm(request.POST)
        if form.is_valid():
            servicioInsumo.objects.create(
                nombre=form.cleaned_data['nombre'],
                servicio=form.cleaned_data['servicio']
            )
            return redirect('nombre_de_tu_url_de_exito')
        return render(request, "layouts/servicio/anadir_insumo.html", {'form': form})


def addServicioMultimedia(request):
    if request.method == 'GET':
            return render(request, "layouts/servicio/anadir_multimedia.html", {'form' : addServicioMultimedia})
    else: 
        addServicioMultimedia.objects.create(tipo=request.POST.get('tipo'), url = request.POST.get('url'), servicio_id = request.POST.get('servicio_id'))