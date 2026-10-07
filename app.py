"""Rosa's Pizza: find the promised delivery time with the highest net profit.

Run with: streamlit run app.py
"""
import pandas as pd
import streamlit as st

from starter import ZONES, TIME_BLOCKS, COSTS, PROMISE, delivery_times

SEED = 1  # one fixed seed for every promise, so promises are compared fairly


# ---------------------------------------------------------------------------
# Calculations (no Streamlit code here)
# ---------------------------------------------------------------------------
def cost_per_late_order(margin, churn_orders, refund):
    """Refund plus the profit lost on future orders that churn away."""
    return refund + churn_orders * margin


def evaluate_promise(zone, time_block, promise, margin, churn_orders, refund, seed=SEED):
    """Simulate one promised time and return its results."""
    times = delivery_times(zone, time_block, promise=promise, seed=seed)
    n_orders = len(times)
    n_late = int((times > promise).sum())
    late_rate = n_late / n_orders if n_orders else 0.0
    avg_time = float(times.mean()) if n_orders else float("nan")
    net_profit = n_orders * margin - n_late * cost_per_late_order(margin, churn_orders, refund)
    return {
        "promise": promise,
        "orders": n_orders,
        "late_orders": n_late,
        "late_rate": late_rate,
        "avg_time": avg_time,
        "net_profit": net_profit,
    }


@st.cache_data
def sweep_promises(zone, time_block, low, high, step, margin, churn_orders, refund, seed=SEED):
    """Evaluate every promised time from low to high."""
    rows = [
        evaluate_promise(zone, time_block, p, margin, churn_orders, refund, seed)
        for p in range(low, high + 1, step)
    ]
    return pd.DataFrame(rows)


def best_promise(results):
    """Row with the highest net profit (the shorter promise wins a tie)."""
    return results.loc[results["net_profit"].idxmax()]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
st.title("Rosa's Pizza: delivery promise")
st.write(
    "Pick a zone and time block, set the costs, and find the promised "
    "delivery time that earns the most over four weeks."
)

with st.sidebar:
    st.header("Inputs")
    zone = st.selectbox("Zone", ZONES)
    time_block = st.selectbox("Time block", TIME_BLOCKS)
    low, high = st.slider("Promised times to try (minutes)", 10, 120, (20, 70))
    step = st.number_input("Step (minutes)", min_value=1, max_value=30, value=5)
    margin = st.number_input(
        "Profit margin per order ($)", min_value=0.0, value=COSTS["margin"], step=0.5
    )
    churn_orders = st.number_input(
        "Churn orders per late order", min_value=0.0, value=COSTS["churn_orders"], step=0.1
    )
    refund = st.number_input(
        "Refund per late order ($)", min_value=0.0, value=COSTS["refund"], step=0.5
    )
    run = st.button("Calculate best promised time", type="primary")

if run:
    if low >= high:
        st.error("The low end of the range must be below the high end.")
    else:
        results = sweep_promises(
            zone, time_block, low, high, int(step), margin, churn_orders, refund
        )
        best = best_promise(results)

        st.subheader(f"Recommendation: promise {int(best['promise'])} minutes")
        col1, col2, col3 = st.columns(3)
        col1.metric("Net profit", f"${best['net_profit']:,.2f}")
        col2.metric("Late rate", f"{best['late_rate']:.1%}")
        col3.metric("Avg delivery time", f"{best['avg_time']:.1f} min")
        st.caption(
            f"Cost per late order: ${cost_per_late_order(margin, churn_orders, refund):.2f} "
            f"(refund + churn orders x margin). Today's promise is {PROMISE} minutes. "
            "Figures are simulated over four weeks."
        )

        st.subheader("Net profit by promised time")
        st.line_chart(results, x="promise", y="net_profit")
        st.dataframe(
            results.style.format(
                {"late_rate": "{:.1%}", "avg_time": "{:.1f}", "net_profit": "${:,.2f}"}
            ),
            hide_index=True,
        )
else:
    st.info("Set the inputs in the sidebar, then click **Calculate best promised time**.")
