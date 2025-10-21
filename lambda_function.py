"""StormGuard - Multi-Agent Supply Chain AI Demo for AWS AI Agent Global Hackathon 2025.

This Lambda function demonstrates autonomous AI agents coordinating supply chain decisions
during natural disasters using Amazon Bedrock (Claude Sonnet 3.5).

Architecture:
    - 6 specialized AI agents (Demand, Inventory, Procurement, Pricing, Risk, Orchestrator)
    - Real CSV data from S3 (sales history, stores, products, weather events)
    - Single-file serverless deployment via AWS Lambda Function URL
    - Embedded HTML/CSS/JS frontend with two modes:
        * Autonomous Operations: Visual demo of agent communication (no Bedrock calls)
        * Test Scenarios: Real Bedrock API calls with actual data processing

Competition Context:
    - Budget: $100 AWS credits (~3700 runs until Nov 15, 2025)
    - Cost per scenario run: ~$0.027 (6 Bedrock API calls)
    - Governance review threshold: $500K (only Hurricane Milton triggers human approval)

Author: Competition Entry
Model: Claude Sonnet 3.5 via Amazon Bedrock
"""

import os
import json
import boto3
import csv
import itertools
from io import StringIO
import traceback

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
S3_BUCKET = os.getenv("S3_BUCKET", "stormguard-deploy-bucket")

s3 = boto3.client('s3', region_name=REGION)

def get_csv_data(key, max_rows=None):
    """Read CSV data from S3 bucket with optional row limiting for performance.

    Reads CSV files from the configured S3 bucket and parses them into a list of
    dictionaries. Used to load sales history, store data, product catalogs, and
    weather event data for agent analysis.

    Args:
        key (str): S3 object key path (e.g., "data/sales_history.csv").
        max_rows (int, optional): Maximum number of rows to read. If None, reads
            all rows. Use for large files to control Lambda memory usage.

    Returns:
        list[dict]: List of dictionaries where each dict represents a CSV row
            with column headers as keys.

    Example:
        >>> sales = get_csv_data("data/sales_history.csv", max_rows=10000)
        >>> len(sales)
        10000
    """
    obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    content = obj['Body'].read().decode('utf-8')
    reader = csv.DictReader(StringIO(content))
    
    if max_rows:
        return list(itertools.islice(reader, max_rows))
    return list(reader)

def ask_bedrock(prompt):
    """Invoke Amazon Bedrock with Claude Sonnet 3.5 model for agent reasoning.

    Makes a synchronous API call to Amazon Bedrock to get AI-generated responses
    for supply chain decision-making. Each call costs approximately $0.0045 based
    on typical prompt/response sizes.

    Args:
        prompt (str): Formatted prompt string containing scenario context, data,
            and JSON response schema requirements.

    Returns:
        str: Raw JSON string response from Claude model containing agent decision
            data. Caller must parse this JSON.

    Raises:
        Exception: If Bedrock API call fails (throttling, permissions, invalid model).
            Includes full traceback for debugging.

    Example:
        >>> prompt = 'You are a demand forecasting agent. Respond with JSON: {...}'
        >>> response = ask_bedrock(prompt)
        >>> data = json.loads(response)
        >>> data['forecast_multiplier']
        3.5

    Cost Note:
        - Model: Claude Sonnet 3.5 (anthropic.claude-3-sonnet-20240229-v1:0)
        - Typical cost per call: $0.0045 (input + output tokens)
        - Budget: $100 = ~22,000 calls, but demo uses 6 calls per scenario run
    """
    try:
        bedrock = boto3.client("bedrock-runtime", region_name=REGION)
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            })
        )
        return json.loads(response["body"].read())["content"][0]["text"]
    except Exception as e:
        error_msg = "Bedrock Error: {}".format(str(e))
        print(error_msg)
        print(traceback.format_exc())
        raise Exception(error_msg)

