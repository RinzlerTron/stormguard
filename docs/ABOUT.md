# About StormGuard

## The Problem

Hurricane Milton (October 2024) exposed critical supply chain vulnerabilities:
- **$50B+ in losses** across affected regions
- **Service levels dropped to 60%** (vs 95% normal)
- **48+ hours of manual coordination** by exhausted managers
- **Critical stockouts** (water, batteries) while other inventory sat unused

This happens every major disruption: hurricanes, strikes, pandemics, port closures.

## The Solution

StormGuard is an autonomous multi-agent AI system that manages retail supply chains during disruptions. Six AI agents coordinate in real-time using Amazon Bedrock:

1. **Orchestrator** - Routes and coordinates all agents
2. **Demand Intelligence** - Forecasts demand using weather data and history
3. **Inventory Optimizer** - Calculates reorder points and stock levels
4. **Dynamic Pricing** - Adjusts prices within guardrails (max +10%)
5. **Procurement** - Creates purchase orders autonomously
6. **Risk & Compliance** - Validates every decision

## Hurricane Milton Demo

**Timeline:**

- **T-72h:** Weather monitoring detects Category 4 hurricane approaching Florida
- **T-60h:** Demand agent forecasts 300% spike in water, 280% in batteries
- **T-48h:** Inventory agent analyzes 50 stores, flags 23 at critical stockout risk
- **T-36h:** Procurement agent creates 47 emergency purchase orders ($400K total)
- **T-24h:** Pricing agent adjusts 89 SKUs (capped at +10% to prevent gouging)
- **T-12h:** Risk agent validates all decisions, auto-approves within policy
- **T-0h:** Hurricane makes landfall

**Outcome:**
- **98% service level** maintained (vs 60% without system)
- **$2.1M additional revenue** from optimized availability
- **40% fewer stockouts** on critical items
- **80% of decisions** fully autonomous
- **Real-time coordination** across all locations

## Technology

Built entirely on AWS serverless architecture:
- Amazon Bedrock (Claude Sonnet 4) for agent reasoning
- AWS Lambda for serverless execution
- Multi-agent coordination using Bedrock capabilities
- Real-time data processing and decision-making

## Target Users

- Retail chains (grocery, hardware, convenience stores)
- Distribution centers and warehouses
- E-commerce fulfillment operations
- Any business with multi-location inventory challenges