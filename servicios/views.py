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
    insumo = servicioInsumo.objects.filter(servicio_id = servicio)
    multimedia = multimediaServicio.objects.filter(servicio_id=servicio)
    return render(request, 'layouts/servicios/servicio_detalle.html', {'servicio': servicio, 'multimedias': multimedia, 'insumos': insumo})

def servicios_por_categoria_view(request, categoria):
    servicios = Servicio.objects.filter(categoria=categoria)
    return render(request, 'layouts/servicios_por_categoria.html', {'servicios': servicios, 'categoria': categoria})




#Revisar y cambiar por forms.py
def crear_servicio_view(request):

    if request.method == 'GET':
        return render(request, "layouts/servicios/crear_servicio.html", {'form' : CrearNewServicio})
    else: 
        duracion_str = request.POST.get('duracion')
        duracion = timedelta(minutes=int(duracion_str))
        Servicio.objects.create(nombre = request.POST.get('nombre'),
                                categoria = request.POST.get('categoria'),
                                descripcion = request.POST.get('descripcion'), duracion=duracion,
                                precio=request.POST.get('precio'),
                                estado=request.POST.get('estado'))
        return redirect('servicios')



def addServicioInsumo(request, servicio_id):
    if request.method == 'GET':
        form = addServicioInsumoForm(initial={'servicio': servicio_id})
        return render(request, "layouts/servicios/anadir_Insumo.html", {'form': form})
    else:
        form = addServicioInsumoForm(request.POST)
        if form.is_valid():
            servicioInsumo.objects.create(
                nombre=form.cleaned_data['nombre'],
                servicio=form.cleaned_data['servicio']
            )
            return redirect('servicios')
        


def addServicioMultimedia(request, servicio_id):
    if request.method == 'GET':
        form = addServicioMultimediaForm(initial={'servicio': servicio_id})
        return render(request, "layouts/servicios/anadir_Multimedia.html", {'form': form})
    else:
        form = addServicioMultimediaForm(request.POST)
        if form.is_valid():
                multimediaServicio.objects.create(
                    tipo=form.cleaned_data['tipo'],
                    url=form.cleaned_data['url'],
                    servicio=form.cleaned_data['servicio']
                )
        return redirect('servicios')