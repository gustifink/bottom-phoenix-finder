import asyncio
import sys
sys.path.append('.')

from services.dexscreener import DexscreenerService
from services.brs_calculator import BRSCalculator
from datetime import datetime
import json

async def generate_detailed_analysis():
    # OKCC token address
    token_address = "Av4dQxUK7nBfU4rSp9qfj3s8KEzT2crB9j15KXq7pump"
    
    service = DexscreenerService()
    calculator = BRSCalculator()
    
    try:
        # Get token data
        print("Fetching token data...")
        raw_data = await service.get_token_data(token_address)
        
        if not raw_data:
            print("Failed to fetch token data")
            return
        
        # Parse data
        parsed_data = service.parse_token_data(raw_data)
        
        # Calculate BRS score
        brs_analysis = calculator.calculate_brs(parsed_data)
        
        # Calculate token age
        token_age_days = 0
        if parsed_data.get("pair_created_at"):
            created_date = datetime.fromtimestamp(parsed_data["pair_created_at"] / 1000)
            token_age_days = (datetime.utcnow() - created_date).days
        
        # Generate comprehensive analysis
        analysis = {
            "token_identity": {
                "symbol": parsed_data["symbol"],
                "name": parsed_data["name"],
                "address": parsed_data["address"],
                "chain": "Solana",
                "dexscreener_url": parsed_data.get("url", f"https://dexscreener.com/solana/{token_address}"),
                "token_age_days": token_age_days,
                "first_seen": created_date.strftime("%Y-%m-%d %H:%M:%S UTC") if token_age_days > 0 else "Unknown"
            },
            
            "market_snapshot": {
                "current_price": f"${parsed_data['current_price']:.8f}",
                "market_cap": f"${parsed_data['market_cap']:,.0f}",
                "liquidity_usd": f"${parsed_data['liquidity_usd']:,.0f}",
                "volume_24h": f"${parsed_data['volume_24h']:,.0f}",
                "liquidity_to_mcap_ratio": f"{(parsed_data['liquidity_usd'] / parsed_data['market_cap'] * 100):.1f}%",
                "volume_to_mcap_ratio": f"{(parsed_data['volume_24h'] / parsed_data['market_cap'] * 100):.1f}%"
            },
            
            "price_action_analysis": {
                "24h_change": f"{parsed_data['price_change_24h']:.2f}%",
                "6h_change": f"{parsed_data['price_change_6h']:.2f}%", 
                "1h_change": f"{parsed_data['price_change_1h']:.2f}%",
                "5m_change": f"{parsed_data['price_change_5m']:.2f}%",
                "trend_analysis": analyze_trend(parsed_data)
            },
            
            "trading_activity": {
                "24h_transactions": {
                    "buys": parsed_data['buys_24h'],
                    "sells": parsed_data['sells_24h'],
                    "total": parsed_data['buys_24h'] + parsed_data['sells_24h'],
                    "buy_sell_ratio": f"{(parsed_data['buys_24h'] / parsed_data['sells_24h']):.2f}" if parsed_data['sells_24h'] > 0 else "∞"
                },
                "trading_sentiment": analyze_sentiment(parsed_data)
            },
            
            "brs_analysis": {
                "total_score": f"{brs_analysis['brs_score']:.1f}/100",
                "category": calculator.get_score_interpretation(brs_analysis['brs_score'])[0],
                "interpretation": calculator.get_score_interpretation(brs_analysis['brs_score'])[1],
                "component_scores": {
                    "holder_resilience": {
                        "score": f"{brs_analysis['holder_resilience_score']}/20",
                        "percentage": f"{(brs_analysis['holder_resilience_score'] / 20 * 100):.0f}%",
                        "key_metric": f"Buy/Sell Ratio: {brs_analysis['buy_sell_ratio']:.2f}"
                    },
                    "volume_floor": {
                        "score": f"{brs_analysis['volume_floor_score']}/20",
                        "percentage": f"{(brs_analysis['volume_floor_score'] / 20 * 100):.0f}%",
                        "key_metric": f"24h Volume: ${parsed_data['volume_24h']:,.0f}"
                    },
                    "price_recovery": {
                        "score": f"{brs_analysis['price_recovery_score']}/20",
                        "percentage": f"{(brs_analysis['price_recovery_score'] / 20 * 100):.0f}%",
                        "key_metric": f"Recent momentum: {parsed_data['price_change_1h']:.1f}% (1h)"
                    },
                    "distribution_health": {
                        "score": f"{brs_analysis['distribution_health_score']}/10",
                        "percentage": f"{(brs_analysis['distribution_health_score'] / 10 * 100):.0f}%",
                        "key_metric": f"Liquidity ratio: {(parsed_data['liquidity_usd'] / parsed_data['market_cap'] * 100):.1f}%"
                    },
                    "revival_momentum": {
                        "score": f"{brs_analysis['revival_momentum_score']}/15",
                        "percentage": f"{(brs_analysis['revival_momentum_score'] / 15 * 100):.0f}%",
                        "key_metric": f"Volume trend: {brs_analysis['volume_trend']}"
                    },
                    "smart_accumulation": {
                        "score": f"{brs_analysis['smart_accumulation_score']}/15",
                        "percentage": f"{(brs_analysis['smart_accumulation_score'] / 15 * 100):.0f}%",
                        "key_metric": f"Accumulation pattern: {analyze_accumulation(parsed_data)}"
                    }
                }
            },
            
            "phoenix_validation": {
                "meets_criteria": check_criteria(parsed_data),
                "key_strengths": identify_strengths(parsed_data, brs_analysis),
                "risk_factors": identify_risks(parsed_data, brs_analysis),
                "recovery_potential": assess_recovery_potential(parsed_data, brs_analysis)
            },
            
            "investment_thesis": generate_thesis(parsed_data, brs_analysis, token_age_days),
            
            "technical_recommendation": generate_recommendation(parsed_data, brs_analysis)
        }
        
        # Print the comprehensive analysis
        print("\n" + "="*80)
        print("COMPREHENSIVE PHOENIX TOKEN ANALYSIS")
        print("="*80)
        print(json.dumps(analysis, indent=2))
        
        # Save to file
        with open('token_analysis_report.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        print("\nAnalysis saved to token_analysis_report.json")
        
    finally:
        await service.close()

def analyze_trend(data):
    changes = [data['price_change_24h'], data['price_change_6h'], data['price_change_1h']]
    
    if all(c < -10 for c in changes):
        return "Strong downtrend - Capitulation phase"
    elif all(c < 0 for c in changes):
        return "Consistent decline - Testing support levels"
    elif data['price_change_1h'] > 0 and data['price_change_6h'] < 0:
        return "Early reversal signs - Potential bottom formation"
    elif data['price_change_1h'] > 0 and data['price_change_6h'] > 0:
        return "Recovery in progress - Buyers stepping in"
    else:
        return "Mixed signals - Consolidation phase"

def analyze_sentiment(data):
    ratio = data['buys_24h'] / data['sells_24h'] if data['sells_24h'] > 0 else float('inf')
    
    if ratio > 1.5:
        return "Very bullish - Strong accumulation"
    elif ratio > 1.2:
        return "Bullish - More buyers than sellers"
    elif ratio > 0.8:
        return "Neutral - Balanced trading"
    elif ratio > 0.5:
        return "Bearish - Distribution phase"
    else:
        return "Very bearish - Heavy selling pressure"

def analyze_accumulation(data):
    buys = data['buys_24h']
    sells = data['sells_24h']
    volume = data['volume_24h']
    
    if buys > sells * 1.5 and volume > 500000:
        return "Heavy accumulation"
    elif buys > sells:
        return "Net accumulation"
    elif buys < sells * 0.8:
        return "Net distribution"
    else:
        return "Balanced flow"

def check_criteria(data):
    criteria = []
    
    if data['price_change_24h'] < -70:
        criteria.append("✅ Severe crash (>70% drop)")
    elif data['price_change_24h'] < -30:
        criteria.append("✅ Significant crash (>30% drop)")
    else:
        criteria.append("⚠️ Moderate decline (<30% drop)")
    
    if data['volume_24h'] >= 50000:
        criteria.append("✅ Meets minimum volume requirement ($50k+)")
    
    if data['market_cap'] >= 500000:
        criteria.append("✅ Meets minimum market cap ($500k+)")
    elif data['market_cap'] >= 100000:
        criteria.append("⚠️ Below target market cap but tradeable")
    
    if data['liquidity_usd'] >= 20000:
        criteria.append("✅ Good liquidity for entry/exit")
    elif data['liquidity_usd'] >= 5000:
        criteria.append("⚠️ Limited liquidity - use small positions")
    
    return criteria

def identify_strengths(data, brs):
    strengths = []
    
    if data['volume_24h'] > data['market_cap']:
        strengths.append("📊 Exceptional volume relative to market cap")
    
    if brs['buy_sell_ratio'] > 1.2:
        strengths.append("💪 Strong buyer dominance")
    
    if data['liquidity_usd'] / data['market_cap'] > 0.3:
        strengths.append("💧 Deep liquidity pool")
    
    if data['price_change_1h'] > 0 and data['price_change_24h'] < -30:
        strengths.append("🔄 Early reversal pattern forming")
    
    if brs['brs_score'] > 70:
        strengths.append("🏆 High BRS score indicates strong phoenix potential")
    
    return strengths

def identify_risks(data, brs):
    risks = []
    
    if data['market_cap'] < 100000:
        risks.append("⚠️ Micro-cap - high volatility risk")
    
    if data['liquidity_usd'] < 10000:
        risks.append("⚠️ Low liquidity - slippage concerns")
    
    if data['price_change_24h'] < -50:
        risks.append("⚠️ Extreme decline - may continue falling")
    
    if brs['buy_sell_ratio'] < 0.8:
        risks.append("⚠️ More sellers than buyers currently")
    
    if data['liquidity_usd'] / data['market_cap'] < 0.1:
        risks.append("⚠️ Poor liquidity ratio - manipulation risk")
    
    return risks

def assess_recovery_potential(data, brs):
    score = 0
    factors = []
    
    # Volume analysis
    if data['volume_24h'] > data['market_cap'] * 2:
        score += 30
        factors.append("Exceptional volume indicates high interest")
    elif data['volume_24h'] > data['market_cap']:
        score += 20
        factors.append("Strong volume supports recovery")
    
    # Buy pressure
    if brs['buy_sell_ratio'] > 1.5:
        score += 25
        factors.append("Heavy accumulation pattern")
    elif brs['buy_sell_ratio'] > 1:
        score += 15
        factors.append("Net buying pressure")
    
    # Liquidity health
    liq_ratio = data['liquidity_usd'] / data['market_cap']
    if liq_ratio > 0.5:
        score += 20
        factors.append("Excellent liquidity depth")
    elif liq_ratio > 0.2:
        score += 10
        factors.append("Healthy liquidity")
    
    # Price action
    if data['price_change_1h'] > 5:
        score += 15
        factors.append("Strong short-term bounce")
    elif data['price_change_1h'] > 0:
        score += 10
        factors.append("Price stabilizing")
    
    # BRS score
    if brs['brs_score'] > 80:
        score += 20
        factors.append("Exceptional BRS metrics")
    elif brs['brs_score'] > 60:
        score += 10
        factors.append("Good BRS score")
    
    if score >= 80:
        return f"Very High ({score}/100) - {', '.join(factors[:3])}"
    elif score >= 60:
        return f"High ({score}/100) - {', '.join(factors[:2])}"
    elif score >= 40:
        return f"Moderate ({score}/100) - {', '.join(factors[:2])}"
    else:
        return f"Low ({score}/100) - Limited positive signals"

def generate_thesis(data, brs, age_days):
    thesis_parts = []
    
    # Opening
    thesis_parts.append(f"{data['symbol']} presents a potential phoenix opportunity after dropping {abs(data['price_change_24h']):.1f}% in 24 hours.")
    
    # Volume analysis
    vol_to_mc = data['volume_24h'] / data['market_cap'] * 100
    thesis_parts.append(f"The token shows remarkable trading activity with ${data['volume_24h']:,.0f} in 24h volume ({vol_to_mc:.0f}% of market cap), indicating sustained interest despite the price decline.")
    
    # Accumulation pattern
    if brs['buy_sell_ratio'] > 1:
        thesis_parts.append(f"Buy/sell ratio of {brs['buy_sell_ratio']:.2f} suggests smart money accumulation at these levels.")
    
    # Liquidity analysis
    liq_ratio = data['liquidity_usd'] / data['market_cap'] * 100
    thesis_parts.append(f"Liquidity of ${data['liquidity_usd']:,.0f} ({liq_ratio:.1f}% of market cap) provides adequate depth for position building.")
    
    # BRS interpretation
    category, interpretation = BRSCalculator().get_score_interpretation(brs['brs_score'])
    thesis_parts.append(f"BRS analysis rates this as '{category}' with score {brs['brs_score']:.1f}/100: {interpretation}")
    
    # Age consideration
    if age_days > 0:
        if age_days < 7:
            thesis_parts.append(f"Note: This is a very new token ({age_days} days old), which adds risk but also potential for explosive moves.")
        elif age_days < 30:
            thesis_parts.append(f"The token is {age_days} days old, still in price discovery phase.")
        else:
            thesis_parts.append(f"With {age_days} days of trading history, the token has established trading patterns.")
    
    return " ".join(thesis_parts)

def generate_recommendation(data, brs):
    score = brs['brs_score']
    
    if score >= 80:
        action = "STRONG BUY"
        position_size = "2-3% of portfolio"
        strategy = "Accumulate on dips, target 2-3x recovery"
    elif score >= 60:
        action = "BUY"
        position_size = "1-2% of portfolio"
        strategy = "Scale in gradually, monitor volume"
    elif score >= 40:
        action = "SPECULATIVE BUY"
        position_size = "0.5-1% of portfolio"
        strategy = "Small position only, tight stop loss"
    else:
        action = "WATCH"
        position_size = "No position yet"
        strategy = "Wait for clearer recovery signals"
    
    risk_management = []
    
    # Stop loss based on liquidity
    if data['liquidity_usd'] > 50000:
        risk_management.append("Stop loss: -20% from entry")
    else:
        risk_management.append("Stop loss: -15% from entry (tighter due to low liquidity)")
    
    # Take profit targets
    if data['price_change_24h'] < -70:
        risk_management.append("Target 1: +50% (partial exit)")
        risk_management.append("Target 2: +100% (reduce to house money)")
        risk_management.append("Target 3: +200%+ (moon bag)")
    else:
        risk_management.append("Target 1: +30% (partial exit)")
        risk_management.append("Target 2: +60% (reduce position)")
        risk_management.append("Target 3: +100%+ (final exit)")
    
    return {
        "action": action,
        "position_size": position_size,
        "strategy": strategy,
        "risk_management": risk_management,
        "time_horizon": "1-7 days for initial bounce, 2-4 weeks for full recovery"
    }

if __name__ == "__main__":
    asyncio.run(generate_detailed_analysis()) 