import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
# import datetime as dt

# print(f"Streamlit version is {st.__version__}")
# print(f"Pandas version is {pd.__version__}")
# print(f"Matplotlib version is {matplotlib.__version__}")

path_item = r"items.csv"
path_orders = r"orders.csv"
path_users = r"users.csv"

@st.cache_data
def load_data(path_item, path_orders, path_users):
    """Function to read .csv"""
    item = pd.read_csv(path_item, encoding="utf-8")
    orders = pd.read_csv(
        path_orders, encoding="utf-8", parse_dates=["order_date"]
    )
    users = pd.read_csv(
        path_users, encoding="utf-8", parse_dates=["registration_date"]
    )

    return item, orders, users


item, orders, users = load_data(path_item, path_orders, path_users)
# print(item)

st.title("Sales analysis")

user_orders = pd.merge(orders, users, on='user_id', how='left')
df = pd.merge(user_orders, item, on='item_id', how='left')

# print(df.head(10))
print('==== Column names ====')
colnames = df.columns.tolist()
print(colnames)
print('==== Dataframe info ====')
print(df.info())
print(f"Count of NA = {df.isna().sum()}")
print(f"Counts of duplicates = {df.duplicated().sum()}")

# ===== Блок очистки данных, приведения данных ===== #
for col in colnames:
    if "date" in col:
        col_tp = df[col].dtype
        if col_tp != 'datetime64[us]':
            df[col] = pd.to_datetime(df[col])
    if "price" in col:
        col_tp = df[col].dtype
        if col_tp != 'float64':
            df[col] = pd.to_numeric(df[col], errors='coerce')

df_len = len(df)
for col in colnames:
    nas = df[col].isna().sum()
    prcnt = nas / df_len * 100
    print(f"Column {col} contains {nas} NAs. It is {prcnt} percent of whole data.")
    if df[col].dtype == 'int64' or df[col].dtype == 'float64' or df[col].dtype == 'datetime64[us]':
        df[col].dropna()
    if df[col].dtype == 'str':
        df[col] = df[col].fillna('Unknown')

# ===== The end of block ===== #

# 5. Создание дашборда в Streamlit:

# 5.1 Вкладка или блок «Сырые данные»
# Отобразите итоговый DataFrame с помощью st.dataframe() или st.table().
# Добавьте возможность фильтрации по дате или категории
st.subheader('Raw data')
st.dataframe(df)

with st.sidebar:
    st.header("Filters")

    selected_category = st.selectbox(
        "Select category: ",
        options=df['category'].unique()
    )

    filtered_df = df[df['category'] == selected_category]

st.write(f"Data by category: **{selected_category}**")
st.dataframe(filtered_df)

# 5.2 Вкладка или блок «Ключевые показатели»
# Рассчитайте и отобразите с помощью st.metric():
# o Общее количество заказов
# o Общую выручку
# o Количество уникальных пользователей
# o Средний чек (общая выручка / общее количество заказов)

st.subheader('Key parameters')

total_order_counts = len(filtered_df['order_id'])
filtered_df['cost'] = filtered_df['quantity'] * filtered_df['price_per_unit']
revenue = filtered_df['cost'].sum()
unique_user = len(filtered_df['user_id'].unique())
mean_cost = revenue / total_order_counts

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total order count, ₽: ", f"{total_order_counts:,.0f}")

with col2:
    st.metric("Total income, ₽: ", f"{revenue:,.0f}")

with col3:
    st.metric("Count of unique users: ", f"{unique_user}")

with col4:
    st.metric("Mean income, ₽: ", f"{mean_cost:,.0f}")

# 5.3 Вкладка или блок «Визуализация»:

