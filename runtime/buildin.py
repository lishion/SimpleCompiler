from runtime.data import DataObject, MetaManager


class Converter:

    def __init__(self, metaManager: MetaManager):
        self._metaManager = metaManager

    def to_float(self, obj):
        if isinstance(obj, DataObject):
            return DataObject(
                data=float(obj.data),
                meta=self._metaManager.get_or_create_meta('Float')
            )
        else:
            return float(obj)

    def to_string(self, obj):
        if isinstance(obj, DataObject):
            return DataObject(
                data=str(obj.data),
                meta=self._metaManager.get_or_create_meta('String')
            )
        else:
            return str(obj)

    def echo(self, obj):
        if isinstance(obj, DataObject) and isinstance(obj.data, str):
            print(obj.data)
        elif isinstance(obj, str):
            print(obj)
        else:
            raise RuntimeError(f"can not print obj {type(obj)}")

class Ops:

    def add(self, l, r):
        return l + r

    def sub(self, l, r):
        return l - r

    def mul(self, l, r):
        return l * r

    def div(self, l, r):
        return l / r