import requests
import pandas as pd
from itertools import combinations
from math import radians, sin, cos, sqrt, asin
import time

# 地铁站坐标
stations = {
    "边家村": (108.9188388, 34.2428542),
    "西北工业大学": (108.9053867, 34.2424700),
    "科技路": (108.8996871, 34.2330316),
    "太白南路": (108.9127987, 34.2270507),
    "吉祥村": (108.9287192, 34.2240962),
    "小寨": (108.9422300, 34.2244603),
    "大雁塔": (108.9592490, 34.2246971),
    "北池头": (108.9724294, 34.2253066),
    "青龙寺": (108.9892709, 34.2323446),
    "雁翔路北口": (108.9844441, 34.2398929),
    "太乙路": (108.9690737, 34.2428266),
    "建筑科技大学·李家村": (108.9588813, 34.2427607),
    "西安科技大学": (108.9590442, 34.2349959),
    "文艺路": (108.9507584, 34.2427786),
    "南稍门": (108.9422300, 34.2427600),
    "体育场": (108.9421891, 34.2341032),
    "省人民医院·黄雁村": (108.9284088, 34.2428324)
}

key = "" #高德APIkey
citycode = "029"  #城市代码
pairs = list(combinations(stations.items(), 2))

results = []
for (s1, (lon1, lat1)), (s2, (lon2, lat2)) in pairs:
    origin      = f"{lon1:.6f},{lat1:.6f}"
    destination = f"{lon2:.6f},{lat2:.6f}"
    url = (
       f"https://restapi.amap.com/v5/direction/transit/integrated"
       f"?origin={origin}&destination={destination}"
       f"&city1={citycode}&city2={citycode}"
       f"&key={key}&output=json"
    )

    resp = requests.get(url, proxies={"http": None, "https": None}, timeout=10)
    data = resp.json()
    if data.get("status") != "1":
        continue

    for trans in data["route"]["transits"][:2]:
        for seg in trans.get("segments", []):
            for line in seg.get("bus", {}).get("buslines", []):
                dep_name = line["departure_stop"]["name"]
                dep_loc  = line["departure_stop"]["location"]
                arr_name = line["arrival_stop"]["name"]
                arr_loc  = line["arrival_stop"]["location"]
                via      = line.get("via_stops", [])

                # 保留上/下车坐标
                if not via:
                    results.append({
                        "起点":    s1,  "终点":    s2,
                        "线路":    line["name"],
                        "站点类型":"上车", "站点名": dep_name, "经纬度": dep_loc
                    })
                    results.append({
                        "起点":    s1,  "终点":    s2,
                        "线路":    line["name"],
                        "站点类型":"下车", "站点名": arr_name, "经纬度": arr_loc
                    })
                else:
                    # 上车点
                    results.append({
                        "起点":    s1,  "终点":    s2,
                        "线路":    line["name"],
                        "站点类型":"上车", "站点名": dep_name, "经纬度": dep_loc
                    })
                    # 每一个中间站
                    for stop in via:
                        results.append({
                            "起点":    s1,  "终点":    s2,
                            "线路":    line["name"],
                            "站点类型":"途经", "站点名": stop["name"], "经纬度": stop["location"]
                        })
                    # 下车点
                    results.append({
                        "起点":    s1,  "终点":    s2,
                        "线路":    line["name"],
                        "站点类型":"下车", "站点名": arr_name, "经纬度": arr_loc
                    })

    time.sleep(0.3)


df_full = pd.DataFrame(results).drop_duplicates()

# Haversine 距离函数
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))
    dlon = lon2 - lon1; dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * 6371 * asin(sqrt(a))

#  提取“可接驳”公交站点
radius = 0.3  # 单位 km
dock = []     # 存放 (地铁站, 线路, 站点类型, 站点名, 经度, 纬度)

# 把 “经纬度” 列拆成 lon/lat
df_full[["lon","lat"]] = df_full["经纬度"].str.split(",", expand=True).astype(float)