def lambda_handler(event, context):
    """AWS Lambda handler for StormGuard multi-agent supply chain demo.

    This is the main entry point that handles both frontend HTML delivery and
    backend API calls for AI agent execution. Routes requests based on query
    parameters to either serve the UI or execute specific agent actions.

    Frontend Request (no action parameter):
        Returns embedded HTML/CSS/JS single-page application with two modes:
        - Autonomous Operations: Visual-only demo (hardcoded messages, no API calls)
        - Test Scenarios: Real Bedrock API calls with actual supply chain data

    Backend API Request (with action parameter):
        Executes specific AI agent and returns JSON response:
        - action=demand: Demand Intelligence Agent (forecast demand spike)
        - action=inventory: Inventory Optimization Agent (identify at-risk stores)
        - action=procurement: Procurement Agent (create emergency purchase orders)
        - action=pricing: Price Stability Agent (prevent price gouging)
        - action=risk: Risk & Compliance Agent (validate decisions, check thresholds)
        - action=orchestrator: Orchestrator Agent (synthesize final executive summary)

    Args:
        event (dict): Lambda event object from Function URL. Contains:
            - queryStringParameters: Dict with 'action' and 'scenario' keys.
        context (object): Lambda context object (unused but required by AWS).

    Returns:
        dict: Lambda response object with:
            - statusCode (int): HTTP status code (200 or 500).
            - headers (dict): CORS headers and content type.
            - body (str): For API calls, JSON string with agent results.
                         For UI requests, full HTML page.

    Scenario Types:
        - chris: Tropical Storm Chris ($300K budget, 15 stores, 2.2x spike)
        - uri: Winter Storm Uri ($400K budget, 18 stores, 2.8x spike)
        - milton: Hurricane Milton ($650K budget, 42 stores, 4.2x spike)

    Data Flow:
        1. Load CSV data from S3 (sales, stores, products, events)
        2. Calculate real statistics (baseline revenue, spike multiplier)
        3. Build agent-specific prompt with scenario context + real data
        4. Call Amazon Bedrock (Claude Sonnet 3.5) for reasoning
        5. Return JSON response to frontend for display

    Cost Analysis:
        - Frontend HTML delivery: Free (no Bedrock calls)
        - Autonomous mode: Free (visual-only, no API calls)
        - Test scenario run: ~$0.027 (6 Bedrock calls at $0.0045 each)
        - Budget allows ~3,700 test scenario runs before Nov 15, 2025

    Example:
        API call for demand forecast:
        >>> event = {'queryStringParameters': {'action': 'demand', 'scenario': 'milton'}}
        >>> response = lambda_handler(event, None)
        >>> json.loads(response['body'])['result']
        '{"forecast_multiplier": 4.2, "units_needed": 180000, ...}'

        UI delivery:
        >>> event = {'queryStringParameters': None}
        >>> response = lambda_handler(event, None)
        >>> '<html>' in response['body']
        True

    Note:
        Autonomous mode is purely visual demonstration - it does NOT call
        Bedrock or process real data. It uses hardcoded messages on a timer
        to simulate agent activity without incurring AWS costs.
    """
    try:
        query_params = event.get('queryStringParameters', {}) or {}
        action = query_params.get('action')
        scenario_type = query_params.get('scenario', 'milton')

        print("Action: {}, Scenario: {}".format(action, scenario_type))

        # Scenario configurations
        scenarios = {
            'chris': {
                'name': 'Tropical Storm Chris',
                'icon': '🌊',
                'spike': 2.2,
                'budget': 300000,
                'stores_at_risk': 15,
                'critical_products': 'water, batteries, tarps',
                'duration_days': 4
            },
            'uri': {
                'name': 'Winter Storm Uri',
                'icon': '❄️',
                'spike': 2.8,
                'budget': 400000,
                'stores_at_risk': 18,
                'critical_products': 'generators, heaters, blankets',
                'duration_days': 5
            },
            'milton': {
                'name': 'Hurricane Milton',
                'icon': '🌀',
                'spike': 4.2,
                'budget': 650000,
                'stores_at_risk': 42,
                'critical_products': 'water, food, medical supplies',
                'duration_days': 8
            }
        }

        scenario_config = scenarios.get(scenario_type, scenarios['chris'])
        
        # Load data from S3 (limit sales to 10K rows for performance)
        sales_data = get_csv_data("data/sales_history.csv", max_rows=10000)
        stores_data = get_csv_data("data/stores.csv")
        products_data = get_csv_data("data/products.csv")
        events_data = get_csv_data("data/known_events.csv")
        
        # Calculate stats from real data
        before_sales = [float(row.get('revenue', 0)) for row in sales_data[:len(sales_data)//2]]
        during_sales = [float(row.get('revenue', 0)) for row in sales_data[len(sales_data)//2:]]
        
        avg_before = sum(before_sales) / len(before_sales) if before_sales else 0
        avg_during = sum(during_sales) / len(during_sales) if during_sales else 0
        spike_multiplier = round(avg_during / avg_before, 2) if avg_before > 0 else 3.5
        
        scenario_data = {
            "sales_data": sales_data,
            "stores_data": stores_data,
            "products_data": products_data,
            "events_data": events_data,
            "stats": {
                "avg_before": round(avg_before, 0),
                "avg_during": round(avg_during, 0),
                "spike_multiplier": spike_multiplier,
                "num_stores": len(stores_data),
                "num_products": len(products_data)
            }
        }
        
        stats = scenario_data["stats"]
        
        if action == 'demand':
            prompt = """You are the Demand Intelligence Agent analyzing {}.

SCENARIO: {}
- Expected demand spike: {}x normal levels
- Critical products: {}
- Duration: {} days

DATA FROM S3:
- Sales records: {} rows analyzed
- Historical baseline: ${}/day average

Forecast demand surge. Respond with EXACT JSON:
{{
  "forecast_multiplier": <use scenario spike>,
  "units_needed": <calculate based on spike>,
  "confidence": "high/medium/low",
  "key_insight": "One clear sentence explaining what products will surge and why"
}}""".format(scenario_config['icon'], scenario_config['name'], scenario_config['spike'],
             scenario_config['critical_products'], scenario_config['duration_days'],
             len(sales_data), stats["avg_before"])
            
            result = ask_bedrock(prompt)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"result": result})
            }
        
        elif action == 'inventory':
            prompt = """You are the Inventory Optimization Agent for {}.

SCENARIO DATA:
- Stores at high risk: {} (from predictive model)
- Demand spike: {}x normal
- Critical SKUs: {}
- {} total stores, {} total products

Respond with EXACT JSON:
{{
  "at_risk_stores": <use scenario value {}>,
  "total_units_to_order": <large number based on spike>,
  "reorder_urgency": "critical/high/medium",
  "key_insight": "One clear sentence about which stores need emergency restocking"
}}""".format(scenario_config['name'], scenario_config['stores_at_risk'],
             scenario_config['spike'], scenario_config['critical_products'],
             stats["num_stores"], stats["num_products"], scenario_config['stores_at_risk'])
            
            result = ask_bedrock(prompt)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"result": result})
            }
        
        elif action == 'procurement':
            prompt = """You are the Procurement Agent for {}.

EMERGENCY SITUATION:
- {} stores need immediate restocking
- {}x demand spike for: {}
- Emergency budget approved: ${:,}
- Delivery needed in {} days

Create emergency purchase orders. Respond with EXACT JSON:
{{
  "purchase_orders": <number between 40-80>,
  "total_value_usd": <use scenario budget {}>,
  "vendors_engaged": <number 3-8>,
  "delivery_timeline_hours": <based on duration>,
  "key_insight": "One sentence about emergency procurement strategy"
}}""".format(scenario_config['name'], scenario_config['stores_at_risk'],
             scenario_config['spike'], scenario_config['critical_products'],
             scenario_config['budget'], scenario_config['duration_days'],
             scenario_config['budget'])
            
            result = ask_bedrock(prompt)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"result": result})
            }
        
        elif action == 'pricing':
            prompt = """You are the Price Stability & Anti-Gouging Agent for {}.

MISSION: PREVENT price increases during crisis to protect customers and brand reputation.

CONTEXT:
- Demand spike: {}x normal levels
- Competitor monitoring: Active
- Company policy: MAINTAIN or REDUCE prices on essentials during disasters
- Anti-gouging laws: Strictly enforced in all operating states

ACTIONS TAKEN:
- Monitoring internal systems for unauthorized price increases
- Flagging competitor price gouging for regulatory reporting
- Recommending stable pricing on critical items (water, batteries, etc.)
- Protecting brand reputation and customer loyalty

Respond with EXACT JSON:
{{
  "price_adjustment_pct": 0,
  "price_stability_maintained": true,
  "competitor_gouging_flagged": <number 2-8>,
  "brand_protection_value_usd": <number 50000-200000>,
  "key_insight": "One sentence about maintaining ethical pricing and preventing gouging"
}}""".format(scenario_config['name'], scenario_config['spike'])
            
            result = ask_bedrock(prompt)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"result": result})
            }
        
        elif action == 'risk':
            budget = scenario_config['budget']
            threshold = 500000
            approval = "auto_approved" if budget <= threshold else "governance_review"
            prompt = """You are the Risk & Compliance Agent for {}.

DECISION VALIDATION:
- Procurement spend: ${:,}
- Auto-approval threshold: ${:,}
- Price increase policy: max +10%
- Anti-gouging compliance: REQUIRED

IMPORTANT: If spend >${:,}, approval_status MUST be "governance_review", otherwise "auto_approved"

Respond with EXACT JSON:
{{
  "approval_status": "{}",
  "financial_risk": "{}",
  "compliance_score": <7-10>,
  "flagged_issues": {},
  "key_insight": "One sentence about approval decision"
}}""".format(scenario_config['name'], budget, threshold, threshold, approval,
             "high" if budget > threshold else "low",
             '["Spend exceeds ${:,} - requires executive approval"]'.format(threshold) if budget > threshold else '[]')
            
            result = ask_bedrock(prompt)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"result": result})
            }
        
        elif action == 'orchestrator':
            prompt = """You are the Orchestrator Agent coordinating response to {}.

SCENARIO SUMMARY:
- Event: {}
- Demand spike: {}x normal levels
- Stores at risk: {} of {}
- Emergency budget: ${:,}
- Critical products: {}
- Duration: {} days
- All 5 specialist agents completed analysis

Calculate business impact. Respond with EXACT JSON:
{{
  "service_level_pct": <90-99 realistic>,
  "revenue_protected_millions": <number between 2.0-8.0 based on spike and duration>,
  "automation_level_pct": <realistic % of decisions that were auto-approved, if budget<500K then 85-95, if budget>500K then 60-75>,
  "stores_prevented_stockout": <use exact value {}>,
  "executive_summary": "2-3 clear sentences explaining AI coordination results and business impact"
}}""".format(scenario_config['icon'], scenario_config['name'], scenario_config['spike'],
             scenario_config['stores_at_risk'], stats["num_stores"],
             scenario_config['budget'], scenario_config['critical_products'],
             scenario_config['duration_days'], scenario_config['stores_at_risk'])
            
            result = ask_bedrock(prompt)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"result": result})
            }
        
        html = generate_html(scenario_data)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": html
        }
        
    except Exception as e:
        error_detail = str(e)
        stack_trace = traceback.format_exc()
        print("ERROR: {}".format(error_detail))
        print(stack_trace)
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": error_detail,
                "trace": stack_trace
            })
        }

