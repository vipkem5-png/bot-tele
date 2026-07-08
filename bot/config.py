import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
LINK4M_API_KEY = os.environ["LINK4M_API_KEY"]  # 64c9234dc40d5e17a54b4cbd

# Điểm thưởng per task
REWARD_SHORTEN = 50      # điểm khi tạo link rút gọn
REWARD_VISIT = 30        # điểm khi báo đã xem quảng cáo

# Tỉ lệ quy đổi: 1000 điểm = 10,000 VNĐ
POINTS_PER_VND = 100     # 100 điểm = 1,000 VNĐ
MIN_WITHDRAW = 5000      # điểm tối thiểu để rút
