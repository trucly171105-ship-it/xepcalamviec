import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Quản lý xếp ca hướng dẫn viên du lịch",
    page_icon="🧭",
    layout="wide"
)

# Khởi tạo dữ liệu lưu trữ trong session state (để giữ dữ liệu khi deploy lên Streamlit Cloud)
if "hdv_list" not in st.session_state:
    st.session_state.hdv_list = [
        {"id": 1, "ten": "Nguyễn Văn A", "chuyen_mon": "Trong nước", "so_ngay_nghi": 4},
        {"id": 2, "ten": "Trần Thị B", "chuyen_mon": "Quốc tế", "so_ngay_nghi": 4},
        {"id": 3, "ten": "Lê Văn C", "chuyen_mon": "Trekking", "so_ngay_nghi": 4},
    ]

if "lich_trinh_list" not in st.session_state:
    st.session_state.lich_trinh_list = []

if "phân_ca" not in st.session_state:
    st.session_state.phân_ca = pd.DataFrame(columns=["Ngày", "Hướng dẫn viên", "Chuyên môn", "Tour", "Loại tour"])

# Hàm tiện ích lấy danh sách ngày theo tuần
def lay_danh_sach_ngay(tuan=None):
    today = datetime.today().date()
    if tuan:
        start = today - timedelta(days=today.weekday()) + timedelta(weeks=tuan-1)
    else:
        start = today - timedelta(days=today.weekday())
    return [start + timedelta(days=i) for i in range(7)]

# Giao diện Sidebar quản lý dữ liệu
with st.sidebar:
    st.header("⚙️ Quản lý dữ liệu")

    # Form thêm hướng dẫn viên
    with st.expander("Thêm hướng dẫn viên"):
        ten_hdv = st.text_input("Tên hướng dẫn viên", key="ten_hdv")
        chuyen_mon = st.selectbox("Chuyên môn", ["Trong nước", "Quốc tế", "Trekking", "Đường dài"], key="chuyen_mon")
        so_ngay_nghi = st.number_input("Số ngày nghỉ/tuần", min_value=1, max_value=7, value=4, key="so_ngay_nghi")
        if st.button("Thêm hướng dẫn viên", type="primary"):
            new_id = max([x["id"] for x in st.session_state.hdv_list], default=0) + 1
            st.session_state.hdv_list.append({
                "id": new_id,
                "ten": ten_hdv,
                "chuyen_mon": chuyen_mon,
                "so_ngay_nghi": so_ngay_nghi
            })
            st.success(f"Đã thêm thành công hướng dẫn viên {ten_hdv}")

    # Form thêm lịch tour
    with st.expander("Thêm lịch tour mới"):
        ten_tour = st.text_input("Tên tour", key="ten_tour")
        ngay_khoi_hanh = st.date_input("Ngày khởi hành", key="ngay_khoi_hanh")
        loai_tour = st.selectbox("Loại tour", ["Trong nước", "Quốc tế", "Trekking"], key="loai_tour")
        so_luong_hdv_can = st.number_input("Số lượng HDV cần phân", min_value=1, value=1, key="so_luong_hdv_can")
        if st.button("Thêm lịch tour", type="primary"):
            new_id = max([x["id"] for x in st.session_state.lich_trinh_list], default=0) + 1
            st.session_state.lich_trinh_list.append({
                "id": new_id,
                "ten_tour": ten_tour,
                "ngay_khoi_hanh": ngay_khoi_hanh,
                "loai_tour": loai_tour,
                "so_luong_hdv_can": so_luong_hdv_can,
                "hdv_phan_ca": []
            })
            st.success(f"Đã thêm lịch tour {ten_tour}")

# Nội dung chính của ứng dụng
st.title("🧭 Hệ thống xếp ca hướng dẫn viên du lịch")

tab1, tab2, tab3, tab4 = st.tabs(["Danh sách hướng dẫn viên", "Lịch tour", "Xếp ca tự động", "Xem lịch phân ca"])

