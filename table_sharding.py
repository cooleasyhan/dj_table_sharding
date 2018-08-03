'''
Simple Django Table Sharding
'''
from collections import Iterable, MutableMapping, MutableSequence, defaultdict
from itertools import chain

from django.db.models import Max, Model, QuerySet


class ShardingException(Exception):
    '''
       Sharding Exception
    '''


class ShardingManager:

    def __init__(self, module_classes, last_func=None):
        if len(module_classes) > 0:
            if hasattr(module_classes[0], 'objects'):
                self.objects = [m.objects for m in module_classes]
            else:
                self.objects = module_classes
        else:
            raise ShardingException('module_classes cannot be Null')

        self.last_func = last_func

    def __getattr__(self, attr):
        rst = []
        for manager in self.objects:
            obj = getattr(manager, attr)
            rst.append(obj)

        return ShardingManager(rst, last_func=attr)

    def __call__(self, *args, **kwargs):
        rst = []
        for obj in self.objects:
            rst.append(obj(*args, **kwargs))

        if len(rst) > 0:
            # if isinstance(rst[0], (int, float)):
            #     return sum(rst)
            if isinstance(rst[0], (Model, int, float)):
                return rst

        return ShardingManager(rst, last_func=self.last_func)

    def __repr__(self):
        return repr(self.objects)

    def _is_sequence(self):
        if len(self.objects) == 0:
            return False
        else:
            if isinstance(self.objects[0], (list, MutableSequence, QuerySet)):
                return True
            else:
                return False

    def _chain(self):
        if self._is_sequence():
            return chain(*self.objects)
        else:
            return chain(self.objects)

    def result(self):
        if isinstance(self._chain(), Iterable):
            return [i for i in self._chain()]
        else:
            return self._chain()

    def __iter__(self):
        return iter(self._chain())

    def count(self):
        return sum([obj.count() for obj in self.objects])

    def exists(self):
        return sum([obj.exists() for obj in self.objects]) > 0

    def x_distinct(self):
        return list(set(self.result()))

    def x_agg(self, *fields):
        tmp = defaultdict(list)
        for rec in self.result():
            for key, value in rec.items():
                tmp[key].append(value)

        '''
        defaultdict(list,
            {'pk__max': [2144170, 2021552, 2102226],
             'pk__count': [6929, 6926, 6937],
             'pk__avg': [Decimal('1028130.8183'),
              Decimal('994947.7571'),
              Decimal('1034751.4051')],
             'pk__min': [13, 5, 9],
             'pk__stddev': [681050.7840290959,
              640605.0279375393,
              668557.8899381086],
             'pk__sum': [Decimal('7123918440'),
              Decimal('6891008166'),
              Decimal('7178070497')],
             'pk__variance': [463830170426.64624,
              410374801818.8555,
              446969652198.49615]})
        '''
        rst = {}
        for key, value in tmp.items():
            f = key.split('__')[1]
            if f == 'max':
                rst[key] = max(value)
            elif f == 'count':
                rst[key] = sum(value)
            elif f == 'avg':
                rst[key] = sum(value)/len(value)
            elif f == 'min':
                rst[key] = min(value)
            elif f == 'stddev':
                rst[key] = 'todo'
            elif f == 'sum':
                rst[key] = sum(value)
            elif f == 'variance':
                rst[key] = 'todo'
        return rst
        # def x_distinct():
        #     return list(set(self.result()))

        # def x_sum():
        #     return sum(self.result())


class ShardingMixin:
    # def get_sharding_key(self):
    #     return 'pk'
    _classes = {}

    @classmethod
    def get_tables(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def get_module_classes(cls, *args, **kwargs):
        shardings = cls.get_tables(*args, **kwargs)
        rst = []
        for table_name in shardings:
            class_name = ''.join([i.capitalize()
                                  for i in table_name.split('_')])
            key = '%s:%s' % (cls.__module__, class_name)
            if key not in ShardingMixin._classes:
                Meta = cls.Meta
                Meta.abstract = False
                Meta.db_table = table_name
                ShardingMixin._classes[key] = type(
                    class_name, (cls,), {'Meta': Meta, '__module__': cls.__module__})
            rst.append(ShardingMixin._classes[key])

        return rst

    @classmethod
    def as_manager(cls, *args, **kwargs):
        module_classes = cls.get_module_classes(*args, **kwargs)
        return ShardingManager(module_classes)
