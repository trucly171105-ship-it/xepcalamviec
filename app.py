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

# Khởi tạo dữ liệu trong session state
if "hdv_list" not in st.session_state:
    st.session_state.hdv_list = [
        {"id": 1, "Tên": "Nguyễn Văn A", "Chuyên môn": "Trong nước", "Số ngày nghỉ": 4, "ngay_nghi": []},
        {"id": 2, "Tên": "Trần Thị B", "Chuyên môn": "Quốc tế", "Số ngày nghỉ": 4, "ngay_nghi": []},
        {"id": 3, "Tên": "Lê Văn C", "Chuyên môn": "Trekking", "Số ngày nghỉ": 4, "ngay_nghi": []},
    ]

if "lich_trinh_list" not in st.session_state:
    st.session_state.lich_trinh_list = []

if "phân_ca" not in st.session_state:
    st.session_state.phân_ca = pd.DataFrame(columns=["Ngày", "Hướng dẫn viên", "Chuyên môn", "Tour", "Loại tour"])

# Hàm tiện ích
def lay_danh_sach_ngay(tuan=None):
    today = datetime.today().date()
    if tuan:
        start = today - timedelta(days=today.weekday()) + timedelta(weeks=tuan-1)
    else:
        start = today - timedelta(days=today.weekday())
    return [start + timedelta(days=i) for i in range(7)]

# --- TÍNH NĂNG 1: Cảnh báo xung đột lịch làm việc ---
def kiem_tra_xung_dot(hdv, ngay_moi):
    """Kiểm tra xem hướng dẫn viên có bị phân công trùng ngày không"""
    if st.session_state.phân_ca.empty:
        return False
    ca_cua_hdv = st.session_state.phân_ca[st.session_state.phân_ca["Hướng dẫn viên"] == hdv]
    return ngay_moi.strftime("%d/%m/%Y") in ca_cua_hdv["Ngày"].values

# --- TÍNH NĂNG 2: Đăng ký nghỉ phép & xác thực tự động ---
def them_ngay_nghi(hdv_id, ngay_nghi):
    """Thêm ngày nghỉ vào danh sách của hướng dẫn viên"""
    hdv = next(x for x in st.session_state.hdv_list if x["id"] == hdv_id)
    ngay_str = ngay_nghi.strftime("%d/%m/%Y")
    if ngay_str not in hdv["ngay_nghi"]:
        hdv["ngay_nghi"].append(ngay_str)
        return True
    return False

# --- TÍNH NĂNG 3: Thống kê khối lượng công việc tự cân bằng ---
def tinh_thong_ke_can_bang():
    """Tính số tour của từng HDV và so sánh với trung bình"""
    if st.session_state.phân_ca.empty:
        return pd.DataFrame()
    thong_ke = st.session_state.phân_ca["Hướng dẫn viên"].value_counts().reset_index()
    thong_ke.columns = ["Hướng dẫn viên", "Số tour đã làm"]
    trung_binh = thong_ke["Số tour đã làm"].mean()
    thong_ke["Chênh lệch so với trung bình"] = thong_ke["Số tour đã làm"] - trung_binh
    return thong_ke

# --- TÍNH NĂNG 4: Nhắc nhở lịch làm việc ---
def lay_lich_nhac_nho(hdv_ten):
    """Lấy danh sách tour sắp tới của HDV trong 7 ngày tới"""
    if st.session_state.phân_ca.empty:
        return []
    ngay_hien_tai = datetime.today().date()
    lich = st.session_state.phân_ca[
        (st.session_state.phân_ca["Hướng dẫn viên"] == hdv_ten) &
        (pd.to_datetime(st.session_state.phân_ca["Ngày"], format="%d/%m/%Y").dt.date >= ngay_hien_tai) &
        (pd.to_datetime(st.session_state.phân_ca["Ngày"], format="%d/%m/%Y").dt.date <= ngay_hien_tai + timedelta(days=7))
    ]
    return lich[["Ngày", "Tour"]].values.tolist()

# Sidebar quản lý dữ liệu
with st.sidebar:
    st.header("⚙️ Quản lý dữ liệu")

    # Form thêm hướng dẫn viên
    with st.expander("Thêm hướng dẫn viên"):
        ten_hdv = st.text_input("Tên hướng dẫn viên")
        chuyen_mon = st.selectbox("Chuyên môn", ["Trong nước", "Quốc tế", "Trekking", "Đường dài"])
        so_ngay_nghi = st.number_input("Số ngày nghỉ/tuần", min_value=1, max_value=7, value=4)
        if st.button("Thêm hướng dẫn viên", type="primary"):
            new_id = max([x["id"] for x in st.session_state.hdv_list], default=0) + 1
            st.session_state.hdv_list.append({
                "id": new_id,
                "ten": ten_hdv,
                "chuyen_mon": chuyen_mon,
                "so_ngay_nghi": so_ngay_nghi,
                "ngay_nghi": []
            })
            st.success(f"Đã thêm {ten_hdv}")

    # Form đăng ký nghỉ phép 
    with st.expander("Đăng ký nghỉ phép"):
        hdv_cho_nghi = st.selectbox("Chọn hướng dẫn viên", [x["ten"] for x in st.session_state.hdv_list])
        ngay_nghi = st.date_input("Chọn ngày nghỉ")
        if st.button("Gửi đơn nghỉ phép", type="secondary"):
            hdv_id = next(x["id"] for x in st.session_state.hdv_list if x["ten"] == hdv_cho_nghi)
            if them_ngay_nghi(hdv_id, ngay_nghi):
                st.success(f"Đã đăng ký nghỉ ngày {ngay_nghi.strftime('%d/%m/%Y')} cho {hdv_cho_nghi}")
            else:
                st.warning("Ngày này đã được đăng ký nghỉ trước đó")

