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

# Khởi tạo dữ liệu lưu trữ trong session state
if "hdv_list" not in st.session_state:
    st.session_state.hdv_list = [
        {"id": 1, "ten": "Nguyễn Văn A", "chuyen_mon": "Trong nước", "so_ngay_nghi": 4, "ngay_nghi": []},
        {"id": 2, "ten": "Trần Thị B", "chuyen_mon": "Quốc tế", "so_ngay_nghi": 4, "ngay_nghi": []},
        {"id": 3, "ten": "Lê Văn C", "chuyen_mon": "Trekking", "so_ngay_nghi": 4, "ngay_nghi": []},
    ]

if "lich_trinh_list" not in st.session_state:
    st.session_state.lich_trinh_list = []

if "phân_ca" not in st.session_state:
    st.session_state.phân_ca = pd.DataFrame(columns=["Ngày", "Hướng dẫn viên", "Chuyên môn", "Tour", "Loại tour", "Chi tiết"])

# Hàm tiện ích
def lay_danh_sach_ngay(tuan=None):
    today = datetime.today().date()
    if tuan:
        start = today - timedelta(days=today.weekday()) + timedelta(weeks=tuan-1)
    else:
        start = today - timedelta(days=today.weekday())
    return [start + timedelta(days=i) for i in range(7)]

def kiem_tra_xung_dot(hdv, ngay_moi):
    if st.session_state.phân_ca.empty:
        return False
    ca_cua_hdv = st.session_state.phân_ca[st.session_state.phân_ca["Hướng dẫn viên"] == hdv]
    return ngay_moi.strftime("%d/%m/%Y") in ca_cua_hdv["Ngày"].values

def them_ngay_nghi(hdv_id, ngay_nghi):
    hdv = next(x for x in st.session_state.hdv_list if x["id"] == hdv_id)
    ngay_str = ngay_nghi.strftime("%d/%m/%Y")
    if ngay_str not in hdv["ngay_nghi"]:
        hdv["ngay_nghi"].append(ngay_str)
        return True
    return False

def tinh_thong_ke_can_bang():
    if st.session_state.phân_ca.empty:
        return pd.DataFrame()
    thong_ke = st.session_state.phân_ca["Hướng dẫn viên"].value_counts().reset_index()
    thong_ke.columns = ["Hướng dẫn viên", "Số tour đã làm"]
    trung_binh = thong_ke["Số tour đã làm"].mean()
    thong_ke["Chênh lệch so với trung bình"] = thong_ke["Số tour đã làm"] - trung_binh
    return thong_ke

def lay_lich_nhac_nho(hdv_ten):
    if st.session_state.phân_ca.empty:
        return []
    ngay_hien_tai = datetime.today().date()
    lich = st.session_state.phân_ca[
        (st.session_state.phân_ca["Hướng dẫn viên"] == hdv_ten) &
        (pd.to_datetime(st.session_state.phân_ca["Ngày"], format="%d/%m/%Y").dt.date >= ngay_hien_tai) &
        (pd.to_datetime(st.session_state.phân_ca["Ngày"], format="%d/%m/%Y").dt.date <= ngay_hien_tai + timedelta(days=7))
    ]
    return lich[["Ngày", "Tour", "Chi tiết"]].values.tolist()

# --- Cải thiện giao diện các tab ---