with tab1:
    st.subheader("Danh sách tất cả hướng dẫn viên")
    if not st.session_state.hdv_list:
        st.info("Chưa có hướng dẫn viên nào được thêm")
    else:
        df_hdv = pd.DataFrame(st.session_state.hdv_list)
        st.dataframe(df_hdv[["ten", "chuyen_mon", "so_ngay_nghi"]], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Danh sách lịch tour cần phân công")
    if not st.session_state.lich_trinh_list:
        st.info("Chưa có lịch tour nào được thêm")
    else:
        df_tour = pd.DataFrame(st.session_state.lich_trinh_list)
        df_tour["ngay_khoi_hanh"] = df_tour["ngay_khoi_hanh"].apply(lambda x: x.strftime("%d/%m/%Y"))
        st.dataframe(df_tour[["ten_tour", "ngay_khoi_hanh", "loai_tour", "so_luong_hdv_can"]], use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Xếp ca tự động theo chuyên môn")
    tuan_chon = st.selectbox("Chọn tuần cần phân ca", [f"Tuần {i}" for i in range(1, 6)])
    ngay_trong_tuan = lay_danh_sach_ngay(int(tuan_chon.split()[-1]))

    if st.button("Bắt đầu xếp ca tự động", type="primary"):
        ds_phân_ca_moi = []
        # Lọc tour nằm trong tuần đã chọn
        for tour in st.session_state.lich_trinh_list:
            ngay_tour = tour["ngay_khoi_hanh"]
            if ngay_tour not in ngay_trong_tuan:
                continue

            # Lọc hướng dẫn viên phù hợp chuyên môn của tour
            hdv_phu_hop = [
                hdv for hdv in st.session_state.hdv_list
                if hdv["chuyen_mon"] == tour["loai_tour"]
            ]

            # Phân công số lượng HDV cần cho tour
            for i in range(tour["so_luong_hdv_can"]):
                if hdv_phu_hop:
                    hdv_chon = hdv_phu_hop.pop(0)
                    ds_phân_ca_moi.append({
                        "Ngày": ngay_tour.strftime("%d/%m/%Y"),
                        "Hướng dẫn viên": hdv_chon["ten"],
                        "Chuyên môn": hdv_chon["chuyen_mon"],
                        "Tour": tour["ten_tour"],
                        "Loại tour": tour["loai_tour"]
                    })

        # Cập nhật bảng phân ca
        if ds_phân_ca_moi:
            # Thêm dữ liệu mới vào bảng hiện tại (không trùng lặp)
            df_moi = pd.DataFrame(ds_phân_ca_moi)
            if st.session_state.phân_ca.empty:
                st.session_state.phân_ca = df_moi
            else:
                st.session_state.phân_ca = pd.concat([st.session_state.phân_ca, df_moi], ignore_index=True)
            st.success(f"Đã phân ca thành công {len(ds_phân_ca_moi)} lượt cho tuần {tuan_chon}")
        else:
            st.warning("Không có tour hoặc hướng dẫn viên phù hợp trong tuần đã chọn")

    # Phân ca thủ công
    st.subheader("Phân ca thủ công")
    col1, col2, col3 = st.columns(3)
    with col1:
        ten_hdv_list = [x["ten"] for x in st.session_state.hdv_list]
        hdv_chon = st.selectbox("Chọn hướng dẫn viên", ten_hdv_list if ten_hdv_list else ["Chưa có HDV"])
    with col2:
        ngay_chon = st.date_input("Chọn ngày phân công")
    with col3:
        tour_list = [x["ten_tour"] for x in st.session_state.lich_trinh_list]
        tour_chon = st.selectbox("Gán cho tour", tour_list if tour_list else ["Chưa có tour"])
    
    if st.button("Lưu phân công thủ công", type="secondary") and ten_hdv_list and tour_list:
        hdv_info = next(x for x in st.session_state.hdv_list if x["ten"] == hdv_chon)
        tour_info = next(x for x in st.session_state.lich_trinh_list if x["ten_tour"] == tour_chon)
        new_row = pd.DataFrame([{
            "Ngày": ngay_chon.strftime("%d/%m/%Y"),
            "Hướng dẫn viên": hdv_chon,
            "Chuyên môn": hdv_info["chuyen_mon"],
            "Tour": tour_chon,
            "Loại tour": tour_info["loai_tour"]
        }])
        st.session_state.phân_ca = pd.concat([st.session_state.phân_ca, new_row], ignore_index=True)
        st.success("Đã lưu phân công thủ công thành công")

with tab4:
    st.subheader("Toàn bộ lịch phân ca")
    if st.session_state.phân_ca.empty:
        st.info("Chưa có lịch phân ca nào được tạo")
    else:
        # Hiển thị bảng lịch phân ca
        st.dataframe(st.session_state.phân_ca, use_container_width=True, hide_index=True)
        
        # Biểu đồ thống kê số lượng công việc của từng HDV
        st.subheader("📊 Thống kê khối lượng công việc")
        thong_ke_hdv = st.session_state.phân_ca["Hướng dẫn viên"].value_counts().reset_index()
        thong_ke_hdv.columns = ["Hướng dẫn viên", "Số tour đã phân"]
        
        fig = px.bar(
            thong_ke_hdv,
            x="Hướng dẫn viên",
            y="Số tour đã phân",
            color="Hướng dẫn viên",
            title="Số lượng tour được phân công cho mỗi hướng dẫn viên",
            text="Số tour đã phân"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Nút xuất file CSV để tải về
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
        
        csv_data = convert_df(st.session_state.phân_ca)
        st.download_button(
            label="📥 Tải lịch phân ca về file CSV",
            data=csv_data,
            file_name=f"lich_phan_ca_{datetime.today().strftime('%d-%m-%Y')}.csv",
            mime='text/csv'
        )
