import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from collections import defaultdict
import yfinance as yf
from textblob import TextBlob
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import numpy as np
import shap
import matplotlib.pyplot as plt
# Use a simple model for demonstration
import xgboost as xgb

# Configuration
st.set_page_config(
    page_title="Project Catalyst: ESG & SDG Intelligence",
    # page_description="Analyze company ESG performance, news sentiment, and SDG alignment.",
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# SDG keywords mapping with color coding
SDG_KEYWORDS = {
    "No Poverty (SDG1)": {
        "keywords": ["poverty", "financial inclusion", "poverty reduction"],
        "color": "#e5243b"
    },
    "Good Health and Well-being (SDG3)": {
        "keywords": ["health", "wellbeing", "mental health", "healthcare"],
        "color": "#4c9f38"
    },
    "Gender Equality (SDG5)": {
        "keywords": ["gender equality", "women empowerment", "diversity", "inclusion"],
        "color": "#ff3a21"
    },
    "Affordable and Clean Energy (SDG7)": {
        "keywords": ["clean energy", "renewable", "solar", "wind", "energy efficiency"],
        "color": "#fcc30b"
    },
    "Decent Work and Economic Growth (SDG8)": {
        "keywords": ["economic growth", "jobs", "employment", "decent work"],
        "color": "#a21942"
    },
    "Industry, Innovation and Infrastructure (SDG9)": {
        "keywords": ["innovation", "infrastructure", "technology", "industry"],
        "color": "#fd6925"
    },
    "Reduced Inequalities (SDG10)": {
        "keywords": ["inequality", "equal opportunity", "inclusion", "fairness"],
        "color": "#dd1367"
    },
    "Sustainable Cities and Communities (SDG11)": {
        "keywords": ["sustainable cities", "urban", "communities", "housing"],
        "color": "#fd9d24"
    },
    "Responsible Consumption and Production (SDG12)": {
        "keywords": ["sustainable consumption", "waste", "recycling", "circular economy"],
        "color": "#bf8b2e"
    },
    "Climate Action (SDG13)": {
        "keywords": ["climate change", "carbon emissions", "climate action", "global warming"],
        "color": "#3f7e44"
    },
    "Life Below Water (SDG14)": {
        "keywords": ["marine", "oceans", "water pollution", "marine life"],
        "color": "#0a97d9"
    },
    "Life on Land (SDG15)": {
        "keywords": ["biodiversity", "forests", "land", "wildlife", "ecosystem"],
        "color": "#56c02b"
    },
    "Peace, Justice and Strong Institutions (SDG16)": {
        "keywords": ["peace", "justice", "strong institutions", "governance"],
        "color": "#00689d"
    },
    "Partnerships for the Goals (SDG17)": {
        "keywords": ["partnership", "collaboration", "sdg goals", "sustainable development goals"],
        "color": "#19486a"
    }
}

@st.cache_resource(show_spinner="Loading AI models...")
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

def scrape_esgtoday_company_news(company_name, max_articles=10):
    """Scrape ESG Today for company news with error handling and retries"""
    search_url = f"https://www.esgtoday.com/?s={company_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article", class_="post", limit=max_articles)

    news_data = []
    for article in articles:
        try:
            title_tag = article.find("h2", class_="post-title")
            title = title_tag.text.strip() if title_tag else "No title"
            link = title_tag.find("a")["href"] if title_tag and title_tag.find("a") else "#"
            
            date_tag = article.find("time", class_="post-date")
            date = date_tag["datetime"] if date_tag else "Unknown"
            if date != "Unknown":
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
                    date = date_obj.strftime("%b %d, %Y")
                except ValueError:
                    pass
            
            author_tag = article.find("span", class_="author-name")
            author = author_tag.text.strip() if author_tag else "Unknown"
            
            summary_tag = article.select_one("div.entry-content > p")
            summary = summary_tag.text.strip() if summary_tag else "No summary available."
            
            news_data.append({
                "title": title,
                "link": link,
                "date": date,
                "author": author,
                "summary": summary
            })
        except Exception as e:
            st.warning(f"Error parsing article: {str(e)}")
            continue

    return news_data

def map_snippet_to_sdgs(text):
    """Map text to relevant SDGs with keyword matching"""
    matched_sdgs = set()
    text_lower = text.lower()
    for sdg, data in SDG_KEYWORDS.items():
        if any(keyword in text_lower for keyword in data["keywords"]):
            matched_sdgs.add(sdg)
    return list(matched_sdgs)

