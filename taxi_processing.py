import pandas as pd
import datetime
import numpy as np
from math import radians, sin, cos, sqrt, asin
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from adjustText import adjust_text


plt.rcParams['font.sans-serif'] = ['SimSun']             
plt.rcParams['axes.unicode_minus'] = False
# —— 1. 读取并预处理 ——
path = "2021-2-7.csv" #数据提供
df = pd.read_csv(path, parse_dates=['GPS_TIME'])
df = df[df['EFF'] == 1]

# 筛选时间：07:30–09:30
df['GPS_TIME'] = pd.to_datetime(df['GPS_TIME'])
t0 = datetime.time(7, 30);
t1 = datetime.time(9, 30)
df = df[(df['GPS_TIME'].dt.time >= t0) & (df['GPS_TIME'].dt.time <= t1)]

df = df.sort_values(['LICENSEPLATENO', 'GPS_TIME'])
df['prev_stat'] = df.groupby('LICENSEPLATENO')['CAR_STAT1'].shift(1)

# 提取上客/下车点
pickup = df[(df['prev_stat'] == 4) & (df['CAR_STAT1'] == 5)].copy()
dropoff = df[(df['prev_stat'] == 5) & (df['CAR_STAT1'] == 4)].copy()

# —— 2. 地铁站点列表 ——
stations = [
    ("边家村", 108.9188388, 34.2428542),
    ("西北工业大学", 108.9053867, 34.2424700),
    ("科技路", 108.8996871, 34.2330316),
    ("太白南路", 108.9127987, 34.2270507),
    ("吉祥村", 108.9287192, 34.2240962),
    ("小寨", 108.9422300, 34.2244603),
    ("大雁塔", 108.9592490, 34.2246971),
    ("北池头", 108.9724294, 34.2253066),
    ("青龙寺", 108.9892709, 34.2323446),
    ("雁翔路北口", 108.9844441, 34.2398929),
    ("太乙路", 108.9690737, 34.2428266),
    ("建筑科技大学·李家村", 108.9588813, 34.2427607),
    ("西安科技大学", 108.9590442, 34.2349959),
    ("文艺路", 108.9507584, 34.2427786),
    ("南稍门", 108.9422300, 34.2427600),
    ("体育场", 108.9421891, 34.2341032),
    ("省人民医院·黄雁村", 108.9284088, 34.2428322),
]


# —— 3. Haversine 计算距离函数 ——
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1;
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))

# —— 4. 筛选站点周边点 & 聚类 ——
radius_km = 0.35  # 半径 350 m
pu_centers_all = []
do_centers_all = []
results = []
for name, lon_s, lat_s in stations:
    pickup['dist'] = pickup.apply(
        lambda r: haversine(r.LONGITUDE, r.LATITUDE, lon_s, lat_s), axis=1
    )
    dropoff['dist'] = dropoff.apply(
        lambda r: haversine(r.LONGITUDE, r.LATITUDE, lon_s, lat_s), axis=1
    )
    pu_near = pickup[pickup['dist'] <= radius_km].copy()
    do_near = dropoff[dropoff['dist'] <= radius_km].copy()

    # 聚类 DBSCAN
    pu_centers = None
    do_centers = None
    pu_cluster_num = 0
    do_cluster_num = 0

    # 上客点聚类
    if len(pu_near) >= 10:
        db1 = DBSCAN(eps=0.0016, min_samples=5).fit(pu_near[['LONGITUDE', 'LATITUDE']])
        pu_near.loc[:, 'cluster'] = db1.labels_
        # 统计标签 >=0 的不同簇数
        pu_cluster_num = len(set(db1.labels_) - {-1})
        pu_centers = (
            pu_near[pu_near['cluster'] != -1]
            .groupby('cluster')[['LONGITUDE', 'LATITUDE']]
            .mean().reset_index()
        )

        for _, row in pu_centers.iterrows():
            pu_centers_all.append({
                '站点': name,
                                '簇编号': int(row['cluster']),
                                '经度': row['LONGITUDE'],
                                '纬度': row['LATITUDE']})


    # 下车点聚类
    if len(do_near) >= 10:
        db2 = DBSCAN(eps=0.0016, min_samples=5).fit(do_near[['LONGITUDE', 'LATITUDE']])
        do_near.loc[:, 'cluster'] = db2.labels_
        do_cluster_num = len(set(db2.labels_) - {-1})
        do_centers = (
            do_near[do_near['cluster'] != -1]
            .groupby('cluster')[['LONGITUDE', 'LATITUDE']]
            .mean().reset_index()
        )

        for _, row in do_centers.iterrows():
            do_centers_all.append({
                '站点': name,
                                '簇编号': int(row['cluster']),
                                '经度': row['LONGITUDE'],
                                '纬度': row['LATITUDE']})

    results.append({
        '站点': name,
        '上客数': len(pu_near),
        '下车数': len(do_near),
        '上客簇数': pu_cluster_num,
        '下车簇数': do_cluster_num
    })

