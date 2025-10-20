# StormGuard Architecture

## System Overview

StormGuard is a multi-agent AI system that autonomously manages retail supply chains during disruptions. It uses Amazon Bedrock AgentCore to orchestrate 6 specialized agents that sense market conditions, decide optimal actions, and execute changes within policy guardrails.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Event Sources                            │
│  • Weather API (OpenWeather)                                 │
│  • News API (newsapi.org)                                    │
│  • Internal triggers (cron, manual)                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Amazon EventBridge                              │
│  Routes events to appropriate workflows                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│           AWS Step Functions                                 │
│  Orchestrates agent workflow with retries & error handling   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Orchestrator Agent (Amazon Bedrock AgentCore)          │
│  • Coordinates all agents                                    │
│  • Routes requests to specialized agents                     │
│  • Enforces policy gates                                     │
│  • Maintains conversation history                            │
└────────────────┬────────────────────────────────────────────┘
                 │
       ┌─────────┴─────────┬──────────┬──────────┬──────────┐
       ▼                   ▼          ▼          ▼          ▼
┌─────────────┐  ┌──────────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│  Demand     │  │  Inventory   │  │ Pricing│  │Procure │  │  Risk  │
│Intelligence │  │  Optimizer   │  │ Agent  │  │ -ment  │  │Compli- │
│   Agent     │  │    Agent     │  │        │  │ Agent  │  │  ance  │
└──────┬──────┘  └──────┬───────┘  └───┬────┘  └───┬────┘  └───┬────┘
       │                │              │           │           │
       │                │              │           │           │
       └────────────────┴──────────────┴───────────┴───────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │    Agent Tools         │
                    │  • forecast.query      │
                    │  • inventory.optimize  │
                    │  • pricing.update      │
                    │  • procurement.create  │
                    │  • risk.check          │
                    └────────┬───────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        ┌───────────────┐         ┌──────────────┐
        │  AWS Lambda   │         │  Amazon S3   │
        │  (Tools)      │◄────────┤  (Data Lake) │
        └───────┬───────┘         └──────────────┘
                │
                ▼
        ┌──────────────┐
        │  DynamoDB    │
        │  (State)     │
        └──────────────┘
                │
                ▼
        ┌──────────────┐
        │  API Gateway │
        └───────┬──────┘
                │
                ▼
        ┌──────────────┐
        │   React UI   │
        │  (Dashboard) │
        └──────────────┘
```

## Agent Details

### 1. Orchestrator Agent

**Technology**: Amazon Bedrock AgentCore  
**Model**: Claude Sonnet 4  
**Role**: Master coordinator

**Responsibilities**:
- Receives events (hurricane warning, demand spike, etc.)
- Routes requests to appropriate specialist agents
- Aggregates responses from multiple agents
- Enforces policy gates (auto-approve vs human approval)
- Maintains audit trail of all decisions

**Key Logic**:
```python
if event.type == 'hurricane_warning':
    # Parallel execution
    forecast = demand_agent.predict(event)
    inventory = inventory_agent.analyze(forecast)
    pricing = pricing_agent.recommend(event)
    
    # Coordinate actions
    plan = combine_recommendations(forecast, inventory, pricing)
    
    if risk_agent.check(plan).approved:
        procurement_agent.execute(plan)
    else:
        request_human_approval(plan)
```

### 2. Demand Intelligence Agent

**Tools Used**: `forecast.query`, `weather.get_forecast`, `news.search_events`

**Capabilities**:
- Time series forecasting (Prophet/ARIMA)
- Event impact modeling (hurricanes, sports, holidays)
- Demand elasticity estimation
- Cross-product cannibalization analysis

**Output Example**:
```json
{
  "sku": "SKU-0001",
  "baseline_qty": 15,
  "hurricane_adjusted_qty": 52,
  "confidence": "high",
  "reasoning": "Hurricane Milton Cat 4, water demand surge 3.5x"
}
```

### 3. Inventory Optimization Agent

**Tools Used**: `inventory.optimize`, `forecast.bulk_forecast`

**Capabilities**:
- Reorder point calculation
- Safety stock optimization
- Multi-echelon inventory allocation
- Transfer planning between stores

**Algorithm**:
```
Reorder Point = (Lead Time × Daily Velocity) + Safety Stock
Safety Stock = Z-score × σ(demand) × √(lead_time)
Order Quantity = Max(0, Target Level - On Hand - On Order)
```

### 4. Dynamic Pricing Agent

**Tools Used**: `pricing.update`, `elasticity.estimate`

**Capabilities**:
- Price optimization within guardrails
- Competitive price monitoring
- Demand-based dynamic pricing
- Anti-gouging enforcement (max +10% during crisis)

**Policy**:
- Normal: optimize for margin
- High demand event: cap increases, prioritize availability
- Surplus: markdown to clear inventory

### 5. Procurement Agent

**Tools Used**: `procurement.create_po`, `vendor.select`, `capacity.schedule`

**Capabilities**:
- Purchase order creation
- Vendor selection (cost, reliability, lead time)
- Order quantity optimization (MOQ, EOQ)
- Shipment scheduling and routing

**Decision Factors**:
- Unit cost + shipping
- Lead time urgency
- Vendor reliability score
- Capacity constraints

### 6. Risk & Compliance Agent

**Tools Used**: `risk.check`, `policy.validate`, `audit.log`

**Capabilities**:
- Policy gate enforcement
- Financial risk assessment
- Regulatory compliance checks
- Audit trail generation
- Rollback planning

**Approval Logic**:
```python
def check_approval_needed(action):
    if action.financial_impact > 50000:
        return 'human_approval'
    if action.price_change_pct > 10:
        return 'human_approval'
    if action.new_vendor and not action.vendor_vetted:
        return 'human_approval'
    return 'auto_approve'
