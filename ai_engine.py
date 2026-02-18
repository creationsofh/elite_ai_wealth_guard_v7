import streamlit as st

def analyze_portfolio(df):
    st.subheader("🤖 AI Portfolio Insights")
    if df.empty:
        st.info("Add stocks to see AI insights")
        return

    values = df["Value"]
    concentration = max(values)/sum(values)

    if concentration > 0.6:
        risk = "High Risk – Consider diversifying"
    elif concentration > 0.4:
        risk = "Medium Risk – Monitor carefully"
    else:
        risk = "Low Risk – Portfolio is balanced"

    st.info(f"Portfolio Risk Level: {risk}")

    # Simple AI recommendations
    st.markdown("**Recommendations:**")
    for idx, row in df.iterrows():
        if row["P/L"] < 0:
            st.write(f"{row['Ticker']}: Consider holding or reducing position")
        else:
            st.write(f"{row['Ticker']}: Performing well, monitor trends")