# Sidebar
with st.sidebar:
    st.header("⚙️ Quản lý dữ liệu")

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
    st.subheader("Chi tiết các lịch tour")
    # Hiển thị thông tin chi tiết hơn về các tour
    if not st.session_state.lich_trinh_list:
        st.info("Chưa có lịch tour nào được thêm. Vui lòng thêm tour ở mục 'Thêm lịch tour mới' trong Sidebar.")
    else:
        # Thêm form để người dùng nhập thông tin tour
        with st.form("form_them_lich_tour", clear_on_submit=True):
            ten_tour = st.text_input("Tên tour")
            ngay_khoi_hanh = st.date_input("Ngày khởi hành")
            loai_tour = st.selectbox("Loại tour", ["Trong nước", "Quốc tế", "Trekking", "Đường dài"])
            so_luong_hdv_can = st.number_input("Số lượng HDV cần phân", min_value=1, value=1)
            mo_ta_tour = st.text_area("Mô tả chi tiết tour (điểm đến, hoạt động chính, yêu cầu đặc biệt...)")
            submitted = st.form_submit_button("Thêm tour vào danh sách")
            if submitted:
                new_id = max([x["id"] for x in st.session_state.lich_trinh_list], default=0) + 1
                st.session_state.lich_trinh_list.append({
                    "id": new_id,
                    "ten_tour": ten_tour,
                    "ngay_khoi_hanh": ngay_khoi_hanh,
                    "loai_tour": loai_tour,
                    "so_luong_hdv_can": so_luong_hdv_can,
                    "mo_ta_tour": mo_ta_tour,
                    "hdv_phan_ca": [] # Khởi tạo danh sách HDV đã phân ca cho tour này
                })
                st.success(f"Đã thêm tour '{ten_tour}' thành công!")

        st.subheader("Danh sách các tour đã thêm")
        df_tour = pd.DataFrame(st.session_state.lich_trinh_list)
        df_tour["ngay_khoi_hanh"] = df_tour["ngay_khoi_hanh"].apply(lambda x: x.strftime("%d/%m/%Y"))
        # Hiển thị chi tiết hơn
        st.dataframe(df_tour[["ten_tour", "ngay_khoi_hanh", "loai_tour", "so_luong_hdv_can", "mo_ta_tour"]], use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Quản lý xếp ca")
    # Phần xếp ca tự động
    st.markdown("### Xếp ca tự động")
    tuan_chon = st.selectbox("Chọn tuần để xếp ca", [f"Tuần {i}" for i in range(1, 6)])
    ngay_trong_tuan = lay_danh_sach_ngay(int(tuan_chon.split()[-1]))

    if st.button("Bắt đầu xếp ca tự động", type="primary"):
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
                    if kiem_tra_xung_dot(hdv_chon["ten"], ngay_tour):
                        xung_dot.append(f"HDV {hdv_chon['ten']} trùng lịch với tour khác vào ngày {ngay_tour.strftime('%d/%m/%Y')}")
                    else:
                        ds_phân_ca_moi.append({
                            "Ngày": ngay_tour.strftime("%d/%m/%Y"),
                            "Hướng dẫn viên": hdv_chon["ten"],
                            "Chuyên môn": hdv_chon["chuyen_mon"],
                            "Tour": tour["ten_tour"],
                            "Loại tour": tour["loai_tour"],
                            "Chi tiết": tour["mo_ta_tour"] # Thêm mô tả tour vào chi tiết phân ca
                        })

        if ds_phân_ca_moi:
            if st.session_state.phân_ca.empty:
                st.session_state.phân_ca = pd.DataFrame(ds_phân_ca_moi)
            else:
                st.session_state.phân_ca = pd.concat([st.session_state.phân_ca, pd.DataFrame(ds_phân_ca_moi)], ignore_index=True)
            st.success(f"Đã phân công tự động {len(ds_phân_ca_moi)} lượt cho tuần {tuan_chon}.")
            if xung_dot:
                st.warning("⚠️ Có các xung đột lịch đã được phát hiện:")
                for thong_bao in xung_dot:
                    st.write(f"- {thong_bao}")
        else:
            st.warning("Không có tour nào trong tuần này hoặc không đủ HDV phù hợp để phân công.")

    # Phần xếp ca thủ công
    st.markdown("---") # Đường kẻ ngăn cách
    st.subheader("Xếp ca thủ công")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        hdv_list_ten = [x["ten"] for x in st.session_state.hdv_list]
        hdv_chon_thu_cong = st.selectbox("Chọn HDV", hdv_list_ten if hdv_list_ten else ["Chưa có HDV"])
    with col2:
        ngay_chon_thu_cong = st.date_input("Chọn ngày")
    with col3:
        tour_list_ten = [x["ten_tour"] for x in st.session_state.lich_trinh_list]
        tour_chon_thu_cong = st.selectbox("Chọn tour", tour_list_ten if tour_list_ten else ["Chưa có tour"])
    with col4:
        # Thêm ô nhập mô tả chi tiết cho ca thủ công
        chi_tiet_ca_thu_cong = st.text_input("Chi tiết công việc", placeholder="Ví dụ: Hỗ trợ HDV chính...")

    if st.button("Lưu phân công thủ công", type="secondary"):
        if kiem_tra_xung_dot(hdv_chon_thu_cong, ngay_chon_thu_cong):
            st.error("⚠️ HDV này đã được phân công ca khác vào ngày này!")
        else:
            hdv_info = next(x for x in st.session_state.hdv_list if x["ten"] == hdv_chon_thu_cong)
            tour_info = next(x for x in st.session_state.lich_trinh_list if x["ten_tour"] == tour_chon_thu_cong)
            new_row = pd.DataFrame([{
                "Ngày": ngay_chon_thu_cong.strftime("%d/%m/%Y"),
                "Hướng dẫn viên": hdv_chon_thu_cong,
                "Chuyên môn": hdv_info["chuyen_mon"],
                "Tour": tour_chon_thu_cong,
                "Loại tour": tour_info["loai_tour"],
                "Chi tiết": chi_tiet_ca_thu_cong if chi_tiet_ca_thu_cong else "Chưa có chi tiết" # Thêm chi tiết
            }])
            st.session_state.phân_ca = pd.concat([st.session_state.phân_ca, new_row], ignore_index=True)
            st.success("Đã lưu phân công thủ công thành công!")

with tab4:
    st.subheader("Thống kê và cân bằng công việc")
    thong_ke = tinh_thong_ke_can_bang()
    if st.session_state.phân_ca.empty:
        st.info("Chưa có dữ liệu phân ca để thống kê. Hãy thực hiện xếp ca để xem thông tin.")
    else:
        st.markdown("### Khối lượng công việc của Hướng dẫn viên")
        st.dataframe(thong_ke, use_container_width=True, hide_index=True)

        # Biểu đồ thống kê
        fig = px.bar(
            thong_ke,
            x="Hướng dẫn viên",
            y="Số tour đã làm",
            color="Chênh lệch so với trung bình",
            title="So sánh khối lượng công việc của Hướng dẫn viên",
            text="Số tour đã làm",
            labels={"Số tour đã làm": "Số tour đã thực hiện", "Chênh lệch so với trung bình": "So với trung bình"}
        )
        fig.update_layout(xaxis_title="Hướng dẫn viên", yaxis_title="Số tour đã thực hiện")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Tổng quan lịch sử phân ca")
        st.dataframe(st.session_state.phân_ca[["Ngày", "Hướng dẫn viên", "Tour", "Chi tiết"]], use_container_width=True, hide_index=True) # Hiển thị thêm cột "Chi tiết"

with tab5:
    st.subheader("Lịch nhắc nhở tour sắp tới")
    hdv_nhac_ten = st.selectbox("Chọn hướng dẫn viên để xem lịch nhắc nhở", [x["ten"] for x in st.session_state.hdv_list])
    lich = lay_lich_nhac_nho(hdv_nhac_ten)
    if not lich:
        st.info(f"Không có tour nào sắp tới trong 7 ngày tới cho {hdv_nhac_ten}.")
    else:
        st.success(f"Lịch tour sắp tới của {hdv_nhac_ten} (trong 7 ngày):")
        # Hiển thị chi tiết hơn
        df_nhac_nho = pd.DataFrame(lich, columns=["Ngày", "Tour", "Chi tiết"])
        st.dataframe(df_nhac_nho, use_container_width=True, hide_index=True)

    # Nút tải file CSV
    if not st.session_state.phân_ca.empty:
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
        csv = convert_df(st.session_state.phân_ca)
        st.download_button(label="📥 Tải toàn bộ lịch phân ca về file CSV", data=csv, file_name="lich_phan_ca_day_du.csv", mime='text/csv')

