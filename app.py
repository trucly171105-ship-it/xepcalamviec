import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px

# Cấu hình trang
st.set_page_config(
    page_title="Quản lý xếp ca hướng dẫn viên du lịch",
    page_icon="🧭",
    layout="wide"
)

# Khởi tạo session state lưu trữ dữ liệu
if "hdv_list" not in st.session_state:
    st.session_state.hdv_list = [
        {"id": 1, "ten": "Nguyễn Văn A", "chuyen_mon": "Trong nước", "so_ngay_nghi": 4},
        {"id": 2, "ten": "Trần Thị B", "chuyen_mon": "Quốc tế", "so_ngay_nghi": 4},
        {"id": 3, "ten": "Lê Văn C", "chuyen_mon": "Trekking", "so_ngay_nghi": 4},
    ]

if "lich_trinh_list" not in st.session_state:
    st.session_state.lich_trinh_list = []

if "phân_ca" not in st.session_state:
    st.session_state.phân_ca = pd.DataFrame()

# Hàm tiện ích
def lay_danh_sach_ngay(tuan=None):
    today = datetime.today().date()
    if tuan:
        start = today - timedelta(days=today.weekday()) + timedelta(weeks=tuan-1)
    else:
        start = today - timedelta(days=today.weekday())
    return [start + timedelta(days=i) for i in range(7)]

# Sidebar quản lý dữ liệu
with st.sidebar:
    st.header("⚙️ Quản lý dữ liệu")

    # Form thêm hướng dẫn viên
    with st.expander("Thêm hướng dẫn viên"):
        ten_hdv = st.text_input("Tên hướng dẫn viên")
        chuyen_mon = st.selectbox("Chuyên môn", ["Trong nước", "Quốc tế", "Trekking", "Đường dài"])
        so_ngay_nghi = st.number_input("Số ngày nghỉ/tuần", min_value=1, max_value=7, value=4)
        if st.button("Thêm hướng dẫn viên"):
            new_id = max([x["id"] for x in st.session_state.hdv_list], default=0) + 1
            st.session_state.hdv_list.append({
                "id": new_id,
                "ten": ten_hdv,
                "chuyen_mon": chuyen_mon,
                "so_ngay_nghi": so_ngay_nghi
            })
            st.success(f"Đã thêm {ten_hdv}")

    # Form thêm lịch tour
    with st.expander("Thêm lịch tour"):
        ten_tour = st.text_input("Tên tour")
        ngay_khoi_hanh = st.date_input("Ngày khởi hành")
        loai_tour = st.selectbox("Loại tour", ["Trong nước", "Quốc tế", "Trekking"])
        so_luong_hdv_can = st.number_input("Số HDV cần phân", min_value=1, value=1)
        if st.button("Thêm lịch tour"):
            new_id = max([x["id"] for x in st.session_state.lich_trinh_list], default=0) + 1
            st.session_state.lich_trinh_list.append({
                "id": new_id,
                "ten_tour": ten_tour,
                "ngay_khoi_hanh": ngay_khoi_hanh,
                "loai_tour": loai_tour,
                "so_luong_hdv_can": so_luong_hdv_can,
                "hdv_phan_ca": []
            })
            st.success(f"Đã thêm tour {ten_tour}")

# Nội dung chính
st.title("🧭 Hệ thống xếp ca hướng dẫn viên du lịch")

tab1, tab2, tab3, tab4 = st.tabs(["Danh sách HDV", "Lịch tour", "Xếp ca tự động", "Xem lịch phân ca"])

