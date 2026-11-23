from django.db import migrations


CATEGORIAS_INICIALES = [
    ('Peluquería', 'Corte, peinado, cepillado y cuidado capilar a domicilio.'),
    ('Masajes no Médicos', 'Masajes de relajación y bienestar no médicos en casa.'),
    ('Manicure y pedicure', 'Cuidado estético profesional de manos y pies a domicilio.'),
    ('Terapias corporales y spa', 'Rituales de bienestar, exfoliación y spa en casa.'),
    ('Cuidado facial estético', 'Limpieza facial estética e hidratación a domicilio.'),
    ('Maquillaje y peinado', 'Maquillaje social y peinados para eventos en casa.'),
]


def crear_categorias_iniciales(apps, schema_editor):
    Categoria = apps.get_model('catalogo', 'Categoria')
    for nombre, descripcion in CATEGORIAS_INICIALES:
        Categoria.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': descripcion},
        )


def revertir_categorias_iniciales(apps, schema_editor):
    # No borramos categorías que ya puedan tener servicios asociados (on_delete=PROTECT).
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0004_alter_servicio_descripcion'),
    ]

    operations = [
        migrations.RunPython(crear_categorias_iniciales, revertir_categorias_iniciales),
    ]
