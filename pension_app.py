import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime

# --- פונקציית היפוך טקסט (Visual Hebrew) ---
def hb(text):
    if not text:
        return ""
    return str(text)[::-1]

def fmt_num(num):
    return f"{float(num):,.0f}"

# --- אבטחה ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.markdown("<h2 style='text-align: right;'>כניסה למערכת</h2>", unsafe_allow_html=True)
    password = st.text_input("הזן קוד גישה", type="password")
    if st.button("התחבר"):
        if password == "1234":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("קוד שגוי")
    return False

# --- חישובי מס ---
def calculate_tax_detailed(annual_income, points=2.25):
    brackets = [(84120, 0.10), (120720, 0.14), (193800, 0.20), (269280, 0.31), (560280, 0.35), (721560, 0.47), (float('inf'), 0.50)]
    tax, prev_limit = 0, 0
    for limit, rate in brackets:
        if annual_income > limit:
            tax += (limit - prev_limit) * rate
            prev_limit = limit
        else:
            tax += (annual_income - prev_limit) * rate
            break
    surtax = max(0, (annual_income - 721560) * 0.03)
    return max(0, (tax + surtax) - (points * 2904))

# --- יצירת דוח PDF (הגרסה שעבדה) ---
def generate_pdf_report(data_dict, table_rows):
    pdf = FPDF()
    pdf.add_page()
    
    # שימוש בפונט Arial עם תמיכה בסיסית
    pdf.add_font('Arial', '', 'arial.ttf', uni=True)
    pdf.add_font('Arial', 'B', 'arialbd.ttf', uni=True)
    pdf.set_font('Arial', '', 12)

    # כותרת ותאריך
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, hb(f"תאריך הפקה: {datetime.now().strftime('%d/%m/%Y')}"), ln=1, align='L')
    
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, hb("דוח סימולציית פריסת מס"), ln=1, align='C')
    
    pdf.set_font('Arial', '', 12)
    pdf.ln(5)
    pdf.cell(0, 8, hb(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=1, align='R')
    pdf.cell(0, 8, hb(f"סוכן מטפל: {data_dict['agent_name']}"), ln=1, align='R')
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    
    # נתוני המענק
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, hb("נתוני מענק:"), ln=1, align='R')
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, hb(f"סך המענק ברוטו: {fmt_num(data_dict['total_grant'])} שח"), ln=1, align='R')
    pdf.cell(0, 8, hb(f"חלק המענק הפטור: {fmt_num(data_dict['exempt'])} שח"), ln=1, align='R')
    pdf.cell(0, 8, hb(f"חלק המענק החייב: {fmt_num(data_dict['taxable'])} שח"), ln=1, align='R')
    
    # טבלת פריסה
    pdf.ln(10)
    pdf.set_fill_color(230, 240, 255)
    pdf.set_font('Arial', 'B', 10)
    # סדר עמודות הפוך להצגה מימין לשמאל
    pdf.cell(40, 10, hb("מס שנתי"), 1, 0, 'C', True)
    pdf.cell(50, 10, hb("הכנסה כוללת"), 1, 0, 'C', True)
    pdf.cell(50, 10, hb("חלק המענק"), 1, 0, 'C', True)
    pdf.cell(30, 10, hb("שנה"), 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 10)
    for row in table_rows:
        pdf.cell(40, 8, hb(row['מס']), 1, 0, 'C')
        pdf.cell(50, 8, hb(row['הכנסה שנתית']), 1, 0, 'C')
        pdf.cell(50, 8, hb(row['חלק המענק']), 1, 0, 'C')
        pdf.cell(30, 8, hb(row['שנה']), 1, 1, 'C')

    pdf.ln(15)
    pdf.cell(90, 10, hb("________________ :חתימת הלקוח"), 0, 0, 'R')
    pdf.cell(90, 10, hb("________________ :חתימת הסוכן"), 0, 1, 'R')

    # פלט כ-bytes
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- ממשק
