# Simple Django Table Sharding

ShardingMixin 为每个表自动生成module
ShardingManager 接口与models.Manager保持一致，统一操作所有分表，并对结果集提供合并等相应处理


## ShardingMixin
- get_tables
    - 返回数据表列表，子类需重写
- get_module_classes
    - 返回module类，一般不需要重写
- as_manager 
    - 返回 Sharding Manager

## ShardingManager
- result
    - 返回结果集,合并Queryset
- count
- exists
- x_distinct
    - 对结果集进行distinct 处理
- x_agg
    - 对结果集进行合并

```python
'''
Demo
'''

## models.py
from django.db import models

from dj_table_sharding.table_sharding import *

class SmsMsg(models.Model, ShardingMixin):
    id = models.AutoField(db_column='id', primary_key=True)
    msg = models.CharField(max_length=1000, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)

    @classmethod
    def get_tables(cls, *args, **kwargs):
        return ('sms_msg_01', 'sms_msg_02', 'sms_msg_03')

    class Meta:
        managed = False
        abstract = True
```

```python

In [1]: from isms.models import SmsMsg;

In [2]: SmsMsg.as_manager(1,2).filter(pk=1)
Out[2]: [<QuerySet [<SmsMsg0101: SmsMsg0101 object>]>, <QuerySet [<SmsMsg0102: SmsMsg0102 object>]>, <QuerySet [<SmsMsg0103: SmsMsg0103 object>]>]

In [6]: SmsMsg.as_manager(1,2).get(pk=1)
Out[6]:
[<SmsMsg0101: SmsMsg0101 object>,
 <SmsMsg0102: SmsMsg0102 object>,
 <SmsMsg0103: SmsMsg0103 object>]

In [7]: SmsMsg.as_manager(1,2).filter(pk=1).count()
Out[7]: 3

In [8]: SmsMsg.as_manager(1,2).filter(pk=1).exists()
Out[8]: True

In [9]: SmsMsg.as_manager(1,2).filter(pk=-1).exists()
Out[9]: False

In [10]: SmsMsg.as_manager(1,2).filter(pk=1).values_list('mobile')
Out[10]: [<QuerySet [('15012345678',)]>, <QuerySet [('15112345678',)]>, <QuerySet [('15212345678',)]>]

In [11]: from django.db.models import Avg, Count, Max, Min, StdDev, Sum, Variance

In [12]: SmsMsg.as_manager(1,2).filter(mobile='15012345678').aggregate(Max('pk'), Count('pk'), Avg('pk'), Min('pk'), StdDev('pk'), Sum('pk'), Variance('pk'))
Out[12]: [{'pk__max': 2144170, 'pk__count': 6929, 'pk__avg': Decimal('1028130.8183'), 'pk__min': 13, 'pk__stddev': 681050.7840290959, 'pk__sum': Decimal('7123918440'), 'pk__variance': 463830170426.64624}, {'pk__max': 2021552, 'pk__count': 6926, 'pk__avg': Decimal('994947.7571'), 'pk__min': 5, 'pk__stddev': 640605.0279375393, 'pk__sum': Decimal('6891008166'), 'pk__variance': 410374801818.8555}, {'pk__max': 2102226, 'pk__count': 6937, 'pk__avg': Decimal('1034751.4051'), 'pk__min': 9, 'pk__stddev': 668557.8899381086, 'pk__sum': Decimal('7178070497'), 'pk__variance': 446969652198.49615}]

In [13]: _.result()
Out[13]:
[{'pk__max': 2144170,
  'pk__count': 6929,
  'pk__avg': Decimal('1028130.8183'),
  'pk__min': 13,
  'pk__stddev': 681050.7840290959,
  'pk__sum': Decimal('7123918440'),
  'pk__variance': 463830170426.64624},
 {'pk__max': 2021552,
  'pk__count': 6926,
  'pk__avg': Decimal('994947.7571'),
  'pk__min': 5,
  'pk__stddev': 640605.0279375393,
  'pk__sum': Decimal('6891008166'),
  'pk__variance': 410374801818.8555},
 {'pk__max': 2102226,
  'pk__count': 6937,
  'pk__avg': Decimal('1034751.4051'),
  'pk__min': 9,
  'pk__stddev': 668557.8899381086,
  'pk__sum': Decimal('7178070497'),
  'pk__variance': 446969652198.49615}]

In [15]: SmsMsg.as_manager(1,2).filter(mobile='15001368927').aggregate(Max('pk'), Count('pk'), Avg('pk'), Min('pk'), StdDev('pk'), Sum('pk'), Variance('pk'))
Out[15]: [{'pk__max': 2144170, 'pk__count': 6929, 'pk__avg': Decimal('1028130.8183'), 'pk__min': 13, 'pk__stddev': 681050.7840290959, 'pk__sum': Decimal('7123918440'), 'pk__variance': 463830170426.64624}, {'pk__max': 2021552, 'pk__count': 6926, 'pk__avg': Decimal('994947.7571'), 'pk__min': 5, 'pk__stddev': 640605.0279375393, 'pk__sum': Decimal('6891008166'), 'pk__variance': 410374801818.8555}, {'pk__max': 2102226, 'pk__count': 6937, 'pk__avg': Decimal('1034751.4051'), 'pk__min': 9, 'pk__stddev': 668557.8899381086, 'pk__sum': Decimal('7178070497'), 'pk__variance': 446969652198.49615}]

In [16]: _.x_agg()
Out[16]:
{'pk__max': 2144170,
 'pk__count': 20792,
 'pk__avg': Decimal('1019276.660166666666666666667'),
 'pk__min': 5,
 'pk__stddev': 'x',
 'pk__sum': Decimal('21192997103'),
 'pk__variance': 'y'}


In [19]: SmsMsg.as_manager(1,2).filter(mobile='15001368927').values_list('mobile').distinct().x_distinct()
Out[19]: [('15001368927',)]

In [20]: SmsMsg.as_manager(1,2).filter(mobile='15001368927').values_list('mobile').distinct()
Out[20]: [<QuerySet [('15001368927',)]>, <QuerySet [('15001368927',)]>, <QuerySet [('15001368927',)]>]


```
