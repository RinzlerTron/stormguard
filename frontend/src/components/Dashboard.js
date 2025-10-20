/**
 * StormGuard Main Dashboard Component
 * 
 * Displays autonomous agent decisions during Hurricane Milton scenario.
 * Shows before/after metrics, decision timeline, and map visualization.
 */

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Activity, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

import './Dashboard.css';

const Dashboard = () => {
  const [scenario, setScenario] = useState('milton');
  const [agentDecisions, setAgentDecisions] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    // Fetch initial metrics
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const startScenario = async () => {
    setIsRunning(true);
    setAgentDecisions([]);

    try {
      // Start the agent orchestration
      const response = await fetch('/api/scenarios/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ scenario }),
      });

      const data = await response.json();
      
      // Poll for decision updates
      pollDecisions(data.execution_id);
    } catch (error) {
      console.error('Failed to start scenario:', error);
      setIsRunning(false);
    }
  };

  const pollDecisions = async (executionId) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/scenarios/status/' + executionId);
        const data = await response.json();
        
        if (data.decisions) {
          setAgentDecisions(data.decisions);
        }

        if (data.status === 'completed') {
          clearInterval(interval);
          setIsRunning(false);
          fetchMetrics();
        }
      } catch (error) {
        console.error('Poll error:', error);
        clearInterval(interval);
        setIsRunning(false);
      }
    }, 2000);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>StormGuard Autonomous Supply Chain</h1>
        <p className="subtitle">Multi-Agent AI System for Disruption Response</p>
      </header>

      {/* Metrics Overview */}
      <div className="metrics-grid">
        <MetricCard
          title="Service Level"
          icon={<CheckCircle />}
          value={metrics ? metrics.service_level + '%' : '--'}
          change={metrics ? '+38%' : '--'}
          positive
        />
        <MetricCard
          title="Revenue Impact"
          icon={<TrendingUp />}
          value={metrics ? formatCurrency(metrics.revenue_impact) : '--'}
          change={metrics ? '+$2.1M' : '--'}
          positive
        />
        <MetricCard
          title="Stockout Risk"
          icon={<AlertTriangle />}
          value={metrics ? metrics.stockout_risk : '--'}
          change={metrics ? '-40%' : '--'}
          positive
        />
        <MetricCard
          title="Automation Rate"
          icon={<Activity />}
          value={metrics ? metrics.automation_rate + '%' : '--'}
          change={metrics ? '80% auto' : '--'}
          positive
        />
      </div>

      {/* Scenario Control */}
      <div className="scenario-control">
        <h2>Hurricane Milton Scenario</h2>
        <p>
          Category 4 hurricane approaching Florida coast. 
          Watch agents autonomously optimize supply chain in real-time.
        </p>
        <button
          className="btn-primary"
          onClick={startScenario}
          disabled={isRunning}
        >
          {isRunning ? 'Running...' : 'Start Scenario'}
        </button>
      </div>

      {/* Decision Timeline */}
      {agentDecisions.length > 0 && (
        <div className="decision-timeline">
          <h2>Agent Decision Timeline</h2>
          <div className="timeline">
            {agentDecisions.map((decision, index) => (
              <DecisionCard key={index} decision={decision} />
            ))}
          </div>
        </div>
      )}

      {/* Demand Forecast Chart */}
      {metrics && metrics.forecast_data && (
        <div className="chart-container">
          <h2>Demand Forecast: Water & Batteries</h2>
          <LineChart
            width={800}
            height={300}
            data={metrics.forecast_data}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="baseline"
              stroke="#8884d8"
              name="Baseline"
            />
            <Line
              type="monotone"
              dataKey="hurricane"
              stroke="#ff7300"
              name="Hurricane Adjusted"
            />
          </LineChart>
        </div>
      )}
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, icon, value, change, positive }) => {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-icon">{icon}</span>
        <h3>{title}</h3>
      </div>
      <div className="metric-value">{value}</div>
      <div className={positive ? 'metric-change positive' : 'metric-change negative'}>
        {change}
      </div>
    </div>
  );
};

// Decision Card Component
const DecisionCard = ({ decision }) => {
  const getAgentColor = (agent) => {
    const colors = {
      demand: '#3b82f6',
      inventory: '#10b981',
      pricing: '#f59e0b',
      procurement: '#8b5cf6',
      risk: '#ef4444',
    };
    return colors[agent] || '#6b7280';
  };

  return (
    <div
      className="decision-card"
      style={{ borderLeftColor: getAgentColor(decision.agent) }}
    >
      <div className="decision-time">{decision.timestamp}</div>
      <div className="decision-agent">{decision.agent_name}</div>
      <div className="decision-action">{decision.action}</div>
      <div className="decision-reasoning">{decision.reasoning}</div>
      {decision.tools_used && (
        <div className="decision-tools">
          Tools: {decision.tools_used.join(', ')}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
