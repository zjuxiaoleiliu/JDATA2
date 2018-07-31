import numpy as np
import pandas as pd
from dateutil.parser import parse
from datetime import date, timedelta

# 求解rmse的均值和标准差
def get_ave_std(c1,c2,f1,f2):
    '''
    :param c1: 提交的常数1
    :param c2: 提交的常数2
    :param f1: 得分1
    :param f2: 得分2
    :return: 均值和标准差
    '''
    f1 = f1**2; f2 = f2**2;
    a = 2; b = 2*(c1+c2); c = c1**2+c2**2-(f1-f2);
    ave = (f1 - f2 + c2 ** 2 - c1 ** 2) / 2 / (c2 - c1)
    std = (f1 - (c1 - ave) ** 2) ** 0.5
    return ave,std

# 求解rmse的均值
def get_sub_ave_std(c1,c2,f1,f2,n1,n2):
    '''
    :param c1: 提交1的常数
    :param c2: 提交2有差异的部分的常数
    :param f1: 提交1的分数
    :param f2: 提交2的分数
    :param n1: 提交总个数
    :param n2: 提交2有差异部分的个数
    :return: 提交2有差异部分的均值
    '''
    result = ((c1+c2)-((f1**2-f2**2)*n1/n2/(c1-c2)))/2
    return result


# 抽样函数
def make_sample(n,n_sub=2,seed=None):
    import random
    if seed is not None:
        random.seed(seed)
    if type(n) is int:
        l = list(range(n))
        s = int(n / n_sub)
    else:
        l = list(n)
        s = int(len(n) / n_sub)
    random.shuffle(l)
    result = []
    for i in range(n_sub):
        if i == n_sub:
            result.append(l[i*s:])
        else:
            result.append(l[i*s: (i+1)*s])
    return result


# 统计list的value_counts
def value_counts(l):
    s = set(l)
    d = dict([(x,0) for x in s])
    for i in l:
        d[i] += 1
    result = pd.Series(d)
    result.sort_values(ascending=False,inplace=True)
    return result


# 分类模型统计分析
def analyse(data,name,label='label'):
    result = data.groupby(name)[label].agg({'count':'count',
                                              'sum':'sum'})
    result['rate'] = result['sum']/result['count']
    return result

# 分析特征的信息量
def analyse2(data,name='id',label='label', factor=10):
    grouping = pd.cut(data[name],factor)
    rate = data.groupby(grouping)[label].agg({'sum':'sum',
                                              'count':'count'})
    rate['rate'] = rate['sum']/rate['count']
    return rate

# 分组标准化
def grp_standard(data,key,names):
    for name in names:
        mean_std = data.groupby(key, as_index=False)[name].agg({'mean': 'mean',
                                                               'std': 'std'})
        data = data.merge(mean_std, on=key, how='left')
        data[name] = ((data[name]-data['mean'])/data['std']).fillna(0)
        data[name] = data[name].replace(-np.inf, 0).fillna(0)
        data.drop(['mean','std'],axis=1,inplace=True)
    return data

# 分组归一化
def grp_normalize(data,key,names,start=0):
    for name in names:
        max_min = data.groupby(key,as_index=False)[name].agg({'max':'max',
                                                'min':'min'})
        data = data.merge(max_min,on=key,how='left')
        data[name] = (data[name]-data['min'])/(data['max']-data['min'])
        data[name] = data[name].replace(-np.inf, start).fillna(start)
        data.drop(['max','min'],axis=1,inplace=True)
    return data

# 分组排序
def grp_rank(data,key,names,ascending=True):
    for name in names:
        data.sort_values([key, name], inplace=True, ascending=ascending)
        data['rank'] = range(data.shape[0])
        min_rank = data.groupby(key, as_index=False)['rank'].agg({'min_rank': 'min'})
        data = pd.merge(data, min_rank, on=key, how='left')
        data['rank'] = data['rank'] - data['min_rank']
        data[names] = data['rank']
    data.drop(['rank'],axis=1,inplace=True)
    return data

