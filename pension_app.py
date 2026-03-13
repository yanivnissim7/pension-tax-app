import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- הגדרות אבטחה ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: right;'>כניסה למערכת אפקט סוכנות לביטוח 🔒</h2>", unsafe_allow_html=True)
        pwd = st.text_input("הזן סיסמה:", type="password")
        if st.button("התחבר"):
            if pwd == "Effect2026": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("סיסמה שגויה")
        return False
    return True

def fmt_num(num): return f"{float(num):,.0f}"

def calculate_income_tax(monthly_income, credit_points=2.25):
    brackets = [(7010, 0.10), (10060, 0.14), (16150, 0.20), (22440, 0.31), (46690, 0.35), (float('inf'), 0.47)]
    tax, prev_bracket = 0, 0
    marginal_rate = 0.10
    for bracket, rate in brackets:
        if monthly_income > prev_bracket:
            taxable_in_bracket = min(monthly_income, bracket) - prev_bracket
            tax += taxable_in_bracket * rate
            marginal_rate = rate
            prev_bracket = bracket
        else: break
    return max(0, tax - (credit_points * 250)), marginal_rate

def main():
    if not check_password(): return

    st.set_page_config(page_title="דוח פרישה - אפקט", layout="wide")

    # יישור לימין (RTL)
    st.markdown("""<style>
        .main, .stTabs, div[data-testid="stMetricValue"], .stMarkdown, p, h1, h2, h3, label {
            direction: rtl; text-align: right !important;
        }
        .stTable { direction: rtl; }
    </style>""", unsafe_allow_html=True)

    with st.sidebar:
        st.header("👤 פרטים")
        agent = st.text_input("סוכן מטפל", value="ישראל ישראלי")
        client = st.text_input("שם לקוח", value="")
        c_id = st.text_input("ת.ז", value="")
        st.divider()
        st.header("📋 נתוני פרישה")
        retirement_date = st.date_input("תאריך פרישה", value=datetime(2025, 12, 31))
        expected_pension = st.number_input("קצבת ברוטו חודשית", value=18400)
        credit_points = st.number_input("נקודות זיכוי", value=2.25)
        seniority = st.number_input("שנות ותק", value=33.4)
        st.divider()
        st.header("💰 מענקים")
        total_grant_bruto = st.number_input("סך מענק ברוטו", value=968000)
        salary_for_exempt = st.number_input("שכר קובע לפטור", value=13750)
        past_exempt_grants = st.number_input("פטורים בעבר", value=0)

    st.markdown(f"""<div style="text-align: right; background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-right: 5px solid #007bff;">
        <h1 style="margin:0;">דוח תכנון פרישה אסטרטגי - אפקט סוכנות לביטוח בע"מ</h1>
        <p><b>עבור:</b> {client} | <b>ת.ז:</b> {c_id} | <b>סוכן:</b> {agent}</p>
    </div>""", unsafe_allow_html=True)

    # חישובים
    actual_exempt_now = min(total_grant_bruto, seniority * min(salary_for_exempt, 13750))
    taxable_grant = total_grant_bruto - actual_exempt_now
    reduction = ((actual_exempt_now + past_exempt_grants) * 1.35) * (32/seniority if seniority > 32 else 1)
    max_mon_exemp = max(0, 976005 - reduction) / 180

    st.subheader("1. אופטימיזציה")
    pct = st.select_slider("אחוז מהפטור לקצבה:", options=range(0, 101, 10), value=0)
    sel_exemp = max_mon_exemp * (pct / 100)

    tab1, tab2, tab3 = st.tabs(["📜 קיבוע", "🔄 פריסה", "📊 כדאיות"])

    with tab1:
        t_no, _ = calculate_income_tax(expected_pension, credit_points)
        t_yes, _ = calculate_income_tax(max(0, expected_pension - sel_exemp), credit_points)
        c1, c2, c3 = st.columns(3)
        c1.metric("קצבה נטו", f"₪{fmt_num(expected_pension - t_yes)}", f"+₪{fmt_num(t_no - t_yes)}")
        c2.metric("מס חודשי", f"₪{fmt_num(t_yes)}")
        c3.metric("הון פטור נותר", f"₪{fmt_num((max_mon_exemp*180) * (1-pct/100))}")

    with tab2:
        is_after_oct = retirement_date.month >= 10
        start_yr = st.selectbox("שנת תחילת פריסה:", [retirement_date.year, retirement_date.year + 1], index=1 if is_after_oct else 0)
        max_y = 6 if (is_after_oct or start_yr == retirement_date.year) else 5
        num_y = st.slider("שנות פריסה:", 1, max_y, max_y)
        
        ann_grant = taxable_grant / num_y
        total_tax_spread = 0
        rows = []
        for i in range(num_y):
            yr = start_yr + i
            p_m = 12 if (yr != retirement_date.year) else (12 - retirement_date.month)
            t_p, _ = calculate_income_tax(max(0, expected_pension - sel_exemp), credit_points)
            t_all, m_rate = calculate_income_tax(max(0, expected_pension + (ann_grant/12) - sel_exemp), credit_points)
            tax_on_g = (t_all - t_p) * 12
            total_tax_spread += tax_on_g
            rows.append({"שנה": yr, "ברוטו שנתי": (expected_pension * p_m) + ann_grant, "מס שנתי": t_all * 12, "נטו שנתי": ((expected_pension * p_m) + ann_grant) - (t_all * 12), "מדרגה": f"{m_rate*100:.0f}%"})
        
        st.table(pd.DataFrame(rows))
        
        # תיקון החישוב שגרם למינוס:
        tax_no_spread = taxable_grant * 0.47
        saving = tax_no_spread - total_tax_spread
        
        col_a, col_b, col_c = st.columns(3)
        col_a.error(f"מס ללא פריסה: ₪{fmt_num(tax_no_spread)}")
        col_b.warning(f"מס בפריסה: ₪{fmt_num(total_tax_spread)}")
        col_c.success(f"חיסכון נקי: ₪{fmt_num(saving)}")

    with tab3:
        tax_save_15 = (t_no - calculate_income_tax(max(0, expected_pension - max_mon_exemp), credit_points)[0]) * 180
        fig = go.Figure(data=[
            go.Bar(name='הון פטור', x=['השוואה'], y=[max_mon_exemp*180], marker_color='#2ecc71'),
            go.Bar(name='חיסכון במס (15 שנה)', x=['השוואה'], y=[tax_save_15], marker_color='#3498db')
        ])
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
