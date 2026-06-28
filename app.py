import streamlit as st
import pymannkendall as mk
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime, timedelta

# Cấu hình trang
st.set_page_config(
    page_title="Phân tích cổ phiếu VCB",
    page_icon="📈",
    layout="wide"
)

# Tiêu đề ứng dụng
st.title("📊 Phân tích Cổ phiếu VCB")
st.markdown("---")

# Sidebar - nhập thông số
st.sidebar.header("⚙️ Cài đặt")
ticker = st.sidebar.text_input("Mã cổ phiếu", value="VCB.VN")
start_date = st.sidebar.date_input(
    "Ngày bắt đầu",
    value=datetime(2026, 1, 1),
    max_value=datetime.now()
)
end_date = st.sidebar.date_input(
    "Ngày kết thúc",
    value=datetime(2026, 6, 27),
    max_value=datetime.now()
)

# Nút tải dữ liệu
if st.sidebar.button("📥 Tải dữ liệu", type="primary"):
    with st.spinner("Đang tải dữ liệu..."):
        # Tải dữ liệu
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if df.empty:
            st.error("Không tìm thấy dữ liệu cho mã cổ phiếu này!")
            st.stop()
        
        # Xử lý dữ liệu
        df.columns = df.columns.droplevel('Ticker')
        full_date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
        df = df.reindex(full_date_range)
        df = df.ffill()
        df['simple_ret'] = df['Close'].pct_change()
        df['log_ret'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Lưu vào session state
        st.session_state['df'] = df
        st.session_state['ticker'] = ticker
        st.session_state['start_date'] = start_date
        st.session_state['end_date'] = end_date

# Kiểm tra dữ liệu đã tải chưa
if 'df' not in st.session_state:
    st.info("👈 Vui lòng nhập thông tin và nhấn 'Tải dữ liệu' để bắt đầu")
    st.stop()

df = st.session_state['df']
ticker = st.session_state['ticker']

# Hiển thị thông tin dữ liệu
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Thông tin dữ liệu")
st.sidebar.write(f"**Số ngày:** {len(df)}")
st.sidebar.write(f"**Từ:** {df.index.min().strftime('%d/%m/%Y')}")
st.sidebar.write(f"**Đến:** {df.index.max().strftime('%d/%m/%Y')}")
st.sidebar.write(f"**Giá cao nhất:** {df['High'].max():,.0f} VND")
st.sidebar.write(f"**Giá thấp nhất:** {df['Low'].min():,.0f} VND")

# Main content - tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Biểu đồ giá", "📊 Biểu đồ nến", "📉 Phân tích xu hướng", "📋 Dữ liệu"])

# Tab 1: Biểu đồ giá và log return
with tab1:
    st.subheader("Biểu đồ giá và log return")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Biểu đồ giá đóng cửa
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df.index, df['Close'], color='red', linewidth=1.5, label='GIÁ ĐÓNG CỬA')
        ax1.set_title(f'GIÁ ĐÓNG CỬA CỦA CỔ PHIẾU {ticker}')
        ax1.set_ylabel('VND')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        st.pyplot(fig1)
    
    with col2:
        # Biểu đồ log return
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(df.index, df['log_ret'], color='green', linewidth=1, label='Log Return')
        ax2.set_title(f'{ticker} Log Return')
        ax2.set_ylabel('Log Return')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        st.pyplot(fig2)
    
    # Thống kê nhanh
    st.subheader("📊 Thống kê nhanh")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Giá đóng cửa cuối", f"{df['Close'].iloc[-1]:,.0f} VND", 
                 f"{((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100):.2f}%")
    with col2:
        st.metric("Giá cao nhất", f"{df['High'].max():,.0f} VND")
    with col3:
        st.metric("Giá thấp nhất", f"{df['Low'].min():,.0f} VND")
    with col4:
        st.metric("Khối lượng trung bình", f"{df['Volume'].mean():,.0f}")

