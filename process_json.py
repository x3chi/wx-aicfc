import json
import numpy as np
import scipy.fft
from statsmodels.tsa.seasonal import seasonal_decompose

def classify_item(history):
    """
    根据数据点的结构和特点分类。
    """
    if not history:
        return "empty"
    
    # 判断是否为数值型时间序列数据
    if all(isinstance(dp, dict) and "time" in dp and "value" in dp for dp in history):
        try:
            # 尝试将文本值转化为数值，保留数值型的条目
            float(history[0]["value"])
            return "numeric_time_series"
        except ValueError:
            return "textual_time_series"
    
    return "unknown"

def process_numeric_time_series(history):
    """
    提炼数值型时间序列数据的特征。
    """
    values = np.array([float(entry["value"]) for entry in history])
    result = {}

    # 提炼统计摘要
    result["summary_stats"] = {
        "mean": float(round(np.mean(values), 2)),
        "min": float(round(np.min(values), 2)),
        "max": float(round(np.max(values), 2))
    }

    # 提炼趋势斜率
    x = np.arange(len(values))
    coeffs = np.polyfit(x, values, 1)
    result["trend_slope"] = float(round(coeffs[0], 6))

    # 提炼 FFT 主频率
    fft_vals = scipy.fft.rfft(values)
    fft_freqs = scipy.fft.rfftfreq(len(values), d=1)
    peak_idx = np.argmax(np.abs(fft_vals))
    result["fft_dominant_frequency"] = float(round(fft_freqs[peak_idx], 6))

    # 提炼季节性分解的趋势首尾值
    decomposition = seasonal_decompose(values, period=max(2, len(values) // 2), model='additive', extrapolate_trend="freq")
    trend = decomposition.trend
    result["trend_values"] = {
        "start": float(round(trend[0], 2)) if trend[0] is not np.nan else None,
        "end": float(round(trend[-1], 2)) if trend[-1] is not np.nan else None
    }

    # 提炼突变点总数
    diffs = np.diff(values)
    cusum = np.cumsum(diffs - np.mean(diffs))
    change_points = np.where(np.abs(cusum) > np.std(cusum))[0]
    result["change_points_total"] = int(len(change_points))

    # 提炼异常点总数
    mean = np.mean(values)
    std = np.std(values)
    threshold_upper = mean + 2 * std
    threshold_lower = mean - 2 * std
    anomalies = [val for val in values if val > threshold_upper or val < threshold_lower]
    result["anomalies_total"] = int(len(anomalies))

    return result

def process_textual_time_series(history):
    """
    提炼文本型数据，只保留出现频率最高的状态及其比例。
    """
    values = [entry["value"] for entry in history]
    unique_values, counts = np.unique(values, return_counts=True)
    total_states = sum(counts)
    dominant_state = unique_values[np.argmax(counts)]
    dominant_frequency = counts[np.argmax(counts)]

    return {
        "dominant_state": dominant_state,
        "frequency": int(dominant_frequency),
        "proportion": float(round(dominant_frequency / total_states, 2))
    }

def process_and_refine(input_file, output_file):
    """
    从原始 JSON 文件中提炼数据，并输出提炼后的 JSON 文件。
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    refined_results = {}

    for item in data.get("items", []):
        item_name = item.get("item_name", "未知项")
        history = item.get("history", [])
        category = classify_item(history)

        if category == "numeric_time_series":
            refined_results[item_name] = process_numeric_time_series(history)
        elif category == "textual_time_series":
            refined_results[item_name] = process_textual_time_series(history)
        else:
            # 忽略空值和未知数据
            continue

    # 将结果写入输出文件，确保所有 NumPy 数据类型转换为 Python 原生类型
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(refined_results, f, ensure_ascii=False, indent=4)

    print(f"数据已成功提炼并保存到 {output_file}")

if __name__ == "__main__":
    # 输入和输出文件路径
    input_file = input("请输入文件名：")  # 替换为原始 JSON 文件路径
    output_file = "refined_data.json"  # 替换为输出提炼后的 JSON 文件路径

    process_and_refine(input_file, output_file)