#     Топ-10 товаров по выручке
#     Создайте горизонтальную столбчатую диаграмму (bar chart) с помощью matplotlib
# и отобразите её через st.pyplot()
#
# # 'item_id', 'item_name', 'category', 'supplier', 'base_price',
# 'order_id', 'user_id', 'order_date', 'quantity', 'price_per_unit',
# 'user_name', 'registration_date', 'city', 'user_segment'
#
#     Выручка по категориям товаров
#     Создайте круговую диаграмму (pie chart) или столбчатую диаграмму,
# показывающую долю каждой категории в общей выручке
#     Зависимость количества заказов от дня недели
#     Создайте линейный или столбчатый график
st.subheader('Visualization')

filtered_df['cost'] = filtered_df['quantity'] * filtered_df['price_per_unit']
top_10 = (
    filtered_df.groupby('item_name')['cost'].sum().
    sort_values(ascending=False).
    head(10).
    sort_values()
    )

top = top_10.index[-1]

# 2. Horizontal bar chart
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(top_10.index, top_10.values, color="steelblue")
ax.set_xlabel("Cost, ₽")
ax.set_ylabel("Item")
ax.set_title("Top-10 of items by cost")
ax.grid(axis="x", linestyle="--", alpha=0.5)

# 3. Visualization with Streamlit
st.pyplot(fig)


df['cost'] = df['quantity'] * df['price_per_unit']
category_revenue = (
    df.groupby("category", as_index=False)["cost"]
    .sum().sort_values(ascending=False, by="cost")
)

cat = category_revenue.loc[category_revenue['cost'].idxmax(), 'category']
cat_rev = category_revenue.loc[category_revenue['category'].idxmax(), 'cost']

# 4. Pie chart
# fig2, ax2 = plt.subplots(figsize=(8, 8))
# ax2.pie(
#     category_revenue["cost"],
#     labels=category_revenue["category"],
#     autopct="%1.1f%%",
#     startangle=90,
#     counterclock=False,
# )
# ax2.set_title("Category share of total revenue")
# ax2.axis("equal")
# plt.legend(bbox_to_anchor=(1.4, 1), loc='upper right')
# st.pyplot(fig2)
#
revenue_ = df['cost'].sum()

fig2, ax2 = plt.subplots(figsize=(8, 8))

# 1. Формируем красивые подписи для легенды: "Категория: Стоимость"
legend_labels = [
    f"{cat}: {cost:,.1f}"
    for cat, cost in zip(category_revenue["category"], category_revenue["cost"] / revenue_ * 100)
]

# 2. Строим график БЕЗ labels на самом круге
wedges, texts, autotects = ax2.pie(
    category_revenue["cost"],
    labels=None,                 # Убираем подписи с самого рисунка
    autopct="%1.1f%%",
    startangle=90,
    counterclock=False,
)

ax2.set_title("Category share of total revenue")
ax2.axis("equal")

# 3. Tie legend to wedges beyond the graph
ax2.legend(
    wedges,
    legend_labels,
    title="Categories & Persentage",
    bbox_to_anchor=(1.05, 1),    # X shift
    loc='upper left'             # 'upper left' location
)

plt.tight_layout()

st.pyplot(fig2)


# 5. Linear plot
# Get the day of the week
filtered_df['day_of_week'] = filtered_df['order_date'].dt.strftime("%a")
orders_wd = filtered_df.groupby('day_of_week')['order_id'].count().sort_values(ascending=False)

top_2_wd = orders_wd.index[0:2].tolist()

fig3, ax = plt.subplots()
ax.plot(orders_wd.index, orders_wd.values, marker="o")
st.pyplot(fig3)

# 5.4 Вкладка или блок «Аналитические выводы»:
# Используйте st.markdown() или st.write(), чтобы сформулировать выводы. Например:
# * «Основная выручка приходится на категорию X»
# * «Пик заказов наблюдается по выходным»
# * «Товар Y является лидером продаж»
st.subheader('Conclusions')

st.write(f'Основная выручка приходится на категорию "{cat}", {cat_rev/ revenue_ * 100:,.1f} %.')
st.write('Пик заказов наблюдается в дни недели: ', *top_2_wd)
st.write('Товар "', top,'" является лидером продаж.')