def generate_html(scenario_data):
    stats = scenario_data["stats"]

    return """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>StormGuard - Multi-Agent Supply Chain AI</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;padding:20px;background:#232F3E;color:white;line-height:1.6}}
.header{{text-align:center;margin-bottom:15px}}
.header h1{{font-size:2.2em;margin-bottom:8px}}
.aws-badge{{background:#FF9900;color:#232F3E;padding:8px 18px;border-radius:6px;display:inline-block;font-size:13px;font-weight:bold;margin:5px 0}}
.hero-impact{{background:linear-gradient(135deg,#1a472a,#0d2818);padding:30px;border-radius:12px;margin:20px 0;border:3px solid #4CAF50;text-align:center}}
.hero-title{{font-size:1.4em;color:#4CAF50;margin-bottom:20px;font-weight:bold}}
.hero-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:20px;margin-top:15px}}
.hero-card{{background:rgba(76,175,80,0.1);padding:20px;border-radius:8px;border:2px solid #4CAF50}}
.hero-value{{font-size:2.5em;color:#4CAF50;font-weight:bold;margin-bottom:5px}}
.hero-label{{color:#AAB7B8;font-size:0.95em}}
.hero-context{{color:#888;font-size:0.8em;margin-top:5px;font-style:italic}}
.mode-toggle{{display:flex;justify-content:center;gap:15px;margin:20px 0}}
.mode-btn{{background:linear-gradient(135deg,#37475A,#2d3a48);color:white;border:2px solid #4A90E2;padding:15px 35px;border-radius:10px;cursor:pointer;font-size:1.1em;font-weight:bold;transition:all 0.3s;box-shadow:0 2px 10px rgba(0,0,0,0.3)}}
.mode-btn.active{{background:linear-gradient(135deg,#4A90E2,#357ABD);border-color:#4CAF50;box-shadow:0 4px 15px rgba(74,144,226,0.5)}}
.mode-btn:hover{{transform:translateY(-2px);box-shadow:0 4px 15px rgba(74,144,226,0.3)}}
.autonomous-container{{display:none}}
.autonomous-container.active{{display:grid;grid-template-columns:60fr 40fr;gap:20px;margin:20px 0}}
.activity-log{{background:linear-gradient(135deg,#1a1a1a,#0d0d0d);padding:20px;border-radius:10px;border:2px solid #4A90E2;max-height:600px;overflow-y:auto}}
.activity-log-title{{font-size:1.2em;color:#4A90E2;margin-bottom:15px;font-weight:bold}}
.activity-entry{{padding:10px 14px;margin:5px 0;background:#232F3E;border-left:3px solid #4A90E2;border-radius:4px;font-family:monospace;font-size:1.05em;animation:slideIn 0.3s ease}}
.activity-entry.demand{{border-left-color:#E91E63}}
.activity-entry.inventory{{border-left-color:#9C27B0}}
.activity-entry.procurement{{border-left-color:#FF9800}}
.activity-entry.pricing{{border-left-color:#4CAF50}}
.activity-entry.risk{{border-left-color:#F44336}}
.activity-entry.orchestrator{{border-left-color:#FF9900}}
.activity-timestamp{{color:#FF9900;margin-right:10px;font-weight:bold;font-size:1.0em}}
.activity-agent{{color:#4A90E2;font-weight:bold;margin-right:10px;font-size:1.25em}}
.activity-message{{color:#ddd;font-size:1.0em}}
.flow-diagram{{background:linear-gradient(135deg,#1a1a1a,#0d0d0d);padding:20px;border-radius:10px;border:2px solid #4CAF50;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.flow-title{{font-size:1.2em;color:#4CAF50;margin-bottom:20px;font-weight:bold}}
.flow-svg{{width:100%;max-width:400px}}
.agent-node{{transition:all 0.3s}}
.agent-node.active{{animation:pulse 1.5s ease-in-out infinite}}
.agent-edge{{transition:all 0.3s;opacity:0.3}}
.agent-edge.active{{opacity:1;animation:glow 1s ease-in-out}}
@keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.1)}}}}
@keyframes glow{{0%{{stroke-width:2;opacity:0.3}}50%{{stroke-width:4;opacity:1}}100%{{stroke-width:2;opacity:0.3}}}}
@keyframes slideIn{{from{{opacity:0;transform:translateX(-20px)}}to{{opacity:1;transform:translateX(0)}}}}
.scenario-container{{display:flex;justify-content:center;gap:10px;margin:15px 0;flex-wrap:wrap}}
.scenario-container.hidden{{display:none}}
.scenario-btn{{background:#37475A;color:white;border:2px solid #FF9900;padding:10px 20px;border-radius:8px;cursor:pointer;font-size:0.95em;font-weight:bold;transition:all 0.3s}}
.scenario-btn.active{{background:#FF9900;color:#232F3E}}
.scenario-btn:hover{{background:#FF7700;color:#232F3E;transform:translateY(-2px)}}
.start-button{{background:linear-gradient(135deg,#FF9900,#FF7700);color:#232F3E;border:none;padding:18px 50px;font-size:1.3em;font-weight:bold;border-radius:10px;cursor:pointer;transition:all 0.3s;box-shadow:0 4px 15px rgba(255,153,0,0.4);margin:15px 0}}
.start-button:hover{{background:linear-gradient(135deg,#FF7700,#FF6600);transform:translateY(-2px);box-shadow:0 6px 20px rgba(255,153,0,0.6)}}
.start-button:disabled{{background:#37475A;cursor:not-allowed;opacity:0.6;transform:none}}
.progress-bar{{background:#1a1a1a;height:6px;border-radius:3px;margin:15px 0;overflow:hidden;display:none}}
.progress-fill{{background:linear-gradient(90deg,#FF9900,#FF7700);height:100%;width:0;transition:width 0.5s ease}}
.agents-grid{{display:none;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:15px;margin:20px 0}}
.agent-card{{background:linear-gradient(135deg,#37475A,#2d3a48);padding:18px;border-radius:10px;border:2px solid #1a1a1a;transition:all 0.3s;opacity:0.5}}
.agent-card.active{{opacity:1;border-color:#FF9900;box-shadow:0 4px 15px rgba(255,153,0,0.3)}}
.agent-card.complete{{opacity:1;border-color:#4CAF50}}
.agent-card:hover{{transform:translateY(-2px)}}
.agent-header{{display:flex;align-items:center;margin-bottom:10px}}
.agent-icon{{font-size:1.8em;margin-right:10px}}
.agent-title{{font-size:1.05em;font-weight:bold;color:#FF9900}}
.agent-status{{font-size:0.85em;color:#AAB7B8;margin-top:3px}}
.agent-input{{background:rgba(74,144,226,0.1);padding:10px;border-radius:6px;margin-top:10px;border-left:4px solid #4A90E2;display:none;font-size:0.85em;line-height:1.4}}
.agent-input.show{{display:block}}
.agent-input strong{{color:#4A90E2}}
.agent-insight{{background:#1a1a1a;padding:12px;border-radius:6px;margin-top:10px;border-left:4px solid #FF9900;display:none;font-size:0.9em;line-height:1.5}}
.agent-insight.show{{display:block}}
.agent-insight strong{{color:#FF9900}}
.agent-metrics{{display:none;margin-top:12px;padding-top:12px;border-top:1px solid #37475A}}
.agent-metrics.show{{display:block}}
.metric-row{{display:flex;justify-content:space-between;margin:6px 0;font-size:0.9em}}
.metric-label{{color:#AAB7B8}}
.metric-value{{color:#4CAF50;font-weight:bold}}
.metric-context{{color:#888;font-size:0.85em;margin-left:5px}}
.approval-badge{{background:#FF9900;color:#232F3E;padding:4px 10px;border-radius:4px;font-size:0.85em;font-weight:bold;display:inline-block;margin-top:8px}}
.approval-badge.auto{{background:#4CAF50}}
.approval-badge.governance{{background:#4A90E2;color:white}}
.final-results{{display:none;background:linear-gradient(135deg,#1a472a,#0d2818);padding:35px;border-radius:12px;margin:25px 0;border:3px solid #4CAF50}}
.final-results.show{{display:block}}
.final-title{{font-size:1.8em;color:#4CAF50;margin-bottom:15px;text-align:center}}
.final-summary{{background:rgba(76,175,80,0.1);padding:20px;border-radius:8px;margin-bottom:20px;border:2px solid #4CAF50}}
.final-summary h3{{color:#4CAF50;margin-bottom:10px}}
.final-summary p{{line-height:1.6;color:#ddd;font-size:0.95em}}
.impact-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-top:20px}}
.impact-card{{background:rgba(76,175,80,0.1);padding:20px;border-radius:10px;text-align:center;border:2px solid #4CAF50}}
.impact-value{{font-size:2.2em;color:#4CAF50;font-weight:bold;margin-bottom:5px}}
.impact-label{{color:#AAB7B8;font-size:0.9em}}
.impact-details{{color:#888;font-size:0.8em;margin-top:8px}}
.cost-badge{{position:fixed;top:15px;right:15px;background:#1a1a1a;padding:10px 18px;border-radius:6px;border:1px solid #FF9900;font-size:0.9em;z-index:1000;display:none}}
.cost-badge-value{{color:#FF9900;font-weight:bold;font-size:1.1em}}
.scale-badge{{position:fixed;top:70px;right:15px;background:#1a1a1a;padding:12px 18px;border-radius:6px;border:1px solid #4CAF50;font-size:0.9em;z-index:1000;line-height:1.8}}
.scale-badge-label{{color:#AAB7B8;font-size:0.9em}}
.scale-badge-value{{color:#4CAF50;font-weight:bold;margin-left:5px;font-size:1.05em}}
.run-log{{background:linear-gradient(135deg,#37475A,#2d3a48);padding:15px 20px;border-radius:8px;margin:15px 0;border:2px solid #FF9900;font-family:monospace;font-size:0.85em}}
.run-log-entry{{padding:5px 0;border-bottom:1px solid #37475A}}
.run-log-entry:last-child{{border-bottom:none}}
.run-log-time{{color:#FF9900;margin-right:10px}}
.run-log-scenario{{color:#4CAF50;font-weight:bold}}
.run-log-risk{{color:#888;margin-left:10px}}
.run-log-risk.auto{{color:#4CAF50}}
.run-log-risk.governance{{color:#4A90E2;font-weight:bold}}
.run-log-risk.rejected{{color:#F44336;font-weight:bold}}
.approval-modal{{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.85);z-index:2000;justify-content:center;align-items:center}}
.approval-modal.show{{display:flex}}
.approval-content{{background:linear-gradient(135deg,#37475A,#2d3a48);padding:40px;border-radius:12px;border:3px solid #4A90E2;max-width:600px;text-align:center}}
.approval-title{{font-size:1.8em;color:#4A90E2;margin-bottom:20px}}
.approval-details{{background:#1a1a1a;padding:20px;border-radius:8px;margin:20px 0;text-align:left}}
.approval-buttons{{display:flex;gap:15px;justify-content:center;margin-top:25px}}
.approval-btn{{padding:15px 40px;border:none;border-radius:8px;font-size:1.1em;font-weight:bold;cursor:pointer;transition:all 0.3s}}
.approval-btn.approve{{background:#4CAF50;color:white}}
.approval-btn.approve:hover{{background:#45a049}}
.approval-btn.reject{{background:#666;color:white}}
.approval-btn.reject:hover{{background:#555}}
.roi-display{{margin-top:15px;padding:15px;background:rgba(76,175,80,0.1);border-radius:8px;text-align:center;font-size:1em;border:2px solid #4CAF50}}
.roi-display strong{{color:#4CAF50;font-size:1.2em}}
footer{{text-align:center;margin-top:35px;padding-top:15px;border-top:2px solid #37475A;color:#888;font-size:0.85em}}
</style>
</head><body>

<div class="cost-badge">AWS AI Running Cost: <span class="cost-badge-value" id="costValue">$0.00</span></div>

<div class="scale-badge">
<div style="margin-bottom:5px;font-weight:bold;color:#4CAF50;font-size:0.95em">System Scale</div>
<div><span class="scale-badge-label">Stores:</span><span class="scale-badge-value">{1}</span></div>
<div><span class="scale-badge-label">SKUs:</span><span class="scale-badge-value">{2}</span></div>
<div><span class="scale-badge-label">Sales Data:</span><span class="scale-badge-value">Jan 2023-Oct 2024</span></div>
</div>

<div class="approval-modal" id="approvalModal">
<div class="approval-content">
<div class="approval-title">📋 Executive Approval Required</div>
<div class="approval-details" id="approvalDetails"></div>
<div class="approval-buttons">
<button class="approval-btn approve" id="approveBtn">✓ Approve & Continue</button>
<button class="approval-btn reject" id="rejectBtn">✗ Reject</button>
</div>
</div>
</div>

<div class="header">
<h1>⚡ StormGuard</h1>
<div class="aws-badge">Multi-Agent AI | Amazon Bedrock | Autonomous Supply Chain Resilience</div>
</div>

<div class="hero-impact" id="heroImpact" style="display:none">
<div class="hero-title" id="heroTitle">🎯 Business Impact</div>
<div class="hero-grid" id="heroGrid"></div>
<div class="roi-display" id="roiDisplay"></div>
</div>

<div class="run-log" id="runLog" style="display:none"></div>

<div class="mode-toggle">
<button class="mode-btn active" id="autonomousBtn">🤖 Autonomous Operations</button>
<button class="mode-btn" id="scenariosBtn">🎯 Test Scenarios</button>
</div>

<div class="autonomous-container active" id="autonomousContainer">
<div class="activity-log">
<div class="activity-log-title">🔄 Live Agent Activity Stream</div>
<div id="activityStream"></div>
</div>
<div class="flow-diagram">
<div class="flow-title">⚡ Agent Communication Flow</div>
<svg class="flow-svg" id="flowSvg" viewBox="0 0 400 500">
<defs>
<marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
<polygon points="0 0, 10 3, 0 6" fill="#4A90E2"/>
</marker>
</defs>
<!-- Edges -->
<path id="edge-demand-inventory" class="agent-edge" d="M 100 80 L 300 80" stroke="#4A90E2" stroke-width="2" marker-end="url(#arrowhead)" fill="none"/>
<path id="edge-inventory-procurement" class="agent-edge" d="M 300 120 L 300 200" stroke="#4A90E2" stroke-width="2" marker-end="url(#arrowhead)" fill="none"/>
<path id="edge-procurement-pricing" class="agent-edge" d="M 260 240 L 140 280" stroke="#4A90E2" stroke-width="2" marker-end="url(#arrowhead)" fill="none"/>
<path id="edge-pricing-risk" class="agent-edge" d="M 100 320 L 100 400" stroke="#4A90E2" stroke-width="2" marker-end="url(#arrowhead)" fill="none"/>
<path id="edge-risk-orchestrator" class="agent-edge" d="M 140 440 L 260 440" stroke="#4A90E2" stroke-width="2" marker-end="url(#arrowhead)" fill="none"/>
<path id="edge-demand-orchestrator" class="agent-edge" d="M 100 120 Q 50 280 100 400" stroke="#4A90E2" stroke-width="2" stroke-dasharray="5,5" marker-end="url(#arrowhead)" fill="none"/>
<!-- Nodes -->
<g id="node-demand" class="agent-node">
<circle cx="100" cy="100" r="35" fill="#E91E63" stroke="#fff" stroke-width="2"/>
<text x="100" y="105" text-anchor="middle" fill="white" font-size="28">🧠</text>
<text x="100" y="150" text-anchor="middle" fill="#E91E63" font-size="11" font-weight="bold">Demand</text>
</g>
<g id="node-inventory" class="agent-node">
<circle cx="300" cy="100" r="35" fill="#9C27B0" stroke="#fff" stroke-width="2"/>
<text x="300" y="105" text-anchor="middle" fill="white" font-size="28">📊</text>
<text x="300" y="150" text-anchor="middle" fill="#9C27B0" font-size="11" font-weight="bold">Inventory</text>
</g>
<g id="node-procurement" class="agent-node">
<circle cx="300" cy="220" r="35" fill="#FF9800" stroke="#fff" stroke-width="2"/>
<text x="300" y="225" text-anchor="middle" fill="white" font-size="28">📦</text>
<text x="300" y="270" text-anchor="middle" fill="#FF9800" font-size="11" font-weight="bold">Procurement</text>
</g>
<g id="node-pricing" class="agent-node">
<circle cx="100" cy="300" r="35" fill="#4CAF50" stroke="#fff" stroke-width="2"/>
<text x="100" y="305" text-anchor="middle" fill="white" font-size="28">💰</text>
<text x="100" y="350" text-anchor="middle" fill="#4CAF50" font-size="11" font-weight="bold">Pricing</text>
</g>
<g id="node-risk" class="agent-node">
<circle cx="100" cy="420" r="35" fill="#F44336" stroke="#fff" stroke-width="2"/>
<text x="100" y="425" text-anchor="middle" fill="white" font-size="28">🛡️</text>
<text x="100" y="470" text-anchor="middle" fill="#F44336" font-size="11" font-weight="bold">Risk</text>
</g>
<g id="node-orchestrator" class="agent-node">
<circle cx="300" cy="420" r="35" fill="#FF9900" stroke="#fff" stroke-width="2"/>
<text x="300" y="425" text-anchor="middle" fill="white" font-size="28">⚡</text>
<text x="300" y="470" text-anchor="middle" fill="#FF9900" font-size="11" font-weight="bold">Orchestrator</text>
</g>
</svg>
</div>
</div>

<div class="scenario-container hidden" id="scenarioContainer">
<button class="scenario-btn active" data-scenario="chris">🌊 Tropical Storm Chris</button>
<button class="scenario-btn" data-scenario="uri">❄️ Winter Storm Uri</button>
<button class="scenario-btn" data-scenario="milton">🌀 Hurricane Milton</button>
</div>

<div style="text-align:center" id="startBtnContainer">
<button class="start-button" id="startBtn" style="display:none">▶ Run Multi-Agent Coordination</button>
</div>

<div class="progress-bar" id="progressBar" style="display:none"><div class="progress-fill" id="progressFill"></div></div>

<div class="agents-grid">
<div class="agent-card" data-agent="demand">
<div class="agent-header"><span class="agent-icon">🧠</span><div><div class="agent-title">Demand Intelligence Agent</div><div class="agent-status">Waiting...</div></div></div>
<div class="agent-input"></div>
<div class="agent-insight"></div>
<div class="agent-metrics"></div>
</div>
<div class="agent-card" data-agent="inventory">
<div class="agent-header"><span class="agent-icon">📊</span><div><div class="agent-title">Inventory Optimizer Agent</div><div class="agent-status">Waiting...</div></div></div>
<div class="agent-input"></div>
<div class="agent-insight"></div>
<div class="agent-metrics"></div>
</div>
<div class="agent-card" data-agent="procurement">
<div class="agent-header"><span class="agent-icon">📦</span><div><div class="agent-title">Procurement Agent</div><div class="agent-status">Waiting...</div></div></div>
<div class="agent-input"></div>
<div class="agent-insight"></div>
<div class="agent-metrics"></div>
</div>
<div class="agent-card" data-agent="pricing">
<div class="agent-header"><span class="agent-icon">💰</span><div><div class="agent-title">Price Stability & Anti-Gouging Agent</div><div class="agent-status">Waiting...</div></div></div>
<div class="agent-input"></div>
<div class="agent-insight"></div>
<div class="agent-metrics"></div>
</div>
<div class="agent-card" data-agent="risk">
<div class="agent-header"><span class="agent-icon">🛡️</span><div><div class="agent-title">Risk & Compliance Agent</div><div class="agent-status">Waiting...</div></div></div>
<div class="agent-input"></div>
<div class="agent-insight"></div>
<div class="agent-metrics"></div>
</div>
<div class="agent-card" data-agent="orchestrator">
<div class="agent-header"><span class="agent-icon">⚡</span><div><div class="agent-title">Orchestrator Agent</div><div class="agent-status">Waiting...</div></div></div>
<div class="agent-input"></div>
<div class="agent-insight"></div>
<div class="agent-metrics"></div>
</div>
</div>

<div class="final-results" id="finalResults">
<div class="final-title">✅ Multi-Agent Coordination Complete</div>
<div class="final-summary" id="finalSummary"></div>
<div class="impact-grid" id="impactGrid"></div>
<div class="roi-tiny" id="roiTiny"></div>
</div>

<footer>
<p><strong>StormGuard</strong> | AWS AI Agent Global Hackathon 2025</p>
</footer>

<script>
let isRunning=false;
let totalCost=0;
let selectedScenario='chris';
let runHistory=[];
let autonomousMode=true;
let autonomousInterval=null;
const COST_PER_AGENT=0.0045;
const agents=['demand','inventory','procurement','pricing','risk','orchestrator'];
const agentResults={{}};
const startBtn=document.getElementById('startBtn');
const progressFill=document.getElementById('progressFill');
const progressBar=document.getElementById('progressBar');
const finalResults=document.getElementById('finalResults');
const heroImpact=document.getElementById('heroImpact');
const heroTitle=document.getElementById('heroTitle');
const heroGrid=document.getElementById('heroGrid');
const runLog=document.getElementById('runLog');
const costValue=document.getElementById('costValue');
const roiDisplay=document.getElementById('roiDisplay');
const autonomousBtn=document.getElementById('autonomousBtn');
const scenariosBtn=document.getElementById('scenariosBtn');
const autonomousContainer=document.getElementById('autonomousContainer');
const scenarioContainer=document.getElementById('scenarioContainer');
const activityStream=document.getElementById('activityStream');
const agentsGrid=document.querySelector('.agents-grid');
const costBadge=document.querySelector('.cost-badge');

autonomousBtn.addEventListener('click',()=>{{
  if(autonomousMode)return;
  autonomousMode=true;
  autonomousBtn.classList.add('active');
  scenariosBtn.classList.remove('active');
  autonomousContainer.classList.add('active');
  scenarioContainer.classList.add('hidden');
  startBtn.style.display='none';
  progressBar.style.display='none';
  agentsGrid.style.display='none';
  costBadge.style.display='none';
  finalResults.classList.remove('show');
  runLog.style.display='none';
  heroImpact.style.display='none';
  startAutonomousMode();
}});

scenariosBtn.addEventListener('click',()=>{{
  if(!autonomousMode)return;
  autonomousMode=false;
  scenariosBtn.classList.add('active');
  autonomousBtn.classList.remove('active');
  autonomousContainer.classList.remove('active');
  scenarioContainer.classList.remove('hidden');
  startBtn.style.display='inline-block';
  agentsGrid.style.display='grid';
  costBadge.style.display='block';
  stopAutonomousMode();
}});

const scenarioBtns=document.querySelectorAll('.scenario-btn');
scenarioBtns.forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    scenarioBtns.forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    selectedScenario=btn.dataset.scenario;
  }});
}});

const approvalModal=document.getElementById('approvalModal');
const approvalDetails=document.getElementById('approvalDetails');
const approveBtn=document.getElementById('approveBtn');
const rejectBtn=document.getElementById('rejectBtn');
let approvalPromise=null;

approveBtn.addEventListener('click',()=>{{
  approvalModal.classList.remove('show');
  if(approvalPromise)approvalPromise.resolve(true);
}});

rejectBtn.addEventListener('click',()=>{{
  approvalModal.classList.remove('show');
  if(approvalPromise)approvalPromise.resolve(false);
}});

const miniScenarios=[
  {{agent:'demand',msg:'Detected 1.5x demand surge for batteries in SE region',delay:0}},
  {{agent:'inventory',msg:'Checking stock levels across 12 stores',delay:1.2}},
  {{agent:'procurement',msg:'Sourcing 500 units from vendor Alpha Supply',delay:0.8}},
  {{agent:'pricing',msg:'Maintaining stable pricing (no increase)',delay:1.5}},
  {{agent:'risk',msg:'Auto-approved: $45K within threshold',delay:0.6}},
  {{agent:'orchestrator',msg:'Coordination complete - 95% service level maintained',delay:2.1}}
];

function startAutonomousMode(){{
  activityStream.innerHTML='';
  runAutonomousScenario();
  autonomousInterval=setInterval(runAutonomousScenario,12000);
}}

function stopAutonomousMode(){{
  if(autonomousInterval){{
    clearInterval(autonomousInterval);
    autonomousInterval=null;
  }}
}}

function runAutonomousScenario(){{
  const scenarios=[
    ['demand','inventory','procurement','pricing','risk','orchestrator'],
    ['demand','pricing','inventory','procurement','risk','orchestrator'],
    ['inventory','demand','procurement','risk','pricing','orchestrator']
  ];
  const scenario=scenarios[Math.floor(Math.random()*scenarios.length)];

  let delay=0;
  scenario.forEach((agent,idx)=>{{
    setTimeout(()=>{{
      const realDelay=(Math.random()*2+0.5).toFixed(1);
      const messages={{
        'demand':['Forecasting demand spike of '+(Math.random()*2+1).toFixed(1)+'x for water','Analyzing sales patterns across 50 stores','Detecting surge in hurricane preparedness items'],
        'inventory':['Checking stock levels at '+(Math.floor(Math.random()*15)+5)+' stores','Identifying '+Math.floor(Math.random()*10+5)+' at-risk locations','Calculating reorder points for critical SKUs'],
        'procurement':['Creating '+(Math.floor(Math.random()*20)+10)+' purchase orders','Engaging '+(Math.floor(Math.random()*4)+2)+' vendors for rapid fulfillment','Emergency procurement: $'+(Math.floor(Math.random()*200+100))+'K approved'],
        'pricing':['Maintaining price stability on essentials','Monitoring '+(Math.floor(Math.random()*5)+2)+' competitors for gouging','Price protected: $'+(Math.floor(Math.random()*100+50))+'K brand value'],
        'risk':['Auto-approved: $'+(Math.floor(Math.random()*300+100))+'K within policy','Compliance score: '+(Math.floor(Math.random()*3)+7)+'/10','Financial risk: low'],
        'orchestrator':['Multi-agent coordination complete','Service level: '+(Math.floor(Math.random()*5)+94)+'% maintained','Revenue protected: $'+(Math.random()*3+1).toFixed(1)+'M']
      }};
      const msg=messages[agent][Math.floor(Math.random()*messages[agent].length)];
      addActivityLog(agent,msg,realDelay,idx>0?scenario[idx-1]:null);
      highlightAgent(agent);
      if(idx>0){{
        highlightEdge(scenario[idx-1],agent);
      }}
    }},delay);
    delay+=Math.random()*1500+800;
  }});
}}

function addActivityLog(agent,message,delay,prevAgent){{
  const timestamp=new Date().toLocaleTimeString('en-US',{{hour:'2-digit',minute:'2-digit',second:'2-digit'}});
  const delayText=prevAgent?' ('+delay+'s after '+prevAgent.charAt(0).toUpperCase()+prevAgent.slice(1)+')':'';
  const entry=document.createElement('div');
  entry.className='activity-entry '+agent;
  entry.innerHTML='<span class="activity-timestamp">'+timestamp+'</span><span class="activity-agent">'+agent.charAt(0).toUpperCase()+agent.slice(1)+':</span><span class="activity-message">'+message+delayText+'</span>';
  activityStream.insertBefore(entry,activityStream.firstChild);
  if(activityStream.children.length>20){{
    activityStream.removeChild(activityStream.lastChild);
  }}
}}

function highlightAgent(agent){{
  const node=document.getElementById('node-'+agent);
  if(node){{
    node.classList.add('active');
    setTimeout(()=>node.classList.remove('active'),1500);
  }}
}}

function highlightEdge(fromAgent,toAgent){{
  const edgeId='edge-'+fromAgent+'-'+toAgent;
  const edge=document.getElementById(edgeId);
  if(edge){{
    edge.classList.add('active');
    setTimeout(()=>edge.classList.remove('active'),1000);
  }}
}}

startBtn.addEventListener('click',async()=>{{
  if(isRunning)return;
  isRunning=true;
  startBtn.disabled=true;
  startBtn.textContent='⏳ AI Agents Processing...';
  totalCost=0;
  costValue.textContent='$0.00';

  document.querySelectorAll('.agent-card').forEach(card=>{{
    card.classList.remove('active','complete');
    card.querySelector('.agent-status').textContent='Waiting...';
    card.querySelector('.agent-input').classList.remove('show');
    card.querySelector('.agent-input').innerHTML='';
    card.querySelector('.agent-insight').classList.remove('show');
    card.querySelector('.agent-insight').innerHTML='';
    card.querySelector('.agent-metrics').classList.remove('show');
    card.querySelector('.agent-metrics').innerHTML='';
  }});

  progressFill.style.width='0%';
  finalResults.classList.remove('show');

  for(let i=0;i<agents.length;i++){{
    progressFill.style.width=((i+1)/agents.length*100)+'%';
    const success=await runAgent(agents[i]);
    if(!success){{
      isRunning=false;
      startBtn.disabled=false;
      startBtn.textContent='↻ Run Again';
      return;
    }}

    if(agents[i]==='risk'&&agentResults.risk&&agentResults.risk.approval_status==='governance_review'){{
      const approved=await requestHumanApproval();
      if(!approved){{
        // Mark all remaining agents as cancelled
        for(let j=i+1;j<agents.length;j++){{
          const remainingCard=document.querySelector(`[data-agent="${{agents[j]}}"]`);
          if(remainingCard){{
            remainingCard.classList.remove('active');
            remainingCard.classList.add('complete');
            remainingCard.querySelector('.agent-status').textContent='❌ Cancelled (Governance Rejected)';
            remainingCard.querySelector('.agent-status').style.color='#F44336';
          }}
        }}

        // Log the rejection in run history
        const timestamp=new Date().toLocaleTimeString('en-US',{{hour:'2-digit',minute:'2-digit',second:'2-digit'}});
        const scenarioNames={{'chris':'🌊 Tropical Storm Chris','uri':'❄️ Winter Storm Uri','milton':'🌀 Hurricane Milton'}};
        const scenarioName=scenarioNames[selectedScenario]||selectedScenario;
        const proc=agentResults.procurement;

        runHistory.unshift({{time:timestamp,scenario:scenarioName,revenue:0,risk:'rejected',spend:proc?proc.total_value_usd:0}});
        if(runHistory.length>3)runHistory.pop();

        let logHTML='';
        runHistory.forEach(run=>{{
          if(run.risk==='rejected'){{
            logHTML+='<div class="run-log-entry"><span class="run-log-time">'+run.time+'</span><span class="run-log-scenario">'+run.scenario+'</span><span class="run-log-risk rejected"> | ❌ Rejected</span> → Spend: <strong>$'+(run.spend?run.spend.toLocaleString():'0')+'</strong> (Governance Denied)</div>';
          }}else{{
            const riskClass=run.risk==='governance'?'governance':'auto';
            const riskText=run.risk==='governance'?'📋 Governance':'✓ Auto';
            logHTML+='<div class="run-log-entry"><span class="run-log-time">'+run.time+'</span><span class="run-log-scenario">'+run.scenario+'</span><span class="run-log-risk '+riskClass+'"> | '+riskText+'</span> → Revenue: <strong>$'+run.revenue.toFixed(1)+'M</strong></div>';
          }}
        }});
        runLog.innerHTML=logHTML;
        runLog.style.display='block';

        alert('Execution halted: Executive approval rejected. Emergency procurement cancelled.');
        isRunning=false;
        startBtn.disabled=false;
        startBtn.textContent='↻ Run Again';
        return;
      }}
    }}

    await new Promise(r=>setTimeout(r,1000));
  }}

  showFinalResults();
  isRunning=false;
  startBtn.disabled=false;
  startBtn.textContent='↻ Run Again';
}});

function requestHumanApproval(){{
  return new Promise((resolve)=>{{
    const risk=agentResults.risk;
    const proc=agentResults.procurement;
    const demand=agentResults.demand;
    const inventory=agentResults.inventory;
    const scenarioNames={{'chris':'🌊 Tropical Storm Chris','uri':'❄️ Winter Storm Uri','milton':'🌀 Hurricane Milton'}};
    const scenarioName=scenarioNames[selectedScenario]||selectedScenario;

    let details='<div style="background:rgba(255,153,0,0.1);padding:15px;border-radius:8px;border-left:4px solid #FF9900;margin-bottom:20px">';
    details+='<h3 style="color:#FF9900;margin-bottom:10px;font-size:1.1em">Crisis Situation: '+scenarioName+'</h3>';
    if(inventory&&inventory.at_risk_stores){{
      details+='<p style="margin:5px 0"><strong>'+inventory.at_risk_stores+' stores</strong> at risk of stockouts within 48 hours</p>';
    }}
    if(demand&&demand.forecast_multiplier){{
      details+='<p style="margin:5px 0">Demand surge: <strong>'+demand.forecast_multiplier+'x normal levels</strong></p>';
    }}
    if(proc&&proc.key_insight){{
      details+='<p style="margin:5px 0;font-style:italic;color:#ddd">'+proc.key_insight+'</p>';
    }}
    details+='</div>';

    details+='<div style="background:rgba(74,144,226,0.1);padding:15px;border-radius:8px;border-left:4px solid #4A90E2;margin-bottom:15px">';
    details+='<p><strong>Procurement Spend:</strong> <span style="color:#4A90E2;font-size:1.2em">$'+(proc?proc.total_value_usd.toLocaleString():'unknown')+'</span></p>';
    details+='<p><strong>Auto-Approval Threshold:</strong> $500,000</p>';
    details+='<p><strong>Risk Level:</strong> '+(risk.financial_risk||'high').toUpperCase()+'</p>';
    if(risk.flagged_issues&&risk.flagged_issues.length>0){{
      details+='<p><strong>Compliance Flags:</strong> '+risk.flagged_issues.join(', ')+'</p>';
    }}
    details+='</div>';

    details+='<p style="color:#AAB7B8;font-size:0.9em;text-align:center;margin-top:15px">Governance review required for decisions exceeding $500K. Approval enables AI agents to execute emergency procurement and protect revenue.</p>';

    approvalDetails.innerHTML=details;
    approvalModal.classList.add('show');
    approvalPromise={{resolve:resolve}};
  }});
}}

async function runAgent(agentName){{
  const card=document.querySelector(`[data-agent="${{agentName}}"]`);
  card.classList.add('active');
  card.querySelector('.agent-status').textContent='⚡ Calling Amazon Bedrock...';

  let retries=0;
  const maxRetries=3;

  while(retries<maxRetries){{
    try{{
      const response=await fetch('?action='+agentName+'&scenario='+selectedScenario);
      if(!response.ok)throw new Error('HTTP '+response.status);
      const data=await response.json();
      const result=JSON.parse(data.result);
      agentResults[agentName]=result;
      totalCost+=COST_PER_AGENT;
      costValue.textContent='$'+totalCost.toFixed(4);
      card.classList.remove('active');
      card.classList.add('complete');
      card.querySelector('.agent-status').textContent='✓ Complete';
      renderAgentDetails(card,agentName,result);
      return true;
    }}catch(e){{
      retries++;
      if(retries>=maxRetries){{
        card.querySelector('.agent-status').textContent='✗ Error (3 retries failed)';
        card.classList.remove('active');
        console.error('Agent '+agentName+' failed:',e);
        return false;
      }}
      await new Promise(r=>setTimeout(r,2000));
    }}
  }}
  return false;
}}

function renderAgentDetails(card,agentName,result){{
  const inputDiv=card.querySelector('.agent-input');
  const insightDiv=card.querySelector('.agent-insight');
  const metricsDiv=card.querySelector('.agent-metrics');

  // Build data input display based on agent and previous results
  let inputHTML='<strong>Data Input:</strong> ';
  const scenarioSpikes={{'chris':2.2,'uri':2.8,'milton':4.2}};
  const spike=scenarioSpikes[selectedScenario]||3.5;

  if(agentName==='demand'){{
    inputHTML+='Sales history: 10,000 rows analyzed, Scenario: '+spike+'x demand surge expected';
  }}else if(agentName==='inventory'){{
    const dem=agentResults.demand;
    inputHTML+='Demand forecast: '+(dem?dem.forecast_multiplier+'x surge, '+dem.units_needed.toLocaleString()+' units needed':'processing...');
  }}else if(agentName==='procurement'){{
    const inv=agentResults.inventory;
    inputHTML+='Inventory analysis: '+(inv?inv.at_risk_stores+' stores at risk, '+inv.total_units_to_order.toLocaleString()+' units to order':'processing...');
  }}else if(agentName==='pricing'){{
    const dem=agentResults.demand;
    inputHTML+='Demand surge: '+(dem?dem.forecast_multiplier+'x':'processing...')+', Competitor monitoring: Active, Anti-gouging policy: Enforced';
  }}else if(agentName==='risk'){{
    const proc=agentResults.procurement;
    inputHTML+='Procurement spend: $'+(proc?proc.total_value_usd.toLocaleString():'processing...')+', Auto-approval threshold: $500,000';
  }}else if(agentName==='orchestrator'){{
    inputHTML+='All 5 specialist agent analyses complete, synthesizing business impact';
  }}

  inputDiv.innerHTML=inputHTML;
  inputDiv.classList.add('show');

  const insight=result.key_insight||result.executive_summary||'Analysis complete';
  insightDiv.innerHTML='<strong>Key Insight:</strong> '+insight;
  insightDiv.classList.add('show');

  let metricsHTML='';
  const contextMap={{
    'forecast_multiplier':'demand spike factor',
    'units_needed':'units to order',
    'at_risk_stores':'stores facing stockouts',
    'total_units_to_order':'total units across stores',
    'purchase_orders':'POs created',
    'total_value_usd':'emergency procurement spend',
    'price_adjustment_pct':'price change %',
    'price_stability_maintained':'stable pricing during crisis',
    'competitor_gouging_flagged':'',
    'brand_protection_value_usd':'estimated brand goodwill value',
    'approval_status':'',
    'compliance_score':'out of 10',
    'service_level_pct':'target maintained',
    'revenue_protected_millions':'revenue saved by AI',
    'revenue_protected_usd':'revenue saved by AI',
    'automation_level_pct':'decisions auto-approved',
    'stores_prevented_stockout':'stores restocked in time'
  }};

  Object.entries(result).forEach(([key,value])=>{{
    if(key!=='key_insight'&&key!=='executive_summary'&&key!=='flagged_issues'){{
      const context=contextMap[key]||'';
      const displayValue=typeof value==='number'&&value>1000?value.toLocaleString():value;
      metricsHTML+='<div class="metric-row"><span class="metric-label">'+key.replace(/_/g,' ')+':</span> <span class="metric-value">'+displayValue+'</span> <span class="metric-context">'+context+'</span></div>';
    }}
  }});

  if(agentName==='risk'){{
    const approvalClass=result.approval_status==='auto_approved'?'auto':'governance';
    const badgeText=result.approval_status==='auto_approved'?'AUTO APPROVED':'Governance Review (Human-in-the-Loop)';
    metricsHTML+='<div class="approval-badge '+approvalClass+'">'+badgeText+'</div>';
  }}

  metricsDiv.innerHTML=metricsHTML;
  metricsDiv.classList.add('show');
}}

function showFinalResults(){{
  const orch=agentResults.orchestrator;
  if(!orch)return;

  const dem=agentResults.demand;
  const inv=agentResults.inventory;
  const proc=agentResults.procurement;
  const risk=agentResults.risk;

  const timestamp=new Date().toLocaleTimeString('en-US',{{hour:'2-digit',minute:'2-digit',second:'2-digit'}});
  const scenarioNames={{'chris':'🌊 Tropical Storm Chris','uri':'❄️ Winter Storm Uri','milton':'🌀 Hurricane Milton'}};
  const scenarioName=scenarioNames[selectedScenario]||selectedScenario;

  const revenueM=parseFloat(orch.revenue_protected_millions||orch.revenue_protected_usd||0);
  const riskStatus=risk&&risk.approval_status==='governance_review'?'governance':'auto';

  runHistory.unshift({{time:timestamp,scenario:scenarioName,revenue:revenueM,risk:riskStatus}});
  if(runHistory.length>3)runHistory.pop();

  let logHTML='';
  runHistory.forEach(run=>{{
    if(run.risk==='rejected'){{
      logHTML+='<div class="run-log-entry"><span class="run-log-time">'+run.time+'</span><span class="run-log-scenario">'+run.scenario+'</span><span class="run-log-risk rejected"> | ❌ Rejected</span> → Spend: <strong>$'+(run.spend?run.spend.toLocaleString():'0')+'</strong> (Governance Denied)</div>';
    }}else{{
      const riskClass=run.risk==='governance'?'governance':'auto';
      const riskText=run.risk==='governance'?'📋 Governance':'✓ Auto';
      logHTML+='<div class="run-log-entry"><span class="run-log-time">'+run.time+'</span><span class="run-log-scenario">'+run.scenario+'</span><span class="run-log-risk '+riskClass+'"> | '+riskText+'</span> → Revenue: <strong>$'+run.revenue.toFixed(1)+'M</strong></div>';
    }}
  }});
  runLog.innerHTML=logHTML;
  runLog.style.display='block';

  const summaryHTML='<h3>Executive Summary</h3><p>'+orch.executive_summary+'</p><p style="margin-top:10px"><strong>Demand Forecast:</strong> '+(dem?dem.key_insight:'')+'</p><p><strong>Inventory Action:</strong> '+(inv?inv.key_insight:'')+'</p><p><strong>Procurement:</strong> '+(proc?proc.key_insight:'')+'</p>';
  document.getElementById('finalSummary').innerHTML=summaryHTML;

  const baselineRevenue=revenueM*0.60;
  const revenueGain=revenueM-baselineRevenue;
  const roiPct=((revenueGain/baselineRevenue)*100).toFixed(0);

  heroTitle.innerHTML='🎯 Business Impact: '+scenarioName;
  const heroHTML='<div class="hero-card"><div class="hero-value">'+orch.service_level_pct+'%</div><div class="hero-label">Service Level</div><div class="hero-context">vs 60% industry baseline</div></div>'+'<div class="hero-card"><div class="hero-value">$'+revenueM.toFixed(1)+'M</div><div class="hero-label">Revenue Protected</div><div class="hero-context">during crisis event</div></div>'+'<div class="hero-card"><div class="hero-value">'+orch.stores_prevented_stockout+'</div><div class="hero-label">Stockouts Prevented</div><div class="hero-context">critical supplies</div></div>'+'<div class="hero-card"><div class="hero-value">'+orch.automation_level_pct+'%</div><div class="hero-label">Automation</div><div class="hero-context">vs manual coordination</div></div>';
  heroGrid.innerHTML=heroHTML;

  roiDisplay.innerHTML='<strong>ROI: '+roiPct+'% revenue gain</strong> ($'+revenueGain.toFixed(1)+'M additional revenue vs $'+baselineRevenue.toFixed(1)+'M baseline) | Approval: <strong>'+(risk&&risk.approval_status==='governance_review'?'Governance Review (Human-in-the-Loop)':'Auto-Approved')+'</strong>';
  heroImpact.style.display='block';

  finalResults.classList.remove('show');
}}

// Initialize autonomous mode on page load
if(autonomousMode){{
  startAutonomousMode();
}}
</script>
</body></html>""".format(
        stats["spike_multiplier"],
        stats["num_stores"],
        stats["num_products"]
    )
