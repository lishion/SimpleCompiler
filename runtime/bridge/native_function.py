from parser.scope import ScopeManager
from parser.symbol import FunctionSymbol
from parser.symbol_type import FunctionTypeRef, TypeRef
from runtime.data import DataObject, MetaManager

class NativeManager:

    def __init__(self):
        self._scopeManager = ScopeManager()
        self._metaManager = MetaManager()
        self._native_functions = {}


    def register(self, func_defs):
        """
        装饰器：注册原生函数及其类型信息。
        func_defs: List[Tuple[str, Tuple[str, ...], str]]
        """

        def decorator(func):
            for name, input_types, output_type in func_defs:
                self._native_functions[name] = {
                    'func': func,
                    'input_types': input_types,
                    'output_type': output_type
                }
                self._scopeManager.add_symbol(
                    FunctionSymbol(
                        name,
                        FunctionTypeRef(
                            name,
                            args=[TypeRef(x) for x in input_types],
                            return_type=TypeRef(output_type)
                        )
                    )
                )
            return func

        return decorator

    @property
    def scope_manager(self):
        return self._scopeManager

    @property
    def meta_manager(self):
        return self._metaManager

    @property
    def native_functions(self):
        return self._native_functions

NATIVE_MANAGER = NativeManager()

class NativeFunction:
    def __init__(self, meta_manager: MetaManager):
        self._metaManager = meta_manager


    @NATIVE_MANAGER.register([
        ('int_to_float', ('Int', ), 'Float'),
        ('string_to_float', ('String',),  'Float'),
    ])
    def to_float(self, obj):
        if isinstance(obj, DataObject):
            return DataObject(
                data=float(obj.data),
                meta=self._metaManager.get_or_create_meta('Float')
            )
        else:
            return float(obj)

    @NATIVE_MANAGER.register([
        ('int_to_string', ('Int',), 'String'),
        ('float_to_string', ('Float',), 'String'),
        ('bool_to_string', ('Bool',), 'String'),
    ])
    def to_string(self, obj):
        if isinstance(obj, DataObject):
            return DataObject(
                data=str(obj.data),
                meta=self._metaManager.get_or_create_meta('String')
            )
        else:
            return str(obj)

    @NATIVE_MANAGER.register([
        ('add_int', ('Int', 'Int'), 'Int'),
        ('add_float', ('Float', 'Float'), 'Float'),
        ('add_string', ('String', 'String'), 'String'),
    ])
    def add(self, l, r):
        return DataObject(
            data=l.data + r.data,
            meta=l.meta
        )

    @NATIVE_MANAGER.register([
        ('sub_int', ('Int', 'Int'), 'Int'),
        ('sub_float', ('Float', 'Float'), 'Float')
    ])
    def sub(self, l, r):
        return DataObject(
            data=l.data - r.data,
            meta=l.meta
        )

    @NATIVE_MANAGER.register([
        ('div_int', ('Int', 'Int'), 'Int'),
        ('div_float', ('Float', 'Float'), 'Float')
    ])
    def div(self, l, r):
        return DataObject(
            data=l.data / r.data,
            meta=l.meta
        )

    @NATIVE_MANAGER.register([
        ('mul_int', ('Int', 'Int'), 'Int'),
        ('mul_float', ('Float', 'Float'), 'Float')
    ])
    def mul(self, l, r):
        return DataObject(
            data=l.data * r.data,
            meta=l.meta
        )
    @NATIVE_MANAGER.register([
        ('logic_or', ('Bool', 'Bool'), 'Bool'),
    ])
    def _or(self, l, r):
        return DataObject(
            data=l.data or r.data,
            meta=l.meta
        )

    @NATIVE_MANAGER.register([
        ('logic_and', ('Bool', 'Bool'), 'Bool'),
    ])
    def _and(self, l, r):
        return DataObject(
            data=l.data and r.data,
            meta=l.meta
        )

    @NATIVE_MANAGER.register([
        ('lt_int', ('Int', 'Int'), 'Bool'),
        ('lt_float', ('Float', 'Float'), 'Bool'),
        ('lt_string', ('String', 'String'), 'Bool'),
    ])
    def lt(self, l, r):
        return DataObject(
            l.data < r.data,
            meta=self._metaManager.get_or_create_meta('Bool')
        )

    @NATIVE_MANAGER.register([
        ('lte_int', ('Int', 'Int'), 'Bool'),
        ('lte_float', ('Float', 'Float'), 'Bool'),
        ('lte_string', ('String', 'String'), 'Bool'),
    ])
    def lte(self, l, r):
        return DataObject(
            l.data <= r.data,
            meta=self._metaManager.get_or_create_meta('Bool')
        )

    @NATIVE_MANAGER.register([
        ('gt_int', ('Int', 'Int'), 'Bool'),
        ('gt_float', ('Float', 'Float'), 'Bool'),
        ('gt_string', ('String', 'String'), 'Bool'),
    ])
    def gt(self, l, r):
        return DataObject(
            l.data > r.data,
            meta=self._metaManager.get_or_create_meta('Bool')
        )

    @NATIVE_MANAGER.register([
        ('gte_int', ('Int', 'Int'), 'Bool'),
        ('gte_float', ('Float', 'Float'), 'Bool'),
        ('gte_string', ('String', 'String'), 'Bool'),
    ])
    def gte(self, l, r):
        return  DataObject(
            l.data >= r.data,
            meta=self._metaManager.get_or_create_meta('Bool')
        )

    @NATIVE_MANAGER.register([
        ('eq_int', ('Int', 'Int'), 'Bool'),
        ('eq_float', ('Float', 'Float'), 'Bool'),
        ('eq_bool', ('Bool', 'Bool'), 'Bool'),
        ('eq_string', ('String', 'String'), 'Bool'),
    ])
    def eq(self, l, r):
        return DataObject(
            l.data == r.data,
            meta=self._metaManager.get_or_create_meta('Bool')
        )

    @NATIVE_MANAGER.register([
        ('echo', ('String', ), 'Unit'),
    ])
    def echo(self, obj):
        if isinstance(obj, DataObject) and isinstance(obj.data, str):
            print(obj.data)
        elif isinstance(obj, str):
            print(obj)
        else:
            raise RuntimeError(f"can not print obj {type(obj)}")

    @NATIVE_MANAGER.register([
        ('panic', ('String', ), 'Unit')
    ])
    def panic(self, msg):
        print(msg)
        exit(1)

    @NATIVE_MANAGER.register([
        ('is_true', ('Bool',), 'Bool'),
    ])
    def is_true(self, obj):
        return obj.data is True


    # def create_data_object(self, obj, wrap_by: str):
    #     if isinstance(obj, DataObject):
    #         return DataObject(
    #             data=obj.data,
    #             meta=self._metaManager.get_or_create_meta(f'{wrap_by}_p' + obj.meta.name + "_q")
    #         )
    #     if isinstance(obj, str):
    #         return DataObject(obj, meta=self._metaManager.get_or_create_meta('String'))
    #     elif isinstance(obj, int):
    #         return DataObject(obj, meta=self._metaManager.get_or_create_meta('Int'))
    #     elif isinstance(obj, float):
    #         return DataObject(obj, meta=self._metaManager.get_or_create_meta('Float'))
    #     raise RuntimeError(f"can unknown type {type(obj)} for next_item")