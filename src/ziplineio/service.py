class Service:
    pass


def is_service_class(service_class):
    return isinstance(service_class, type) and issubclass(service_class, Service)
