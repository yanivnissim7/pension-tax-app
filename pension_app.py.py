import streamlit as st
import pandas as pd
from datetime import datetime

# פונקציית עזר לחישוב מס הכנסה (לפי מדרגות 2026)
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

def fmt_num(num): return f"₪{float(num):,.0f}"

st.set_page_config(page_title="מחשבון פריסת מענקים - אפקט", layout="wide")

# עיצוב RTL
st.markdown("""<style> .main, .stMarkdown, p, h1, h2, h3, label { direction: rtl; text-align: right !important; } </style>""", unsafe_allow_html=True)

st.title("סימולטור פריסת מענקי פרישה 🔄")

# קלט נתונים
with st.sidebar:
    st.header("נתוני בסיס")
    ret_date = st.date_input("תאריך פרישה", value=datetime(2025, 12, 31))
    pension = st.number_input("קצבה חודשית ברוטו", value=18400)
    taxable_grant = st.number_input("חלק המענק החייב במס", value=500000)
    credit_pts = st.number_input("נקודות זיכוי", value=2.25)

# לוגיקת פריסה (חוק ה-1 באוקטובר)
is_after_oct = ret_date.month >= 10
start_year = st.selectbox("שנת תחילת פריסה:", [ret_date.year, ret_date.year + 1], index=1 if is_after_oct else 0)

max_years = 6
if start_year > ret_date.year and not is_after_oct:
    max_years = 5
    st.warning("שים לב: דחיית פריסה למי שפרש לפני 1.10 מגבילה ל-5 שנים.")

num_years = st.slider("שנות פריסה:", 1, max_years, max_years)

# חישוב הפריסה
ann_grant = taxable_grant / num_years
total_tax_spread = 0
rows = []

for i in range(num_years):
    yr = start_year + i
    # חישוב חודשי עבודה/פנסיה בשנה הראשונה
    months_in_year = 12 if (yr != ret_date.year) else (12 - ret_date.month)
    
    # חישוב מס
    tax_p_only, _ = calculate_income_tax(pension, credit_pts)
    tax_total, m_rate = calculate_income_tax(pension + (ann_grant/12), credit_pts)
    
    tax_on_grant = (tax_total - tax_p_only) * 12
    total_tax_spread += tax_on_grant
    
    rows.append({
        "שנה": yr,
        "ברוטו כולל": (pension * months_in_year) + ann_grant,
        "מס שנתי": tax_total * 12,
        "נטו שנתי": ((pension * months_in_year) + ann_grant) - (tax_total * 12),
        "מדרגת מס": f"{m_rate*100:.0f}%"
    })

# הצגת תוצאות
st.table(pd.DataFrame(rows))

tax_no_spread = taxable_grant * 0.47
saving = tax_no_spread - total_tax_spread

st.divider()
c1, c2, c3 = st.columns(3)
c1.error(f"מס ללא פריסה: {fmt_num(tax_no_spread)}")
c2.warning(f"מס בפריסה: {fmt_num(total_tax_spread)}")
c3.success(f"חיסכון נקי: {fmt_num(saving)}")