for metro, (mx, my) in stations.items():
    sub = df_full.copy()
    # 计算距离
    sub["dist"] = sub.apply(lambda r: haversine(mx, my, r.lon, r.lat), axis=1)
    # 过滤半径内
    near = sub[sub["dist"] <= radius]
    for _, r in near.iterrows():
        dock.append({
            "地铁站": metro,
            "线路":   r["线路"],
            "站点类型": r["站点类型"],
            "站点名": r["站点名"],
            "经度":   r["lon"],
            "纬度":   r["lat"]
        })

df_dock = pd.DataFrame(dock).drop_duplicates()

#每个地铁站 & 可接驳线路对应的站点及其经纬度
df_metro = (
    df_dock
    .groupby(['地铁站','线路'])
    .agg(
        可接驳站点列表=('站点名', lambda x: list(x)),
        可接驳经度列表=('经度',    lambda x: list(x)),
        可接驳纬度列表=('纬度',    lambda x: list(x))
    )
    .reset_index()
)
# 只保留公交线路
df_metro_bus = df_metro[~df_metro['线路'].str.contains('地铁')]

print("每个地铁站可接驳公交线路及站点及经纬度：")
print(df_metro_bus.to_string(index=False))



# 每对地铁站 & 直达公交线路对应的上/下车站点
df_direct = df_full[df_full['站点类型'].isin(['上车','下车'])].copy()
df_pair = (
    df_direct
    .groupby(['起点','终点','线路','站点类型'])['站点名']
    .agg(lambda x: x.unique().tolist())   # <-- 直接拿到 list[str]
    .reset_index()
)
df_pair_wide = (
    df_pair
    .pivot(
        index=['起点','终点','线路'],
        columns='站点类型',
        values='站点名'
    )
    .reset_index()
)
df_pair_wide.columns.name = None
df_pair_wide = df_pair_wide.rename(columns={
    '上车': '上车站点列表',
    '下车': '下车站点列表'
})


# 建立 lookup 表
lookup = (
    df_full[['线路','站点名','经纬度']]
    .drop_duplicates(subset=['线路','站点名'])
    .rename(columns={'站点名':'站点','经纬度':'坐标'})
)

# 处理“上车”部分
df_up = (
    df_pair_wide[['起点','终点','线路','上车站点列表']]
    .explode('上车站点列表')
    .rename(columns={'上车站点列表':'站点'})
    .merge(lookup, on=['线路','站点'], how='left')
)
df_up[['上车经度','上车纬度']] = (
    df_up['坐标'].str.split(',', expand=True).astype(float)
)
df_up_agg = (
    df_up
    .groupby(['起点','终点','线路'], as_index=False)
    .agg({
        '站点':     lambda s: list(s),
        '上车经度': lambda x: list(x),
        '上车纬度': lambda x: list(x),
    })
    .rename(columns={
        '站点':'上车站点列表',
        '上车经度':'上车经度列表',
        '上车纬度':'上车纬度列表',
    })
)

# 处理“下车”部分
df_down = (
    df_pair_wide[['起点','终点','线路','下车站点列表']]
    .explode('下车站点列表')
    .rename(columns={'下车站点列表':'站点'})
    .merge(lookup, on=['线路','站点'], how='left')
)
df_down[['下车经度','下车纬度']] = (
    df_down['坐标'].str.split(',', expand=True).astype(float)
)
df_down_agg = (
    df_down
    .groupby(['起点','终点','线路'], as_index=False)
    .agg({
        '站点':     lambda s: list(s),
        '下车经度': lambda x: list(x),
        '下车纬度': lambda x: list(x),
    })
    .rename(columns={
        '站点':'下车站点列表',
        '下车经度':'下车经度列表',
        '下车纬度':'下车纬度列表',
    })
)

# 合并上下车结果，得到最终表
df_with_coords = (
    df_pair_wide
    .drop(columns=['上车站点列表','下车站点列表'])
    .merge(df_up_agg,   on=['起点','终点','线路'], how='left')
    .merge(df_down_agg, on=['起点','终点','线路'], how='left')
)

df_bus_coords = df_with_coords[~df_with_coords['线路'].str.contains('地铁')]

print("\n=== 仅公交的带经纬度的上下车站点列表 ===")
print(df_bus_coords.to_string(index=False))