# Tab 2: Biểu đồ nến
with tab2:
    st.subheader("Biểu đồ nến Nhật")
    
    # Tùy chọn MA
    ma_periods = st.multiselect(
        "Chọn đường trung bình động (MA)",
        options=[5, 10, 20, 50, 100],
        default=[10, 20]
    )
    
    # Vẽ biểu đồ nến với mplfinance
    fig3, axes = mpf.plot(
        df,
        type="candle",
        mav=ma_periods if ma_periods else None,
        volume=True,
        style="yahoo",
        title=f"GIÁ CỔ PHIẾU {ticker} TỪ {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
        figsize=(12, 6),
        returnfig=True
    )
    st.pyplot(fig3)

# Tab 3: Phân tích xu hướng Mann-Kendall
with tab3:
    st.subheader("📉 Phân tích xu hướng Mann-Kendall")
    
    # Lấy giá đóng cửa
    close_prices = df["Close"].dropna().reset_index(drop=True)
    
    # Thực hiện kiểm định
    with st.spinner("Đang tính toán..."):
        result = mk.original_test(close_prices)
        
        # Hiển thị kết quả
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Xu hướng",
                result.trend,
                help="Xu hướng tăng, giảm hoặc không có xu hướng"
            )
        
        with col2:
            p_value = result.p
            significance = "✅ Có ý nghĩa" if p_value < 0.05 else "❌ Không có ý nghĩa"
            st.metric(
                "p-value",
                f"{p_value:.4f}",
                delta=significance
            )
        
        with col3:
            st.metric(
                "Tau (Kendall's Tau)",
                f"{result.Tau:.4f}",
                help="Hệ số tương quan Kendall - độ mạnh của xu hướng"
            )
        
        # Diễn giải chi tiết
        st.markdown("### 📝 Diễn giải")
        st.write(f"- **Xu hướng:** {result.trend}")
        st.write(f"- **p-value:** {result.p:.6f}")
        st.write(f"- **Kendall's Tau:** {result.Tau:.4f}")
        st.write(f"- **Phương sai S:** {result.var_s:.4f}")
        
        if result.p < 0.05:
            st.success("✅ **Kết luận:** Có xu hướng đáng kể về mặt thống kê.")
            if result.trend == 'increasing':
                st.info("📈 Xu hướng tăng - Giá cổ phiếu có xu hướng tăng trong giai đoạn này.")
            elif result.trend == 'decreasing':
                st.info("📉 Xu hướng giảm - Giá cổ phiếu có xu hướng giảm trong giai đoạn này.")
        else:
            st.warning("⚠️ **Kết luận:** Không có xu hướng rõ ràng về mặt thống kê.")
            st.info("Giá cổ phiếu biến động không có xu hướng rõ rệt trong giai đoạn này.")
        
        # Biểu đồ phân tích xu hướng
        st.subheader("📈 Xu hướng giá và đường trung bình")
        fig4, ax4 = plt.subplots(figsize=(12, 6))
        ax4.plot(df.index, df['Close'], color='blue', linewidth=1, label='Giá đóng cửa')
        ax4.plot(df.index, df['Close'].rolling(20).mean(), color='orange', linewidth=2, label='MA 20 ngày')
        ax4.plot(df.index, df['Close'].rolling(50).mean(), color='green', linewidth=2, label='MA 50 ngày')
        ax4.set_title(f'Xu hướng giá {ticker}')
        ax4.set_ylabel('VND')
        ax4.set_xlabel('Date')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        st.pyplot(fig4)

# Tab 4: Dữ liệu
with tab4:
    st.subheader("📋 Dữ liệu chi tiết")
    
    # Hiển thị dữ liệu với slider
    st.write(f"Hiển thị dữ liệu từ {df.index.min().strftime('%d/%m/%Y')} đến {df.index.max().strftime('%d/%m/%Y')}")
    st.dataframe(
        df[['Open', 'High', 'Low', 'Close', 'Volume', 'simple_ret', 'log_ret']],
        height=400,
        use_container_width=True
    )
    
    # Nút tải xuống
    csv = df.to_csv()
    st.download_button(
        label="📥 Tải dữ liệu CSV",
        data=csv,
        file_name=f"{ticker}_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.caption(f"🔄 Dữ liệu được lấy từ Yahoo Finance | Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