# 合并节约内存
def concat(L):
    result = None
    for l in L:
        if result is None:
            result = l
        else:
            result[l.columns.tolist()] = l
    return result

# 分组排序函数
def group_rank(data, key, values, ascending=True):
    if type(key)==list:
        data_temp = data[key + [values]].copy()
        data_temp.sort_values(key + [values], inplace=True, ascending=ascending)
        data_temp['rank'] = range(data_temp.shape[0])
        min_rank = data_temp.groupby(key,as_index=False)['rank'].agg({'min_rank':'min'})
        index = data_temp.index
        data_temp = data_temp.merge(min_rank,on=key,how='left')
        data_temp.index = index
    else:
        data_temp = data[[key,values]].copy()
        data_temp.sort_values(key + [values], inplace=True, ascending=ascending)
        data_temp['rank'] = range(data_temp.shape[0])
        data_temp['min_rank'] = data_temp[key].map(data_temp.groupby(key)['rank'].min())
    data_temp['rank'] = data_temp['rank'] - data_temp['min_rank']
    return data_temp['rank']

def nunique(x):
    return len(set(x))


# 前后时间差的函数：
def group_diff_time(data,key,value,n):
    data_temp = data[key+[value]].copy()
    shift_value = data_temp.groupby(key)[value].shift(n)
    data_temp['shift_value'] = data_temp[value] - shift_value
    return data_temp['shift_value']



# smape
def smape(y_true,y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_diff = np.abs(y_true-y_pred)
    y_sum = y_true+y_pred
    return np.mean(y_diff/y_sum)*2


# groupby 直接拼接
def groupby(data,stat,key,value,func):
    key = key if type(key)==list else [key]
    data_temp = data[key].copy()
    feat = stat.groupby(key,as_index=False)[value].agg({'feat':func})
    data_temp = data_temp.merge(feat,on=key,how='left')
    return data_temp['feat']



# 计算关系紧密程度指数
def tfidf2(df,key1,key2):
    key = key1 + key2
    tfidf2 = '_'.join(key) + '_tfidf2'
    df1 = df.groupby(key,as_index=False)[key[0]].agg({'key_count': 'size'})
    df2 = df1.groupby(key1,as_index=False)['count'].agg({'key1_count': 'sum'})
    df3 = df1.groupby(key2, as_index=False)['count'].agg({'key2_count': 'sum'})
    df1 = df1.merge(df2,on=key1,how='left').merge(df3,on=key2,how='left')
    df1[tfidf2] = df1['key_count'] / df['key2_count'] / df['key1_count']


# 相差的日期数
def diff_of_days(day1, day2):
    days = (parse(day1[:10]) - parse(day2[:10])).days
    return days

# 相差的分钟数
def diff_of_minutes(time1,time2):
    minutes = (parse(time1) - parse(time2)).total_seconds()//60
    return abs(minutes)

# 相差的小时数
def diff_of_hours(time1,time2):
    hours = (parse(time1) - parse(time2)).total_seconds()//3600
    return abs(hours)

# 日期的加减
def date_add_days(start_date, days):
    end_date = parse(start_date[:10]) + timedelta(days=days)
    end_date = end_date.strftime('%Y-%m-%d')
    return end_date

# 日期的加减
def date_add_hours(start_date, hours):
    end_date = parse(start_date) + timedelta(hours=hours)
    end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')
    return end_date

# 获取某个类型里面第n次的值
def get_last_values(data, stat, key, sort_value, value, shift, sort=None):
    key = key if type(key)==list else [key]
    if sort == 'ascending':
        stat_temp = stat.sort_values(sort_value, ascending=True)
    elif sort == 'descending':
        stat_temp = stat.sort_values(sort_value, ascending=False)
    else:
        stat_temp = stat.copy()
    stat_temp['value'] = stat_temp.groupby(key)[value].shift(shift)
    stat_temp.drop_duplicates(key,keep='last',inplace=True)
    data_temp = data[key].copy()
    data_temp = data_temp.merge(stat_temp,on=key,how='left')
    return data_temp['value']


















