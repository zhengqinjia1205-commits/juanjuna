import json
import os
import math

class ChageeBackendSimulator:
    def __init__(self):
        # 霸王茶姬门店固定配置 (Based on our Chagee case)
        self.config = {
            "steps": [
                {"name": "点单与支付", "time_minutes": 1.0, "resources_count": 1, "is_affected_by_online": True},
                {"name": "贴杯与备料", "time_minutes": 0.5, "resources_count": 1, "is_affected_by_online": False},
                {"name": "萃茶与调饮", "time_minutes": 1.5, "resources_count": 2, "is_affected_by_online": False},
                {"name": "封口与打包", "time_minutes": 1.0, "resources_count": 1, "is_affected_by_online": False},
                {"name": "叫号取餐", "time_minutes": 0.2, "resources_count": 1, "is_affected_by_online": False}
            ],
            "tea_batch_size": 10,
            "tea_extraction_time": 10
        }

    def calculate_wait_time(self, online_queue, offline_queue):
        """
        Using Queueing Theory logic (Little's Law variation):
        Wait Time = Total Queue / System Bottleneck Capacity
        """
        total_orders = online_queue + offline_queue
        
        # 1. 寻找系统整体产能 (Bottleneck Capacity)
        # 霸王茶姬这类流水线，系统整体产能由最慢环节决定
        capacities = []
        for step in self.config["steps"]:
            cap = (60 / step["time_minutes"]) * step["resources_count"]
            capacities.append(cap)
        
        system_capacity_per_hour = min(capacities) # 瓶颈产能 (杯/小时)
        system_capacity_per_minute = system_capacity_per_hour / 60
        
        # 2. 计算预计等待时间 (Wait Time in Minutes)
        if system_capacity_per_minute > 0:
            expected_wait = total_orders / system_capacity_per_minute
        else:
            expected_wait = 0
            
        return round(expected_wait, 1), system_capacity_per_hour

    def run_simulation(self):
        print("\n" + "="*60)
        print("🍵 霸王茶姬 (CHAGEE) 后台实时模拟器")
        print("="*60)
        
        try:
            # 模拟用户输入实时数据
            online_q = int(input(">>> 请输入当前【线上小程序】待制作杯数: "))
            offline_q = int(input(">>> 请输入当前【线下现场】待制作杯数: "))
            
            wait_time, capacity = self.calculate_wait_time(online_q, offline_q)
            
            print("\n" + "-"*60)
            print("📊 后台实时监测结果 (Backend Monitoring):")
            print(f"1. 实时排队总数: {online_q + offline_q} 杯 (线上: {online_q} / 线下: {offline_q})")
            print(f"2. 门店最大产能: {capacity:.1f} 杯/小时")
            print(f"3. 🚨 预计等待时间: {wait_time} 分钟")
            
            # 预警逻辑
            if wait_time > 45:
                print("\n⚠️  [系统预警]: 当前排队过长，建议小程序端显示“门店繁忙，暂停接单”。")
            elif wait_time > 20:
                print("\n💡 [调度建议]: 建议抽调收银员协助封口打包，提高系统瓶颈产能。")
            else:
                print("\n✅ [运行良好]: 门店负荷正常，请保持制作节奏。")
            
            # 茶叶制备逻辑
            tea_needed = math.ceil((online_q + offline_q) / self.config["tea_batch_size"])
            print(f"4. 🍃 备茶建议: 当前队列至少需要准备 {tea_needed} 桶新茶汤。")
            
            print("="*60 + "\n")
            
        except ValueError:
            print("❌ 输入错误: 请输入整数数字。")

if __name__ == "__main__":
    simulator = ChageeBackendSimulator()
    simulator.run_simulation()