# Nội dung chính
st.title("🧭 Hệ thống xếp ca hướng dẫn viên du lịch")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Danh sách HDV", "Lịch tour", "Xếp ca tự động", "Thống kê cân bằng", "Lịch nhắc nhở"])

with tab1:
    st.subheader("Danh sách hướng dẫn viên")
    df_hdv = pd.DataFrame(st.session_state.hdv_list)
    st.dataframe(df_hdv[["ten", "chuyen_mon", "so_ngay_nghi", "ngay_nghi"]], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Danh sách lịch tour")
    if not st.session_state.lich_trinh_list:
        st.info("Chưa có lịch tour nào")
    else:
        df_tour = pd.DataFrame(st.session_state.lich_trinh_list)
        df_tour["ngay_khoi_hanh"] = df_tour["ngay_khoi_hanh"].apply(lambda x: x.strftime("%d/%m/%Y"))
        st.dataframe(df_tour[["ten_tour", "ngay_khoi_hanh", "loai_tour", "so_luong_hdv_can"]], use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Xếp ca tự động & thủ công")
    tuan_chon = st.selectbox("Chọn tuần", [f"Tuần {i}" for i in range(1,6)])
    ngay_trong_tuan = lay_danh_sach_ngay(int(tuan_chon.split()[-1]))

    if st.button("Bắt đầu xếp ca", type="primary"):
        ds_phân_ca_moi = []
        xung_dot = []
        for tour in st.session_state.lich_trinh_list:
            ngay_tour = tour["ngay_khoi_hanh"]
            if ngay_tour not in ngay_trong_tuan:
                continue

            hdv_phu_hop = [
                hdv for hdv in st.session_state.hdv_list
                if hdv["chuyen_mon"] == tour["loai_tour"] and ngay_tour.strftime("%d/%m/%Y") not in hdv["ngay_nghi"]
            ]

            for i in range(tour["so_luong_hdv_can"]):
                if hdv_phu_hop:
                    hdv_chon = hdv_phu_hop.pop(0)
                    # Kiểm tra xung đột 
                    if kiem_tra_xung_dot(hdv_chon["ten"], ngay_tour):
                        xung_dot.append(f"HDV {hdv_chon['ten']} trùng lịch tour {tour['ten_tour']} ngày {ngay_tour.strftime('%d/%m/%Y')}")
                    else:
                        ds_phân_ca_moi.append({
                            "Ngày": ngay_tour.strftime("%d/%m/%Y"),
                            "Hướng dẫn viên": hdv_chon["ten"],
                            "Chuyên môn": hdv_chon["chuyen_mon"],
                            "Tour": tour["ten_tour"],
                            "Loại tour": tour["loai_tour"]
                        })

        # Cập nhật lịch phân ca
        if ds_phân_ca_moi:
            if st.session_state.phân_ca.empty:
                st.session_state.phân_ca = pd.DataFrame(ds_phân_ca_moi)
            else:
                st.session_state.phân_ca = pd.concat([st.session_state.phân_ca, pd.DataFrame(ds_phân_ca_moi)], ignore_index=True)
            st.success(f"Đã phân công {len(ds_phân_ca_moi)} lượt")
            # Hiển thị cảnh báo xung đột nếu có
            if xung_dot:
                st.warning("⚠️ Có các xung đột lịch:")
                for thong_bao in xung_dot:
                    st.write(f"- {thong_bao}")

    # Phân ca thủ công
    st.subheader("Phân ca thủ công")
    col1, col2, col3 = st.columns(3)
    with col1:
        hdv_list = [x["ten"] for x in st.session_state.hdv_list]
        hdv_chon = st.selectbox("Chọn HDV", hdv_list if hdv_list else ["Chưa có HDV"])
    with col2:
        ngay_chon = st.date_input("Chọn ngày")
    with col3:
        tour_list = [x["ten_tour"] for x in st.session_state.lich_trinh_list]
        tour_chon = st.selectbox("Chọn tour", tour_list if tour_list else ["Chưa có tour"])

    if st.button("Lưu phân công thủ công", type="secondary"):
        if kiem_tra_xung_dot(hdv_chon, ngay_chon):
            st.error("⚠️ HDV này đã được phân công ca khác vào ngày này!")
        else:
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
            st.success("Đã lưu phân công thủ công")

with tab4:
    st.subheader("Thống kê cân bằng công việc")
    thong_ke = tinh_thong_ke_can_bang()
    if thong_ke.empty:
        st.info("Chưa có dữ liệu phân ca để thống kê")
    else:
        st.dataframe(thong_ke, use_container_width=True, hide_index=True)
        # Biểu đồ so sánh
        fig = px.bar(thong_ke, x="Hướng dẫn viên", y="Số tour đã làm", color="Chênh lệch so với trung bình",
                    title="Số tour của mỗi HDV so với trung bình", text="Số tour đã làm")
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Lịch nhắc nhở tour sắp tới")
    hdv_nhac = st.selectbox("Chọn hướng dẫn viên để xem lịch nhắc nhở", [x["ten"] for x in st.session_state.hdv_list])
    lich = lay_lich_nhac_nho(hdv_nhac)
    if not lich:
        st.info(f"Không có tour nào sắp tới trong 7 ngày tới cho {hdv_nhac}")
    else:
        st.success(f"Lịch tour sắp tới của {hdv_nhac}:")
        for ngay, tour in lich:
            st.write(f"- Ngày {ngay}: Tour {tour}")

    # Xuất file CSV
    if not st.session_state.phân_ca.empty:
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
        csv = convert_df(st.session_state.phân_ca)
        st.download_button(label="📥 Tải lịch phân ca CSV", data=csv, file_name="lich_phan_ca.csv", mime='text/csv')