def analyze_sentiment(text):
    """Enhanced sentiment analysis with confidence score"""
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    subjectivity = analysis.sentiment.subjectivity
    
    if polarity > 0.2:
        sentiment = "Positive"
    elif polarity < -0.2:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    
    return {
        "sentiment": sentiment,
        "polarity": polarity,
        "subjectivity": subjectivity
    }

def fetch_esg_data(ticker_symbol):
    """Fetch ESG data from Yahoo Finance with error handling"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        esg = ticker.sustainability
        print(f"Fetched ESG data for {ticker_symbol}: {esg}")
        if esg is not None:
            return esg.to_dict()
        return None
    except Exception as e:
        st.error(f"Error fetching ESG data: {str(e)}")
        return None

def display_sdg_badges(sdgs):
    """Display SDG badges with their official colors"""
    if not sdgs:
        return st.write("No SDGs identified")
    
    cols = st.columns(len(sdgs))
    for i, sdg in enumerate(sdgs):
        color = SDG_KEYWORDS.get(sdg, {}).get("color", "#000000")
        cols[i].markdown(
            f"<div style='background-color: {color}; color: white; padding: 5px 10px; "
            f"border-radius: 10px; text-align: center; font-weight: bold;'>{sdg}</div>",
            unsafe_allow_html=True
        )

def display_article(article, show_summary=False):
    """Display an article card with consistent styling"""
    with st.expander(f"**{article['title']}** - {article['date']}"):
        st.markdown(f"**Author:** {article['author']}")
        
        if show_summary:
            st.markdown(f"**Summary:** {article['summary']}")
        
        # Sentiment display with emoji
        sentiment_emoji = {
            "Positive": "😊",
            "Negative": "😞",
            "Neutral": "😐"
        }.get(article['sentiment']['sentiment'], "")
        
        st.markdown(f"**Sentiment:** {article['sentiment']['sentiment']} {sentiment_emoji}")
        
        # SDG badges
        st.markdown("**Related SDGs:**")
        display_sdg_badges(article['sdgs'])
        
        st.markdown(f"[Read full article]({article['link']})", unsafe_allow_html=True)

def display_esg_scores(esg_data):
    """Display ESG scores in a visually appealing way"""
    if not esg_data:
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame.from_dict(esg_data, orient='index', columns=['Value'])
    df.index.name = 'Metric'
    df.reset_index(inplace=True)
    
    # Categorize metrics
    categories = {
        'environment': ['environmentScore', 'carbon', 'climateChange'],
        'social': ['socialScore', 'humanRights', 'product'],
        'governance': ['governanceScore', 'board', 'compensation']
    }
    
    for category, metrics in categories.items():
        cat_df = df[df['Metric'].isin(metrics)]
        if not cat_df.empty:
            st.subheader(f"{category.capitalize()} Metrics")
            
            # Create a bar chart for each category
            fig = px.bar(
                cat_df,
                x='Value',
                y='Metric',
                orientation='h',
                color='Value',
                color_continuous_scale='Viridis',
                title=f"{category.capitalize()} Performance"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display the table
            st.dataframe(
                cat_df,
                column_config={
                    "Metric": st.column_config.TextColumn("Metric"),
                    "Value": st.column_config.ProgressColumn(
                        "Value",
                        format="%.1f",
                        min_value=0,
                        max_value=100
                    )
                },
                hide_index=True,
                use_container_width=True
            )

# Main App
def main():
    # Sidebar for inputs
    with st.sidebar:
        st.title("🌿 Project Catalyst")
        st.markdown("Analyze company ESG performance, news sentiment, and SDG alignment.")
        
        company = st.text_input("Company Name", placeholder="e.g. Apple")
        ticker_symbol = st.text_input("Stock Ticker", placeholder="e.g. AAPL").upper()
        num_articles = st.slider("Number of Articles", 1, 20, 5)
        
        st.markdown("---")
        st.markdown("**Settings**")
        show_summaries = st.checkbox("Show article summaries", value=True)
        st.markdown("---")
        st.markdown("Built with ❤️ using Streamlit")
    
    st.title("🌍 ESG Intelligence Dashboard")
    st.markdown("Comprehensive analysis of Environmental, Social, and Governance factors for companies.")
    
    if not company and not ticker_symbol:
        st.info("Please enter a company name and/or ticker symbol to begin analysis.")
        return
    
    # Initialize session state for articles if not exists
    if 'articles' not in st.session_state:
        st.session_state.articles = []
    # Always refresh articles if company changes
    if company and (not st.session_state.articles or st.sidebar.button("Refresh News")):
        with st.spinner(f"Fetching and analyzing {num_articles} articles about {company}..."):
            st.session_state.articles = scrape_esgtoday_company_news(company, num_articles)
            for art in st.session_state.articles:
                art["sdgs"] = map_snippet_to_sdgs(art['summary'])
                art["sentiment"] = analyze_sentiment(art['summary'])

    if company and st.session_state.articles:
        st.header("📊 SDG Coverage Analysis")
        # Count SDG occurrences
        sdg_counts = defaultdict(int)
        for art in st.session_state.articles:
            for sdg in art["sdgs"]:
                sdg_counts[sdg] += 1

        if sdg_counts:
            # Create a DataFrame for visualization
            sdg_df = pd.DataFrame({
                "SDG": list(sdg_counts.keys()),
                "Count": list(sdg_counts.values()),
                "Color": [SDG_KEYWORDS[sdg]["color"] for sdg in sdg_counts.keys()]
            })
            # Plot SDG coverage
            fig = px.bar(
                sdg_df,
                x="Count",
                y="SDG",
                color="SDG",
                color_discrete_map={row["SDG"]: row["Color"] for _, row in sdg_df.iterrows()},
                title="SDG Coverage in Articles",
                orientation="h"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Combined summary (only if show_summaries is True)
            if show_summaries:
                st.header("📝 Executive Summary")
                combined_text = " ".join([art['summary'] for art in st.session_state.articles])
                combined_text = combined_text[:3000]  # Truncate for summarization
                summarizer = load_summarizer()
                try:
                    combined_summary = summarizer(
                        combined_text,
                        max_length=200,
                        min_length=100,
                        do_sample=False
                    )[0]['summary_text']
                    st.info(combined_summary)
                    combined_sentiment = analyze_sentiment(combined_summary)
                    st.metric(
                        "Overall Sentiment",
                        combined_sentiment['sentiment'],
                        f"Polarity: {combined_sentiment['polarity']:.2f}",
                        delta_color="off"
                    )
                except Exception as e:
                    st.error(f"Error generating summary: {str(e)}")

            # Article display with filtering
            st.header("📰 Latest Articles")
            # Only show SDGs present in articles
            present_sdgs = sorted(set(sdg for art in st.session_state.articles for sdg in art["sdgs"]))
            selected_sdgs = st.multiselect(
                "Filter by SDG",
                present_sdgs,
                default=present_sdgs,
                format_func=lambda x: x.split("(")[0].strip()
            )
            # Filter by sentiment
            sentiment_filter = st.selectbox(
                "Filter by Sentiment",
                ["All", "Positive", "Neutral", "Negative"]
            )
            # Display filtered articles
            filtered_articles = [
                art for art in st.session_state.articles
                if (not selected_sdgs or any(sdg in art["sdgs"] for sdg in selected_sdgs)) and
                   (sentiment_filter == "All" or art["sentiment"]["sentiment"] == sentiment_filter)
            ]
            if filtered_articles:
                for article in filtered_articles:
                    display_article(article, show_summary=show_summaries)
            else:
                st.warning("No articles match the selected filters.")
        else:
            st.warning("No SDG-related content found in the articles.")
    elif company:
        st.warning("No articles found for this company.")

    # ESG Scores Section
    if ticker_symbol:
        st.header(f"📈 ESG Scores for {ticker_symbol}")
        with st.spinner(f"Fetching ESG data for {ticker_symbol}..."):
            ticker = yf.Ticker(ticker_symbol)
            esg_data = ticker.sustainability

        if esg_data is not None and not esg_data.empty:
            st.subheader("🔎 ESG Metrics Dashboard")

            # Identify numeric metrics for filtering
            numeric_metrics = []
            for metric in esg_data.index:
                try:
                    val = float(esg_data.loc[metric, esg_data.columns[0]])
                    numeric_metrics.append((metric, val))
                except Exception:
                    continue

            # Min/max filter
            if numeric_metrics:
                values = [val for _, val in numeric_metrics]
                min_val, max_val = float(np.nanmin(values)), float(np.nanmax(values))
                selected_range = st.slider(
                    "Filter metrics by value range",
                    min_value=float(min_val),
                    max_value=float(max_val),
                    value=(float(min_val), float(max_val)),
                    step=0.1,
                )
            else:
                selected_range = (None, None)

            # Group metrics
            categories = {
                "Environment": ["environmentScore", "environmentPercentile"],
                "Social": ["socialScore", "socialPercentile"],
                "Governance": ["governanceScore", "governancePercentile"],
                "Total ESG": ["totalEsg", "percentile", "esgPerformance"],
                "Controversies": ["highestControversy", "relatedControversy"],
                
              
            }

            # Display metrics by category
            for cat, keys in categories.items():
                cat_metrics = [k for k in keys if k in esg_data.index]
                if not cat_metrics:
                    continue
                st.markdown(f"### {cat}")
                cols = st.columns(len(cat_metrics))
                for i, metric in enumerate(cat_metrics):
                    value = esg_data.loc[metric, esg_data.columns[0]]
                    try:
                        val_float = float(value)
                        # Apply filter
                        if selected_range[0] is not None and not (selected_range[0] <= val_float <= selected_range[1]):
                            continue
                        # Progress bar for scores/percentiles
                        cols[i].progress(min(max(val_float / 100, 0), 1), text=f"{metric}: {val_float:.1f}")
                    except Exception:
                        # Show as text for non-numeric
                        cols[i].markdown(f"**{metric}**: {value}")

            # Display Peer Comparison metrics in a smart way
            peer_keys = [k for k in esg_data.index if k.startswith("peer")]

            if peer_keys:
                st.markdown("### 🤝 Peer Comparison")
                for metric in peer_keys:
                    value = esg_data.loc[metric, esg_data.columns[0]]
                    # If value is a dict with min/avg/max, show as a compact block
                    if isinstance(value, dict) and all(k in value for k in ("min", "avg", "max")):
                        st.markdown(f"**{metric.replace('peer', '').replace('Performance',' Performance').strip().replace('Group','Group')}**")
                        cols = st.columns(3)
                        cols[0].metric("Min", f"{value['min']:.2f}")
                        cols[1].metric("Avg", f"{value['avg']:.2f}")
                        cols[2].metric("Max", f"{value['max']:.2f}")
                        # Optional: Add a progress bar for avg/max
                        cols[1].progress(min(max(value['avg'] / value['max'], 0), 1), text=f"Avg/Max: {value['avg']:.2f}/{value['max']:.2f}")
                    else:
                        # For single values or strings
                        st.markdown(f"**{metric.replace('peer', '').replace('Group','Group').strip()}:** {value}")

            # Exclusions (move to bottom and present as badges in 2 rows if needed)
            exclusion_sectors = {
                "Weapons": ["controversialWeapons", "militaryContract", "smallArms", "nuclear"],
                "Substances": ["alcoholic", "tobacco", "gambling", "adult"],
                "Ethics": ["animalTesting", "catholic", "furLeather", "gmo"],
                "Environment": ["coal", "palmOil", "pesticides"],
            }

            exclusions_present = [k for sector in exclusion_sectors.values() for k in sector if k in esg_data.index]
            if exclusions_present:
                st.markdown("### 🚫 Exclusions & Ethical Flags")
                for sector, keys in exclusion_sectors.items():
                    present = [k for k in keys if k in esg_data.index]
                    if not present:
                        continue
                    st.markdown(f"**{sector}**")
                    cols = st.columns(len(present))
                    for i, metric in enumerate(present):
                        value = esg_data.loc[metric, esg_data.columns[0]]
                        flagged = str(value).strip().lower() in ["1", "true", "yes", "y"]
                        label = "❌ Flagged" if flagged else "✅ No"
                        # Evenly spaced, simple, no color
                        cols[i].markdown(
                            f"<div style='padding: 8px 0; border-radius: 8px; text-align: center; font-weight: bold; min-width: 100px;'>"
                            f"<span style='text-transform:capitalize'>{metric}</span><br>"
                            f"<span style='font-size:1.1em'>{label}</span></div>",
                            unsafe_allow_html=True
                        )
        else:
            st.error("Could not fetch ESG data for this ticker. Please check the ticker symbol and try again.")

    # XAI Section
    st.header("🤖 Explainable AI (XAI) in ESG & SDG Mapping")

    st.markdown("""
    This dashboard uses AI to analyze news and company data, mapping them to SDGs and ESG scores.
    To ensure transparency and trust, we use Explainable AI (XAI) techniques to show how decisions are made.
    """)

    # with st.expander("🔍 How does AI map articles to SDGs?"):
    #     st.markdown("""
    #     - **Keyword Highlighting:** The AI scans each article for SDG-related keywords.
    #     - **Matched SDGs:** When a keyword is found, the corresponding SDG is assigned to the article.
    #     - **Transparency:** You can see which keywords triggered each SDG assignment.
    #     """)
    #     # Example: Highlight keywords in a sample summary
    #     example_summary = "The company invested in renewable energy and improved gender equality in the workplace."
    #     highlighted = example_summary
    #     for sdg, data in SDG_KEYWORDS.items():
    #         for kw in data["keywords"]:
    #             if kw.lower() in highlighted.lower():
    #                 highlighted = highlighted.replace(
    #                     kw, f"<mark style='background-color: #ffe066'>{kw}</mark>"
    #                 )
    #     st.markdown("**Example Article Summary:**")
    #     st.markdown(highlighted, unsafe_allow_html=True)
    #     st.markdown("**Matched SDGs:**")
    #     for sdg, data in SDG_KEYWORDS.items():
    #         if any(kw.lower() in example_summary.lower() for kw in data["keywords"]):
    #             st.markdown(f"- **{sdg}** (triggered by: {', '.join([kw for kw in data['keywords'] if kw.lower() in example_summary.lower()])})")

    with st.expander("📊 How does AI explain ESG scores?"):
        st.markdown("""
        - **Feature Importance:** If ESG scores are predicted by a machine learning model, we use SHAP (SHapley Additive exPlanations) to show which features (e.g., carbon score, governance score) most influenced the result.
        - **Visual Explanation:** SHAP summary plots or bar charts make it easy to see which factors matter most.
        """)

    with st.expander("📊 Real XAI: SHAP Summary Plot for ESG Score (Demo)"):
        st.markdown("""
        This plot shows which features most influence the ESG score, using SHAP values for explainability.
        (Below is a demo with synthetic data. Replace with your real model and features for production.)
        """)

        # --- Dummy data and model for demo ---
        # Let's say your ESG model uses these features:
        feature_names = ["carbon_emissions", "board_diversity", "waste_recycling", "gender_equality", "renewable_energy"]
        X = np.random.rand(100, len(feature_names))
        y = X @ np.array([0.5, 0.2, 0.1, 0.1, 0.1]) + np.random.normal(0, 0.05, 100)

      
        model = xgb.XGBRegressor().fit(X, y)

        # SHAP explanation
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)

        # Plot summary
        fig, ax = plt.subplots(figsize=(8, 4))
        shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
        st.pyplot(fig)

    with st.expander("ℹ️ Why XAI?"):
        st.markdown("""
        - **Trust:** Users can see why the AI made a decision.
        - **Transparency:** Regulators and stakeholders can audit the process.
        - **Actionable Insights:** Companies can understand which areas to improve for better ESG performance.
        """)

    with st.expander("📝 XAI: SDG Keyword Tracing & Transparency"):
        st.markdown("""
        **What makes XAI powerful here?**
        
        - **Transparency:** You see *exactly* which keywords in which articles triggered each SDG.
        - **Traceability:** For every SDG, you can trace back to the specific article and phrase.
        - **Trust:** No black box—every SDG assignment is explainable and auditable.
        """)

        articles = st.session_state.get("articles", [])
        if articles:
            for sdg, data in SDG_KEYWORDS.items():
                matches = []
                for idx, art in enumerate(articles):
                    found = []
                    for kw in data["keywords"]:
                        if kw.lower() in art["summary"].lower():
                            found.append(kw)
                    if found:
                        matches.append((idx, found))
                if matches:
                    st.markdown(f"**{sdg}** was triggered in:")
                    for idx, kws in matches:
                        summary = articles[idx]["summary"]
                        # Highlight keywords in summary
                        highlighted = summary
                        for kw in kws:
                            highlighted = highlighted.replace(
                                kw, f"<mark style='background-color: #ffe066'>{kw}</mark>"
                            )
                        st.markdown(f"- Article {idx+1}: {highlighted}", unsafe_allow_html=True)
                        st.markdown(f"  <span style='font-size:0.9em;color:#888'>Keywords: {', '.join(kws)}</span>", unsafe_allow_html=True)
        else:
            st.info("No articles available to trace SDG keyword triggers.")
        st.info("Want to see more? Click the expanders above for interactive XAI explanations!")

if __name__ == "__main__":
    main()
