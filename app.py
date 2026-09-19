import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

path_item   = r"items.csv"
path_orders = r"orders.csv"
path_users  = r"users.csv"


@st.cache_data
def load_data(path_item, path_orders, path_users):
    """Загрузка трёх CSV с кэшированием."""
    item = pd.read_csv(path_item, encoding="utf-8")
    orders = pd.read_csv(path_orders, encoding="utf-8", parse_dates=["order_date"])
    users = pd.read_csv(path_users, encoding="utf-8", parse_dates=["registration_date"])
    return item, orders, users


item, orders, users = load_data(path_item, path_orders, path_users)

st.title("Sales analysis")

# ===== Объединение =====
user_orders = pd.merge(orders, users, on="user_id", how="left")
df = pd.merge(user_orders, item, on="item_id", how="left")

colnames = df.columns.tolist()
print("==== Column names ====", colnames)
print("==== Dataframe info ====")
print(df.info())
print(f"Count of NA = {df.isna().sum().sum()}")
print(f"Counts of duplicates = {df.duplicated().sum()}")

# ===== Очистка и приведение типов =====
for col in colnames:
    # даты
    if "date" in col and not pd.api.types.is_datetime64_any_dtype(df[col]):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    # цены/числа
    if "price" in col and not pd.api.types.is_numeric_dtype(df[col]):
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Заполняем пропуски (а не «удаляем» их из копии Series)
for col in colnames:
    if df[col].dtype == "object":
        df[col] = df[col].fillna("Unknown")
    elif pd.api.types.is_numeric_dtype(df[col]):
        df[col] = df[col].fillna(0)
# ===== Конец очистки =====


# ===== 5.1 Сырые данные =====
st.subheader("Raw data")
st.dataframe(df)

with st.sidebar:
    st.header("Filters")
    category_options = ["All"] + sorted(df["category"].dropna().unique().tolist())
    selected_category = st.selectbox("Select category: ", options=category_options)

if selected_category == "All":
    filtered_df = df.copy()
else:
    filtered_df = df[df["category"] == selected_category].copy()

st.write(f"Data by category: **{selected_category}**")
st.dataframe(filtered_df)


# ===== 5.2 Ключевые показатели =====
st.subheader("Key parameters")

filtered_df["cost"] = filtered_df["quantity"] * filtered_df["price_per_unit"]

total_order_counts = filtered_df["order_id"].nunique() or len(filtered_df)
revenue            = filtered_df["cost"].sum()
unique_user        = filtered_df["user_id"].nunique()
mean_cost          = revenue / total_order_counts if total_order_counts else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total order count: ", f"{total_order_counts:,.0f}")
with col2:
    st.metric("Total income, ₽: ", f"{revenue:,.0f}")
with col3:
    st.metric("Count of unique users: ", f"{unique_user:,}")
with col4:
    st.metric("Mean income, ₽: ", f"{mean_cost:,.0f}")


# ===== 5.3 Визуализация =====
st.subheader("Visualization")

# --- Топ-10 товаров по выручке (горизонтальный barh) ---
top_10 = (
    filtered_df.groupby("item_name")["cost"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .sort_values()             # для barh: наибольшее — сверху
)

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(top_10.index.astype(str), top_10.values, color="steelblue")
ax.set_xlabel("Cost, ₽")
ax.set_ylabel("Item")
ax.set_title("Top-10 items by revenue")
ax.grid(axis="x", linestyle="--", alpha=0.5)
fig.tight_layout()
st.pyplot(fig)

top_item = top_10.idxmax()


# --- Выручка по категориям (круговая) ---
category_revenue = (
    df.assign(cost=df["quantity"] * df["price_per_unit"])
    .groupby("category", as_index=False)["cost"]
    .sum()
    .sort_values(by="cost", ascending=False)
)

revenue_total = category_revenue["cost"].sum()

# ✅ Правильно: максимум ищем по числовой колонке cost
top_row = category_revenue.iloc[0]
cat     = top_row["category"]
cat_rev = top_row["cost"]

fig2, ax2 = plt.subplots(figsize=(9, 7))
legend_labels = [
    f"{c}: {v:,.1f} ({v / revenue_total * 100:.1f}%)"
    for c, v in zip(category_revenue["category"], category_revenue["cost"])
]

wedges, texts, autotexts = ax2.pie(
    category_revenue["cost"],
    labels=None,
    autopct="%1.1f%%",
    startangle=90,
    counterclock=False,
)
ax2.set_title("Category share of total revenue")
ax2.axis("equal")
ax2.legend(
    wedges,
    legend_labels,
    title="Categories & Percentage",
    bbox_to_anchor=(1.05, 1),
    loc="upper left",
)
fig2.tight_layout()
st.pyplot(fig2)


# --- Зависимость количества заказов от дня недели ---
filtered_df["day_of_week"] = filtered_df["order_date"].dt.strftime("%a")
day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

orders_wd = (
    filtered_df.groupby("day_of_week")["order_id"]
    .count()
    .reindex(day_order, fill_value=0)      # сохраняем календарный порядок
)

top_2_wd = orders_wd.sort_values(ascending=False).index[0:2].tolist()

fig3, ax3 = plt.subplots(figsize=(9, 5))
ax3.plot(orders_wd.index, orders_wd.values, marker="o", linewidth=2, color="steelblue")
ax3.set_xlabel("Day of week")
ax3.set_ylabel("Number of orders")
ax3.set_title("Orders by day of week")
ax3.grid(True, linestyle="--", alpha=0.5)
fig3.tight_layout()
st.pyplot(fig3)


# ===== 5.4 Аналитические выводы =====
st.subheader("Conclusions")

st.markdown(f"* Основная выручка приходится на категорию **«{cat}»** — {cat_rev / revenue_total * 100:,.1f}% от общей выручки.")
st.markdown(f"* Пик заказов наблюдается в дни: **{', '.join(top_2_wd)}**.")
st.markdown(f"* Товар **«{top_item}»** является лидером продаж по выручке.")
