from django import template

register = template.Library()


@register.filter
def custom_enumerate(value):
    """Возвращает список кортежей (индекс, элемент)."""
    return list(enumerate(value))


@register.filter
def class_name(value):
    """Возвращает имя класса объекта."""
    return value.__class__.__name__


@register.filter
def get_attribute(obj, attr_name):
    """Возвращает значение атрибута объекта по его имени."""
    return getattr(obj, attr_name, None)
