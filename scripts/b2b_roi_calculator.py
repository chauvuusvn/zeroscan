#!/usr/bin/env python3
"""
B2B ROI & Token Cost Savings Calculator for Zero-Scan Cloud.
Calculates token burn reduction, financial savings, payback period, and net ROI for software teams.
"""

import argparse
import json
import sys

MODEL_PRICING_PER_1M = {
    "claude-3-5-sonnet": {"input": 3.00, "name": "Anthropic Claude 3.5 Sonnet"},
    "claude-3-opus": {"input": 15.00, "name": "Anthropic Claude 3 Opus"},
    "gpt-4o": {"input": 2.50, "name": "OpenAI GPT-4o"},
    "gpt-4o-mini": {"input": 0.15, "name": "OpenAI GPT-4o mini"},
    "gemini-1-5-pro": {"input": 1.25, "name": "Google Gemini 1.5 Pro"},
    "deepseek-v3": {"input": 0.14, "name": "DeepSeek-V3 / Coder"},
}


def calculate_roi(
    num_devs: int = 15,
    sessions_per_dev_day: int = 12,
    working_days: int = 22,
    model_key: str = "claude-3-5-sonnet",
    full_scan_tokens: int = 50000,
    zero_scan_tokens: int = 1000,
    saas_price_per_seat: float = 15.0,
) -> dict:
    pricing = MODEL_PRICING_PER_1M.get(model_key, MODEL_PRICING_PER_1M["claude-3-5-sonnet"])
    cost_per_1m = pricing["input"]

    total_sessions_month = num_devs * sessions_per_dev_day * working_days
    tokens_unoptimized = total_sessions_month * full_scan_tokens
    tokens_zeroscan = total_sessions_month * zero_scan_tokens
    tokens_saved = tokens_unoptimized - tokens_zeroscan

    cost_before = (tokens_unoptimized / 1_000_000) * cost_per_1m
    cost_after = (tokens_zeroscan / 1_000_000) * cost_per_1m
    gross_monthly_savings = cost_before - cost_after
    annual_gross_savings = gross_monthly_savings * 12

    saas_monthly_cost = num_devs * saas_price_per_seat
    saas_annual_cost = saas_monthly_cost * 12
    net_monthly_savings = gross_monthly_savings - saas_monthly_cost
    net_annual_savings = annual_gross_savings - saas_annual_cost

    roi_pct = (net_monthly_savings / saas_monthly_cost) * 100 if saas_monthly_cost > 0 else 0
    daily_savings = gross_monthly_savings / working_days if working_days > 0 else 1
    payback_days = saas_monthly_cost / daily_savings if daily_savings > 0 else 0

    return {
        "team_size": num_devs,
        "model_evaluated": pricing["name"],
        "rate_per_1m_tokens_usd": cost_per_1m,
        "monthly_sessions_count": total_sessions_month,
        "monthly_tokens_unoptimized_m": round(tokens_unoptimized / 1_000_000, 2),
        "monthly_tokens_zeroscan_m": round(tokens_zeroscan / 1_000_000, 2),
        "monthly_tokens_saved_m": round(tokens_saved / 1_000_000, 2),
        "reduction_percentage": round((tokens_saved / tokens_unoptimized) * 100, 1),
        "token_cost_before_usd": round(cost_before, 2),
        "token_cost_with_zeroscan_usd": round(cost_after, 2),
        "gross_monthly_savings_usd": round(gross_monthly_savings, 2),
        "gross_annual_savings_usd": round(annual_gross_savings, 2),
        "saas_investment_monthly_usd": round(saas_monthly_cost, 2),
        "net_monthly_profit_savings_usd": round(net_monthly_savings, 2),
        "net_annual_profit_savings_usd": round(net_annual_savings, 2),
        "roi_percentage": round(roi_pct, 1),
        "payback_period_days": round(payback_days, 1),
        "savings_per_engineer_month_usd": round(gross_monthly_savings / num_devs, 2),
    }


def print_report(res: dict) -> None:
    print("\n" + "=" * 65)
    print(" 🏛️  ZERO-SCAN CLOUD — B2B FINANCIAL ROI & COST SAVINGS REPORT")
    print("=" * 65)
    print(f" Team Size               : {res['team_size']} Software Engineers")
    print(f" Target Model            : {res['model_evaluated']} (${res['rate_per_1m_tokens_usd']}/1M tokens)")
    print(f" Monthly AI Sessions     : {res['monthly_sessions_count']:,} session starts / prompts")
    print("-" * 65)
    print(f" 🔴 Monthly Tokens (Unoptimized) : {res['monthly_tokens_unoptimized_m']} Million tokens")
    print(f" 🟢 Monthly Tokens (Zero-Scan)   : {res['monthly_tokens_zeroscan_m']} Million tokens")
    print(f" ⚡ Token Reduction              : {res['reduction_percentage']}% Saved ({res['monthly_tokens_saved_m']}M tokens)")
    print("-" * 65)
    print(f" 💸 Token Bill Before Zero-Scan  : ${res['token_cost_before_usd']:,.2f} / month")
    print(f" 💵 Token Bill With Zero-Scan    : ${res['token_cost_with_zeroscan_usd']:,.2f} / month")
    print(f" 💰 Gross Monthly Savings        : ${res['gross_monthly_savings_usd']:,.2f} / month")
    print(f" 🚀 Gross Annual Savings         : ${res['gross_annual_savings_usd']:,.2f} / year")
    print("-" * 65)
    print(f" 💳 Zero-Scan Team SaaS Cost     : ${res['saas_investment_monthly_usd']:,.2f} / month ($15/seat)")
    print(f" ✨ Net Profit Savings (After Sub): ${res['net_monthly_profit_savings_usd']:,.2f} / month")
    print(f" 📈 Net Return on Investment(ROI): {res['roi_percentage']}%")
    print(f" ⏱️  Payback Period               : {res['payback_period_days']} business days")
    print(f" 👤 Savings Per Engineer         : ${res['savings_per_engineer_month_usd']:,.2f} / engineer / month")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Zero-Scan B2B ROI & Token Savings Calculator")
    parser.add_argument("--devs", "-d", type=int, default=20, help="Number of software engineers (default: 20)")
    parser.add_argument("--sessions", "-s", type=int, default=12, help="AI sessions/resumes per engineer per day (default: 12)")
    parser.add_argument("--model", "-m", choices=list(MODEL_PRICING_PER_1M.keys()), default="claude-3-5-sonnet", help="Target LLM model")
    parser.add_argument("--price", "-p", type=float, default=15.0, help="Zero-Scan SaaS price per seat/month (default: 15.0)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    res = calculate_roi(
        num_devs=args.devs,
        sessions_per_dev_day=args.sessions,
        model_key=args.model,
        saas_price_per_seat=args.price,
    )

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print_report(res)


if __name__ == "__main__":
    main()