with tab1:
    st.subheader("Danh sách hướng dẫn viên")
    df_hdv = pd.DataFrame(st.session_state.hdv_list)
    st.dataframe(df_hdv[["ten", "chuyen_mon", "so_ngay_nghi"]], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Danh sách lịch tour cần phân ca")
    if not st.session_state.lich_trinh_list:
        st.info("Chưa có lịch tour nào được thêm vào")
    else:
        df_tour = pd.DataFrame(st.session_state.lich_trinh_list)
        df_tour["ngay_khoi_hanh"] = df_tour["ngay_khoi_hanh"].apply(lambda x: x.strftime("%d/%m/%Y"))
        st.dataframe(df_tour[["ten_tour", "ngay_khoi_hanh", "loai_tour", "so_luong_hdv_can"]], use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Xếp ca tự động theo điều kiện")
    tuan_chon = st.selectbox("Chọn tuần", [f"Tuần {i}" for i in range(1, 5)])
    ngay_trong_tuan = lay_danh_sach(int(tuan_chon.split()))

    if st.button("Bắt đầu xếp ca tự động"):
        ds_phân_ca = []
        for tour in st.session_state.lich_trinh_list:
            ngay_tour = tour["ngay_khoi_hanh"]
            if ngay_tour not in ngay_trong_tuan:
                continue

            # Lọc HDV phù hợp chuyên môn
            hdv_phu_hop = [
                hdv for hdv in st.session_state.hdv_list
                if hdv["chuyen_mon"] == tour["loai_tour"]
            ]

            for i in range(tour["so_luong_hdv_can"]):
                if hdv_phu_hop:
                    hdv_chon = hdv_phu_hop.pop(0)
                    ds_phân_ca.append({
                        "Ngày": ngay_tour.strftime("%d/%m/%Y"),
                        "Hướng dẫn viên": hdv_chon["ten"],
                        "Chuyên môn": hdv_chon["chuyen_mon"],
                        "Tour": tour["ten_tour"],
                        "Loại tour": tour["loai_tour"]
                    })

        if ds_phân_ca:
            st.session_state.phân_ca = pd.DataFrame(ds_phân_ca)
            st.success(f"Đã phân ca thành công cho {len(ds_phân_ca)} lượt phân công!")
        else:
            st.warning("Không có tour nào phù hợp với tuần đã chọn")

    st.subheader("Phân ca thủ công")
    col1, col2, col3 = st.columns(3)
    with col1: hdv_chon = st.selectbox("Chọn hướng dẫn viên", [x["ten"] for x in st.session_state.hdv_list])
    with col2: ngay_chon = st.date_input("Chọn ngày phân ca")
    with col3: tour_chon = st.selectbox("Gán cho tour", [x["ten_tour"] for x in st.session_state.lich_trinh_list])
    if st.button("Lưu phân công thủ công"):
        hdv_info = next(x for x in st.session_state.hdv_list if x["ten"] == hdv_chon)
        new_row = pd.DataFrame([{
            "Ngày": ngay_chon.strftime("%d/%m/%Y"),
            "Hướng dẫn viên": hdv_chon,
            "Chuyên môn": hdv_info["chuyen_mon"],
            "Tour": tour_chon,
            "Loại tour": next(x for x in st.session_state.lich_trinh_list if x["ten_tour"] == tour_chon)["loai_tour"]
        }])
        st.session_state.phân_ca = pd.concat([st.session_state.phân_ca, new_row], ignore_index=True)
        st.success("Đã lưu phân công thủ công!")

with tab4:
    st.subheader("Lịch phân ca theo ngày")
    if st.session_state.phân_ca.empty:
        st.info("Chưa có lịch phân ca nào được tạo")
    else:
        st.dataframe(st.session_state.phân_ca, use_container_width=True, hide_index=True)

        # Biểu đồ thống kê số tour của mỗi HDV
        st.subheader("📊 Thống kê khối lượng công việc")
        thong_ke = st.session_state.phân_ca.groupby("Hướng dẫn viên").size().reset_index(name="Số tour được phân")
        fig = px.bar(thong_ke, x="Hướng dẫn viên", y="Số tour được phân", color="Hướng dẫn viên")
        st.plotly_chart(fig, use_container_width=True)

        # Nút xuất file Excel
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df(st.session_state.phân_ca)
        st.download_button(
            label="📥 Tải xuống lịch phân ca CSV",
            data=csv,
            file_name=f"lich_phan_ca_{datetime.today().strftime('%d-%m-%Y')}.csv",
            mime='text/csv'
        )

