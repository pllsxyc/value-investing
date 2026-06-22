from django.db import migrations, models


def copy_tags_forward(apps, schema_editor):
    """把旧的单个 tag 字符串迁移到新的多对多 tags 关系。"""
    DcfCalculation = apps.get_model('calculator', 'DcfCalculation')
    DcfTag = apps.get_model('calculator', 'DcfTag')
    for calc in DcfCalculation.objects.all():
        name = (calc.tag or '').strip()
        if not name:
            continue
        tag, _ = DcfTag.objects.get_or_create(user=calc.user, name=name)
        calc.tags.add(tag)


def copy_tags_backward(apps, schema_editor):
    """回滚时把第一个标签写回单个 tag 字段。"""
    DcfCalculation = apps.get_model('calculator', 'DcfCalculation')
    for calc in DcfCalculation.objects.all():
        first = calc.tags.first()
        calc.tag = first.name if first else '未分类'
        calc.save(update_fields=['tag'])


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0003_dcftag'),
    ]

    operations = [
        migrations.AddField(
            model_name='dcfcalculation',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='calculations', to='calculator.dcftag'),
        ),
        migrations.RunPython(copy_tags_forward, copy_tags_backward),
        migrations.RemoveField(
            model_name='dcfcalculation',
            name='tag',
        ),
    ]