df_res = pd.DataFrame(results)
print(df_res.to_string(index=False))

pu_centers_df = pd.DataFrame(pu_centers_all)
do_centers_df = pd.DataFrame(do_centers_all)

print("\n上客点簇中心位置：")
print(pu_centers_df.to_string(index=False))
print("\n下车点簇中心位置：")
print(do_centers_df.to_string(index=False))

# 绘图设置
plt.rcParams['font.family']        = ['SimSun']
plt.rcParams['axes.titlesize']     = 11
plt.rcParams['axes.labelsize']     = 10
plt.rcParams['xtick.labelsize']    = 10
plt.rcParams['ytick.labelsize']    = 10
plt.rcParams['legend.fontsize']    = 9
plt.rcParams['axes.unicode_minus'] = False

coords = {
    "边家村":          (108.9188388, 34.2428542),
    "西北工业大学":    (108.9053867, 34.2424700),
    "科技路":          (108.8996871, 34.2330316),
    "太白南路":        (108.9127987, 34.2270507),
    "吉祥村":          (108.9287192, 34.2240962),
    "小寨":            (108.9422300, 34.2244603),
    "大雁塔":          (108.9592490, 34.2246971),
    "北池头":          (108.9724294, 34.2253066),
    "青龙寺":          (108.9892709, 34.2323446),
    "雁翔路北口":      (108.9844441, 34.2398929),
    "太乙路":          (108.9690737, 34.2428266),
    "建筑科技大学·李家村": (108.9588813, 34.2427607),
    "西安科技大学":    (108.9590442, 34.2349959),
    "文艺路":          (108.9507584, 34.2427786),
    "南稍门":          (108.9422300, 34.2427600),
    "体育场":          (108.9421891, 34.2341032),
    "省人民医院·黄雁村": (108.9284088, 34.2428324),
}
coords_df = pd.DataFrame([
    {'站点': name, 'Longitude': lon, 'Latitude': lat}
    for name, (lon, lat) in coords.items()
])

df_plot = pd.merge(df_res, coords_df, on='站点')
plt.figure(figsize=(10, 8))
sizes = (df_plot['上客数'] + df_plot['下车数']) * 2
df_plot['总簇数'] = df_plot['上客簇数'] + df_plot['下车簇数']
colors = df_plot['总簇数']
scatter = plt.scatter(
    df_plot['Longitude'], df_plot['Latitude'],
    s=sizes, c=colors, cmap='viridis', alpha=0.8, edgecolors='w'
)
texts = []
for _, row in df_plot.iterrows():
    t = plt.text(
        row['Longitude'], row['Latitude'], row['站点'],
        fontsize=8
    )
    texts.append(t)
adjust_text(
    texts,
    arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
    only_move={'points':'y', 'texts':'y'}
)
plt.colorbar(scatter, label='总簇数')
plt.title("西安地铁站点周边上/下车点分布")
plt.xlabel("经度")
plt.ylabel("纬度")
plt.grid(True)
plt.tight_layout()
plt.show()