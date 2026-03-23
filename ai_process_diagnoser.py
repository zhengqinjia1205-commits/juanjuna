import json
import os
import math

class ProcessDiagnoser:
    def __init__(self, use_mock_ai=True):
        self.use_mock_ai = use_mock_ai
        
    def extract_process_data(self, text_input):
        """
        AI Module: Extracts structured data and current demand metrics.
        """
        if self.use_mock_ai:
            print("🤖 AI正在解析文本描述并提取关键指标...")
            return {
                "process_name": "霸王茶姬门店业务流程 (高级版)",
                "total_arrival_rate": 70,  # 每小时总订单量 (λ)
                "online_order_ratio": 0.7, # 70% 的订单来自线上小程序
                "tea_batch_size": 10,      # 每桶茶汤可制作10杯
                "tea_extraction_time": 10, # 萃取一桶茶汤需要10分钟
                "steps": [
                    {"name": "点单与支付", "time_minutes": 1.0, "resources_count": 1, "is_affected_by_online": True},
                    {"name": "贴杯与备料", "time_minutes": 0.5, "resources_count": 1, "is_affected_by_online": False},
                    {"name": "萃茶与调饮", "time_minutes": 1.5, "resources_count": 2, "is_affected_by_online": False},
                    {"name": "封口与打包", "time_minutes": 1.0, "resources_count": 1, "is_affected_by_online": False},
                    {"name": "叫号取餐", "time_minutes": 0.2, "resources_count": 1, "is_affected_by_online": False}
                ]
            }
        else:
            pass

    def analyze_process(self, process_data):
        """
        Operations Management Module: Calculates capacity, utilization, and batching logic.
        """
        print("📊 正在执行运筹学计算 (包含线上分流与物料准备逻辑)...")
        steps = process_data["steps"]
        total_lambda = process_data["total_arrival_rate"]
        online_ratio = process_data["online_order_ratio"]
        
        min_capacity = float('inf')
        
        for step in steps:
            # 1. 计算实际负载 (Effective Demand)
            # 只有线下点单环节会被小程序分流减少工作量
            if step.get("is_affected_by_online", False):
                step["effective_demand"] = total_lambda * (1 - online_ratio)
            else:
                step["effective_demand"] = total_lambda
                
            # 2. 计算环节产能 (Capacity)
            step["hourly_capacity"] = (60 / step["time_minutes"]) * step["resources_count"]
            
            # 3. 计算利用率 (Utilization = Demand / Capacity)
            step["utilization"] = (step["effective_demand"] / step["hourly_capacity"]) * 100
            
            if step["hourly_capacity"] < min_capacity:
                min_capacity = step["hourly_capacity"]

        # 4. 茶叶萃取逻辑 (Batching Logic)
        # 频率 = 总需求 / 每桶产量
        process_data["tea_prep_frequency"] = total_lambda / process_data["tea_batch_size"]
        process_data["tea_prep_interval"] = 60 / process_data["tea_prep_frequency"] if process_data["tea_prep_frequency"] > 0 else 0
        
        process_data["process_capacity"] = min_capacity
        return process_data

    def generate_recommendations(self, data):
        print("💡 AI正在生成基于数据指标的优化建议...")
        recs = []
        
        # 找到利用率最高的环节
        sorted_steps = sorted(data["steps"], key=lambda x: x["utilization"], reverse=True)
        bottleneck = sorted_steps[0]
        
        recs.append(f"### 关键诊断结论")
        recs.append(f"- **系统瓶颈**: `{bottleneck['name']}`，当前利用率高达 `{bottleneck['utilization']:.1f}%`。")
        recs.append(f"- **线上占比**: 当前线上订单占比为 `{data['online_order_ratio']*100}%`。这显著减轻了`点单与支付`环节的压力。")
        
        recs.append(f"\n### 1. 人员排班建议 (Scheduling)")
        cashier_util = next(s["utilization"] for s in data["steps"] if s["name"] == "点单与支付")
        if cashier_util < 50:
            recs.append(f"- ⚠️ **人员冗余**: `点单与支付`利用率仅为 `{cashier_util:.1f}%`。由于 {data['online_order_ratio']*100}% 的顾客使用小程序，现场收银岗位有大量空闲。")
            recs.append(f"- ✅ **动态调度**: 建议将收银员岗位设为“柔性岗”。当线上订单激增时，该员工应立即支援`封口打包`或`调饮`环节。")
        else:
            recs.append(f"- ✅ **收银岗位平衡**: 当前线下点单压力尚可，建议维持现有配置。")
        
        recs.append(f"\n### 2. 物料准备逻辑 (Tea Preparation)")
        recs.append(f"- **按需萃取 (JIT)**: 基于当前每小时 `{data['total_arrival_rate']}` 杯的需求，系统计算出每 `{data['tea_prep_interval']:.1f}` 分钟需要消耗一桶茶汤。")
        recs.append(f"- **批量策略**: 建议每隔 8 分钟开启一轮新的萃取流程，以确保茶汤的新鲜度并防止供应断档。")
        recs.append(f"- **库存缓冲**: 建议维持 `{math.ceil(data['total_arrival_rate']/60 * data['tea_extraction_time'] / data['tea_batch_size'])}` 桶的茶汤库存作为安全缓冲，以应对需求波动。")

        return "\n".join(recs)

    def generate_report(self, input_file, output_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
            
        raw_data = self.extract_process_data(text)
        data = self.analyze_process(raw_data)
        recs = self.generate_recommendations(data)
        
        # Build Report
        report = f"# 📊 霸王茶姬运营深度诊断报告\n\n"
        report += "## 🚀 运营仪表盘 (Operations Dashboard)\n"
        report += f"| 指标名称 | 当前数值 | 备注 |\n"
        report += f"|---|---|---|\n"
        report += f"| **总到达率 (λ)** | {data['total_arrival_rate']} 杯/小时 | 门店整体繁忙度 |\n"
        report += f"| **小程序订单占比** | {data['online_order_ratio']*100}% | 数字化分流程度 |\n"
        report += f"| **系统最大产能** | {data['process_capacity']} 杯/小时 | 受限于最慢环节 |\n"
        report += f"| **茶汤萃取频率** | 每 {data['tea_prep_interval']:.1f} 分钟/桶 | 备茶节奏建议 |\n\n"
        
        report += "## 🔍 环节负载与利用率分析\n"
        report += "| 步骤名称 | 实际需求 (杯/小时) | 环节产能 | 利用率 (%) | 状态 |\n"
        report += "|---|---|---|---|---|\n"
        for s in data["steps"]:
            status = "🔴 超负荷" if s["utilization"] > 100 else ("🟡 压力大" if s["utilization"] > 80 else "✅ 正常")
            report += f"| {s['name']} | {s['effective_demand']:.1f} | {s['hourly_capacity']:.1f} | {s['utilization']:.1f}% | {status} |\n"
            
        report += "\n" + recs + "\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # --- Terminal Summary Output ---
        print("\n" + "="*50)
        print("🎯 最终诊断摘要 (Final Diagnosis Summary)")
        print("="*50)
        print(f"1. 核心瓶颈: {next(s['name'] for s in data['steps'] if s['utilization'] > 100)} (利用率: {max(s['utilization'] for s in data['steps']):.1f}%)")
        print(f"2. 备茶建议: 每 {data['tea_prep_interval']:.1f} 分钟萃取一桶茶汤")
        print(f"3. 人员调度: 建议将利用率仅为 {next(s['utilization'] for s in data['steps'] if s['name'] == '点单与支付'):.1f}% 的收银员转为柔性岗支援后端")
        print("="*50)
        print(f"✅ 详细报告已生成至: {output_file}")
        print("💡 提示: 你可以使用 IDE 预览 (Markdown Preview) 查看图表化的报告。")
        print("="*50 + "\n")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, "chagee_case.txt")
    output_file = os.path.join(base_dir, "diagnosis_report_v2.md")
    
    diagnoser = ProcessDiagnoser()
    diagnoser.generate_report(input_file, output_file)
