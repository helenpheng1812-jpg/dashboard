import pandas as pd
import streamlit as st
import plotly.express as px

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Netflix Titles Dashboard",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 Netflix Movies & TV Shows Dashboard")
st.caption("Interactive version of the EDA notebook — filter the catalog and explore it live.")


# ----------------------------------------------------------------------
# Load + clean data (same steps as the notebook, cached so it only runs once)
# ----------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("netflix_titles.csv")

    # Drop exact duplicates
    df = df.drop_duplicates()

    # Handle missing values the same way as the notebook
    df["director"] = df["director"].fillna("Unknown")
    df["cast"] = df["cast"].fillna("Unknown")
    df["country"] = df["country"].fillna("Unknown")
    df["rating"] = df["rating"].fillna(df["rating"].mode()[0])
    df = df.dropna(subset=["date_added"])

    # Type conversions
    df["date_added"] = pd.to_datetime(df["date_added"], format="mixed")
    df["release_year"] = df["release_year"].astype(int)

    # Feature engineering (from the notebook)
    df["year_added"] = df["date_added"].dt.year
    df["month_added"] = df["date_added"].dt.month_name()
    df["content_age"] = df["date_added"].dt.year - df["release_year"]

    # Netflix's country column can hold several comma-separated countries —
    # take the first one listed as the "primary" country for filtering/charts
    df["primary_country"] = df["country"].apply(lambda x: x.split(",")[0].strip())

    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "Couldn't find **netflix_titles.csv**. Place it in the same folder as app.py "
        "(same folder you'd upload to GitHub for deployment)."
    )
    st.stop()


# ----------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------
st.sidebar.header("Filters")
type_options = sorted(df["type"].dropna().unique())
selected_types = st.sidebar.multiselect("Type", type_options, default=type_options)

top_countries = df["primary_country"].value_counts().head(20).index.tolist()
selected_countries = st.sidebar.multiselect(
    "Country (top 20 shown)", top_countries, default=[]
)

rating_options = sorted(df["rating"].dropna().unique())
selected_ratings = st.sidebar.multiselect("Rating", rating_options, default=[])

min_year, max_year = int(df["release_year"].min()), int(df["release_year"].max())
year_range = st.sidebar.slider(
    "Release year range", min_year, max_year, (min_year, max_year)
)

# Apply filters
filtered = df[df["type"].isin(selected_types)]
filtered = filtered[
    (filtered["release_year"] >= year_range[0])
    & (filtered["release_year"] <= year_range[1])
]
if selected_countries:
    filtered = filtered[filtered["primary_country"].isin(selected_countries)]
if selected_ratings:
    filtered = filtered[filtered["rating"].isin(selected_ratings)]

st.sidebar.markdown(f"**{len(filtered):,}** titles match your filters")


# ----------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total titles", f"{len(filtered):,}")
col2.metric("Movies", f"{(filtered['type'] == 'Movie').sum():,}")
col3.metric("TV Shows", f"{(filtered['type'] == 'TV Show').sum():,}")
col4.metric(
    "Median release year",
    int(filtered["release_year"].median()) if len(filtered) else "—",
)

st.divider()


# ----------------------------------------------------------------------
# Charts — row 1: content type split, top countries
# ----------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Content Type Split")
    type_counts = filtered["type"].value_counts().reset_index()
    type_counts.columns = ["type", "count"]
    fig = px.pie(type_counts, names="type", values="count", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Top 10 Countries")
    country_counts = (
        filtered["primary_country"].value_counts().head(10).reset_index()
    )
    country_counts.columns = ["country", "count"]
    fig = px.bar(country_counts, x="count", y="country", orientation="h")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------------------------
# Charts — row 2: release year distribution, ratings distribution
# ----------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("Release Year Distribution")
    fig = px.histogram(filtered, x="release_year", nbins=30)
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Ratings Distribution")
    rating_counts = filtered["rating"].value_counts().reset_index()
    rating_counts.columns = ["rating", "count"]
    fig = px.bar(rating_counts, x="rating", y="count")
    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------------------------
# Charts — row 3: trend over time
# ----------------------------------------------------------------------
st.subheader("Titles Added to Netflix Over Time")
trend = filtered.groupby(["year_added", "type"]).size().reset_index(name="count")
fig = px.line(trend, x="year_added", y="count", color="type", markers=True)
st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------------------------
# Data table
# ----------------------------------------------------------------------
with st.expander("View filtered data"):
    st.dataframe(
        filtered[
            [
                "title",
                "type",
                "primary_country",
                "release_year",
                "rating",
                "duration",
                "listed_in",
            ]
        ],
        use_container_width=True,
    )