```

## Data Flow

### Hurricane Milton Scenario

**T-72h: Event Detection**
```
Weather API → EventBridge → Step Functions → Orchestrator
```

**T-60h: Demand Forecasting**
```
Orchestrator → Demand Agent → forecast.query(water, batteries, etc.)
→ Returns: 300% spike predicted
```

**T-48h: Inventory Analysis**
```
Orchestrator → Inventory Agent → inventory.optimize()
→ Returns: 23 stores at stockout risk
```

**T-36h: Procurement Planning**
```
Orchestrator → Procurement Agent → procurement.create_po()
→ Creates: 47 emergency POs ($400K total)
```

**T-24h: Pricing Adjustment**
```
Orchestrator → Pricing Agent → pricing.update(max_increase=0.10)
→ Updates: 89 SKU prices (+5-10%)
```

**T-12h: Risk Validation**
```
Orchestrator → Risk Agent → risk.check(full_plan)
→ Result: Auto-approved (within policy)
```

**T-0h: Execution**
```
All agents execute approved actions in parallel
DynamoDB stores state, audit logs
Dashboard updates in real-time
```

## Technology Stack

### AWS Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| Amazon Bedrock | LLM reasoning | Claude Sonnet 4 |
| Bedrock AgentCore | Agent orchestration | Multi-agent, tool routing |
| AWS Lambda | Tool execution | Python 3.11, 512MB RAM |
| Step Functions | Workflow coordination | Standard workflows |
| EventBridge | Event routing | Custom event bus |
| S3 | Data lake | Parquet + CSV |
| DynamoDB | State management | On-demand capacity |
| API Gateway | REST endpoints | Regional, CORS enabled |
| CloudWatch | Monitoring | Custom dashboards |

### External Services

| Service | Purpose | Tier |
|---------|---------|------|
| OpenWeather | Weather forecasts | Free (1000/day) |
| NewsAPI | Event detection | Free (100/day) |
| OpenStreetMap | Geocoding | Free (unlimited) |

### Frontend

- **Framework**: React 18
- **Charts**: Recharts
- **Maps**: Leaflet + React-Leaflet
- **Icons**: Lucide React
- **Styling**: Tailwind CSS

## Security & Compliance

### IAM Permissions

```hcl
# Lambda execution role
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "s3:GetObject",
    "dynamodb:PutItem",
    "dynamodb:GetItem",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

### Data Protection

- All data at rest encrypted (S3 + DynamoDB)
- TLS 1.2+ for data in transit
- No PII stored (synthetic data only)
- API Gateway authentication via API keys

### Audit Trail

Every agent decision logged with:
- Timestamp
- Agent ID
- Input context
- Tool calls made
- Output decision
- Approval status
- User ID (if human approved)

## Scalability

### Current Capacity

- **Throughput**: 100 events/minute
- **Stores supported**: 50 (demo), 10,000+ (prod)
- **SKUs supported**: 200 (demo), 100,000+ (prod)
- **Response time**: <5 seconds for standard events

### Scaling Strategies

1. **Horizontal scaling**: More Lambda concurrency
2. **Agent parallelism**: Multiple agents per orchestrator
3. **Caching**: Frequently accessed forecasts cached
4. **Async execution**: Non-critical updates queued

## Monitoring & Observability

### Key Metrics

- **Agent response time**: P50, P95, P99
- **Tool call success rate**: % successful
- **Approval rate**: % auto vs human
- **Financial impact**: $ value of decisions
- **Service level**: % orders fulfilled

### Alerts

- Agent error rate > 5%
- Response time > 10s
- Human approval backlog > 10
- Budget threshold exceeded

## Cost Estimation

**Monthly AWS Costs** (50 stores, 10 events/day):

| Service | Usage | Cost |
|---------|-------|------|
| Bedrock | 30K tokens/day | $75 |
| Lambda | 300K invocations | $12 |
| S3 | 100GB storage | $3 |
| DynamoDB | On-demand | $25 |
| Step Functions | 300 executions | $0.75 |
| **Total** | | **~$116/month** |

**Scale to 1000 stores**: ~$500/month

## Deployment

### Infrastructure as Code

All resources defined in Terraform:
- `infrastructure/terraform/main.tf`
- `infrastructure/terraform/bedrock.tf`
- `infrastructure/terraform/lambda.tf`

### Deployment Steps

```bash
# 1. Initialize Terraform
cd infrastructure/terraform
terraform init

# 2. Review plan
terraform plan -out=plan.out

# 3. Apply
terraform apply plan.out

# 4. Verify deployment
aws bedrock list-agents
aws lambda list-functions --query "Functions[?contains(FunctionName, 'stormguard')]"
```

## Testing Strategy

### Unit Tests
- Each tool independently tested
- Mock Bedrock responses
- pytest + moto (AWS mocking)

### Integration Tests
- End-to-end scenario execution
- Real Bedrock calls (dev agent)
- Validate decision quality

### Load Tests
- Simulate 100 concurrent events
- Verify no throttling
- Response time < 5s @ P95

## Future Enhancements

1. **Reinforcement Learning**: Train RL policy for multi-objective optimization
2. **Real-time Collaboration**: Multi-store coordination for inventory sharing
3. **Supplier Integration**: Direct API to vendor systems
4. **Mobile App**: Store manager approval interface
5. **Multi-region**: Expand beyond Florida

## References

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AgentCore User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Multi-Agent Systems Paper](https://arxiv.org/abs/2308.08155)
- [Supply Chain Optimization](https://www.sciencedirect.com/topics/engineering/supply-chain-optimization)
