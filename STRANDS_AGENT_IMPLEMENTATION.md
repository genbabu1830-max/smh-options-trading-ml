# Strands Agent Implementation Guide
## Building the Recommendation Agent for Options Trading

**Date:** December 6, 2024  
**Framework:** Strands Agents  
**Reference:** lab-01-create-an-agent.ipynb

---

## My Understanding of Strands Framework

### Core Concepts

Based on the documentation and reference code, here's how Strands works:

#### 1. **Agent Creation Pattern**

```python
from strands import Agent
from strands.models import BedrockModel
from strands.tools import tool

# Step 1: Define tools with @tool decorator
@tool
def my_tool(param: str) -> str:
    """Tool description for the LLM.
    
    Args:
        param: Parameter description
    
    Returns:
        Result description
    """
    # Implementation
    return result

# Step 2: Initialize model
model = BedrockModel(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    temperature=0.3,
    region_name="us-east-1"
)

# Step 3: Create agent with tools and instructions
agent = Agent(
    model=model,
    tools=[my_tool],
    system_prompt="You are a helpful assistant..."
)

# Step 4: Invoke agent
response = agent("User query here")
```

#### 2. **Tool Definition**

Tools are the key to agent capabilities. Strands supports three approaches:

**A. Function-based tools (Simplest - We'll use this)**
```python
@tool
def calculate_area(shape: str, radius: float = None) -> float:
    """Calculate area of a shape.
    
    Args:
        shape: Shape type (circle, square)
        radius: Radius for circle
    """
    if shape == "circle":
        return 3.14159 * radius ** 2
    return 0.0
```

**B. Class-based tools (For shared state)**
```python
class DatabaseTools:
    def __init__(self, connection_string):
        self.connection = self._connect(connection_string)
    
    @tool
    def query_database(self, sql: str) -> dict:
        """Run SQL query."""
        return self.connection.execute(sql)
```

**C. Module-based tools (Framework-independent)**
```python
# weather.py
TOOL_SPEC = {
    "name": "weather_forecast",
    "description": "Get weather forecast",
    "inputSchema": {...}
}

def weather_forecast(tool, **kwargs):
    # Implementation
    pass
```

#### 3. **Tool Context (Advanced)**

Tools can access agent state and invocation context:

```python
from strands import ToolContext

@tool(context=True)
def get_user_data(query: str, tool_context: ToolContext) -> dict:
    """Get user-specific data."""
    user_id = tool_context.invocation_state.get("user_id")
    # Use user_id to personalize response
    return fetch_data(user_id, query)

# Invoke with state
agent("Get my data", user_id="user123")
```

#### 4. **Async Tools (For I/O operations)**

```python
@tool
async def fetch_api_data(endpoint: str) -> dict:
    """Fetch data from API asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint) as response:
            return await response.json()
```

---

## How to Build Our Recommendation Agent

### Architecture Overview

```
User Request
    ↓
Recommendation Agent (Strands)
    ├─→ Tool 1: fetch_market_data() - Get option chain from Massive.com
    ├─→ Tool 2: extract_features() - Convert to 84 features
    ├─→ Tool 3: predict_strategy() - ML model prediction (Stage 1)
    └─→ Tool 4: generate_parameters() - Rules-based params (Stage 2)
    ↓
Complete Trade Recommendation
```

### Implementation

#### Step 1: Install Strands

```bash
pip install strands-agents
pip install strands-tools  # For community tools
```

#### Step 2: Create Tools for Our System

```python
# agents/recommendation_agent.py

import boto3
import joblib
import pandas as pd
from strands import Agent, tool
from strands.models import BedrockModel

# Import our existing modules
import sys
sys.path.append('/path/to/project')
from scripts.utils.feature_extractor import FeatureExtractor
from scripts.utils.parameter_generator import ParameterGenerator, RiskManager

# Initialize our components (load once, reuse)
feature_extractor = FeatureExtractor()
risk_manager = RiskManager(account_size=10000, risk_per_trade=0.02)
parameter_generator = ParameterGenerator(risk_manager=risk_manager)

# Load ML model from S3 (or local for testing)
s3 = boto3.client('s3')
model_obj = s3.get_object(Bucket='smh-options-models', Key='production/lightgbm_clean_model.pkl')
ml_model = joblib.loads(model_obj['Body'].read())

encoder_obj = s3.get_object(Bucket='smh-options-models', Key='production/label_encoder_clean.pkl')
label_encoder = joblib.loads(encoder_obj['Body'].read())


# Tool 1: Fetch Market Data
@tool
async def fetch_market_data(ticker: str = "SMH") -> dict:
    """
    Fetch current option chain and price history from Massive.com API.
    
    Args:
        ticker: Stock ticker symbol (default: SMH)
    
    Returns:
        Dictionary with option_chain and price_history DataFrames
    """
    # Use Massive.com API (via MCP or direct)
    # For now, simplified version
    import requests
    
    # Fetch option chain
    response = requests.get(
        f"https://api.massive.com/v1/options/chain/{ticker}",
        headers={"Authorization": f"Bearer {os.getenv('MASSIVE_API_KEY')}"}
    )
    option_chain = pd.DataFrame(response.json()['results'])
    
    # Fetch price history (last 200 days)
    response = requests.get(
        f"https://api.massive.com/v1/stocks/{ticker}/history?days=200",
        headers={"Authorization": f"Bearer {os.getenv('MASSIVE_API_KEY')}"}
    )
    price_history = pd.DataFrame(response.json()['results'])
    
    return {
        'option_chain': option_chain.to_dict(),
        'price_history': price_history.to_dict(),
        'current_price': float(price_history.iloc[-1]['close'])
    }


# Tool 2: Extract Features
@tool
def extract_features(market_data: dict, current_date: str) -> dict:
    """
    Extract 84 features from raw market data using our FeatureExtractor.
    
    Args:
        market_data: Dictionary with option_chain and price_history
        current_date: Date for prediction (YYYY-MM-DD)
    
    Returns:
        Dictionary with 84 features ready for ML model
    """
    # Convert back to DataFrames
    option_chain = pd.DataFrame(market_data['option_chain'])
    price_history = pd.DataFrame(market_data['price_history'])
    
    # Extract features using our existing code
    features = feature_extractor.extract_features(
        option_chain=option_chain,
        price_history=price_history,
        current_date=current_date
    )
    
    return features


# Tool 3: Predict Strategy (Stage 1 - ML)
@tool
def predict_strategy(features: dict) -> dict:
    """
    Use ML model to predict optimal options strategy (Stage 1).
    
    Args:
        features: Dictionary with 84 features
    
    Returns:
        Dictionary with strategy name and confidence score
    """
    # Convert features to DataFrame
    feature_df = feature_extractor.get_feature_dataframe(features)
    
    # Predict using our ML model
    prediction = ml_model.predict(feature_df)[0]
    probabilities = ml_model.predict_proba(feature_df)[0]
    
    # Decode strategy name
    strategy = label_encoder.inverse_transform([prediction])[0]
    confidence = float(probabilities[prediction])
    
    # Get top 3 alternatives
    top_3_idx = probabilities.argsort()[-3:][::-1]
    alternatives = [
        {
            'strategy': label_encoder.inverse_transform([idx])[0],
            'confidence': float(probabilities[idx])
        }
        for idx in top_3_idx
    ]
    
    return {
        'strategy': strategy,
        'confidence': confidence,
        'alternatives': alternatives,
        'model_version': 'v1.0',
        'accuracy': 0.8421  # Our validated accuracy
    }


# Tool 4: Generate Parameters (Stage 2 - Rules)
@tool
def generate_parameters(strategy: str, market_data: dict, features: dict) -> dict:
    """
    Generate trade parameters using rules-based logic (Stage 2).
    
    Args:
        strategy: Strategy name from ML prediction
        market_data: Raw market data with option chain
        features: Extracted features
    
    Returns:
        Complete trade specification with strikes, DTE, sizing, etc.
    """
    # Convert option chain back to DataFrame
    option_chain = pd.DataFrame(market_data['option_chain'])
    current_price = market_data['current_price']
    
    # Generate parameters using our existing code
    parameters = parameter_generator.generate(
        strategy=strategy,
        option_chain=option_chain,
        features=features,
        current_price=current_price
    )
    
    # Add risk validation
    if 'max_loss' in parameters and 'max_profit' in parameters:
        max_loss = parameters.get('total_max_loss', parameters.get('max_loss', 0))
        max_profit = parameters.get('total_max_profit', parameters.get('max_profit', 0))
        
        if isinstance(max_profit, str):
            max_profit = max_loss * 3  # Estimate for unlimited profit
        
        validation = risk_manager.validate_trade(max_loss, max_profit)
        parameters['risk_validation'] = validation
    
    return parameters


# Tool 5: Format Recommendation
@tool
def format_recommendation(strategy: dict, parameters: dict, features: dict) -> str:
    """
    Format the complete recommendation for user presentation.
    
    Args:
        strategy: Strategy prediction with confidence
        parameters: Trade parameters
        features: Market features
    
    Returns:
        Formatted recommendation text
    """
    output = f"""
📊 OPTIONS TRADE RECOMMENDATION
{'=' * 60}

🎯 STRATEGY: {strategy['strategy']}
   Confidence: {strategy['confidence']:.1%}
   Model Accuracy: {strategy['accuracy']:.1%}

💰 TRADE PARAMETERS:
"""
    
    # Add strategy-specific details
    if strategy['strategy'] == 'IRON_CONDOR':
        output += f"""
   Put Spread: ${parameters['put_long_strike']:.0f} / ${parameters['put_short_strike']:.0f}
   Call Spread: ${parameters['call_short_strike']:.0f} / ${parameters['call_long_strike']:.0f}
   DTE: {parameters['dte']} days
   Contracts: {parameters['contracts']}
   
   Net Credit: ${parameters['total_credit']:.2f}
   Max Profit: ${parameters['total_max_profit']:.2f}
   Max Loss: ${parameters['total_max_loss']:.2f}
   
   Profit Zone: ${parameters['breakeven_down']:.2f} - ${parameters['breakeven_up']:.2f}
   Risk/Reward: {parameters['risk_reward_ratio']:.2f}
"""
    
    elif strategy['strategy'] in ['LONG_CALL', 'LONG_PUT']:
        output += f"""
   Strike: ${parameters['strike']:.0f}
   DTE: {parameters['dte']} days
   Contracts: {parameters['contracts']}
   
   Cost: ${parameters['total_cost']:.2f}
   Max Loss: ${parameters['max_loss']:.2f}
   Breakeven: ${parameters['breakeven']:.2f}
"""
    
    # Add market conditions
    output += f"""
📈 MARKET CONDITIONS:
   Current Price: ${features['current_price']:.2f}
   IV Rank: {features['iv_rank']:.1f}%
   Trend: {['Strong Down', 'Weak Down', 'Ranging', 'Weak Up', 'Strong Up'][features['trend_regime']]}
   ADX: {features['adx_14']:.1f}
   RSI: {features['rsi_14']:.1f}

✅ RISK VALIDATION:
   Status: {'APPROVED ✅' if parameters['risk_validation']['approved'] else 'REJECTED ❌'}
   Risk/Reward: {parameters['risk_validation']['risk_reward_ratio']:.2f}
   Risk %: {parameters['risk_validation']['risk_percentage']:.2%}
"""
    
    return output
```

#### Step 3: Create the Recommendation Agent

```python
# agents/recommendation_agent.py (continued)

# System prompt for the agent
SYSTEM_PROMPT = """You are an expert options trading recommendation agent.

Your role is to:
1. Fetch current market data for SMH options
2. Extract 84 technical features from the data
3. Use a trained ML model to predict the optimal strategy (84.21% accuracy)
4. Generate specific trade parameters using professional rules
5. Present a complete, actionable trade recommendation

You have access to these tools:
- fetch_market_data(): Get option chain and price history
- extract_features(): Convert raw data to 84 features
- predict_strategy(): ML prediction (Stage 1)
- generate_parameters(): Rules-based parameters (Stage 2)
- format_recommendation(): Format final output

IMPORTANT:
- Always use ALL tools in sequence
- Stage 1 (ML) predicts WHAT strategy
- Stage 2 (Rules) determines HOW to execute
- Never skip the feature extraction step
- Always validate risk before recommending

Your recommendations are used for real trading, so accuracy is critical."""

# Initialize Bedrock model (or any supported model)
model = BedrockModel(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",  # Fast and cheap
    temperature=0.1,  # Low temperature for consistency
    region_name="us-east-1"
)

# Create the Recommendation Agent
recommendation_agent = Agent(
    model=model,
    tools=[
        fetch_market_data,
        extract_features,
        predict_strategy,
        generate_parameters,
        format_recommendation
    ],
    system_prompt=SYSTEM_PROMPT,
    name="RecommendationAgent"
)

print("✅ Recommendation Agent created successfully!")
```

#### Step 4: Use the Agent

```python
# Simple usage
from datetime import datetime

# Generate recommendation
response = recommendation_agent(
    f"Generate today's options trade recommendation for SMH. "
    f"Current date: {datetime.now().strftime('%Y-%m-%d')}"
)

print(response)
```

#### Step 5: Advanced Usage with State

```python
# With user context
response = recommendation_agent(
    "Generate recommendation for SMH",
    user_id="user123",
    account_size=10000,
    risk_tolerance="moderate"
)

# Access state in tools
@tool(context=True)
def generate_parameters_with_context(
    strategy: str, 
    market_data: dict, 
    features: dict,
    tool_context: ToolContext
) -> dict:
    """Generate parameters with user-specific risk settings."""
    
    # Get user preferences from context
    account_size = tool_context.invocation_state.get("account_size", 10000)
    risk_tolerance = tool_context.invocation_state.get("risk_tolerance", "moderate")
    
    # Adjust risk manager
    risk_pct = {
        "conservative": 0.01,
        "moderate": 0.02,
        "aggressive": 0.03
    }[risk_tolerance]
    
    risk_manager = RiskManager(
        account_size=account_size,
        risk_per_trade=risk_pct
    )
    
    param_gen = ParameterGenerator(risk_manager=risk_manager)
    
    # Generate parameters
    return param_gen.generate(...)
```

---

## Deployment Options

### Option 1: AWS Lambda (Serverless)

```python
# lambda_handler.py

import json
from agents.recommendation_agent import recommendation_agent

def lambda_handler(event, context):
    """Lambda handler for recommendation agent."""
    
    # Parse request
    body = json.loads(event['body'])
    ticker = body.get('ticker', 'SMH')
    date = body.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Generate recommendation
    response = recommendation_agent(
        f"Generate options trade recommendation for {ticker} on {date}"
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'recommendation': response,
            'timestamp': datetime.now().isoformat()
        })
    }
```

### Option 2: Local Testing

```python
# test_agent.py

from agents.recommendation_agent import recommendation_agent

if __name__ == "__main__":
    print("Testing Recommendation Agent...")
    
    response = recommendation_agent(
        "Generate today's SMH options recommendation"
    )
    
    print(response)
```

### Option 3: API Server

```python
# api_server.py

from fastapi import FastAPI
from agents.recommendation_agent import recommendation_agent

app = FastAPI()

@app.post("/recommend")
async def get_recommendation(ticker: str = "SMH"):
    """Get options recommendation."""
    
    response = recommendation_agent(
        f"Generate recommendation for {ticker}"
    )
    
    return {"recommendation": response}

# Run: uvicorn api_server:app --reload
```

---

## Key Advantages of Strands

### 1. **Simplicity**
- Just add `@tool` decorator to functions
- Agent handles tool selection automatically
- No complex orchestration code needed

### 2. **Flexibility**
- Use any model (Bedrock, OpenAI, Anthropic, etc.)
- Mix sync and async tools
- Class-based tools for state management

### 3. **Integration with Our Code**
- Our existing modules work as-is
- Just wrap them in `@tool` decorator
- No need to rewrite anything

### 4. **Production Ready**
- Built-in error handling
- Streaming support
- Context management
- Multi-agent patterns

### 5. **Cost Effective**
- Use cheap models (Haiku) for orchestration
- Tools do the heavy lifting (our code)
- Pay only for LLM calls, not compute

---

## Comparison: Our Plan vs Reference Code

| Aspect | Reference (Customer Support) | Our Implementation (Options Trading) |
|--------|------------------------------|-------------------------------------|
| **Tools** | 4 simple tools (policy, product, search, KB) | 5 tools (fetch, extract, predict, generate, format) |
| **Complexity** | Simple lookups | ML model + rules engine |
| **State** | Stateless | Needs market data + model state |
| **Model** | Claude Haiku (cheap) | Claude Haiku (cheap) ✅ |
| **Pattern** | Single agent | Single agent (can expand to multi-agent) |
| **Deployment** | Local notebook | Lambda + EventBridge |

---

## Next Steps

### Phase 1: Local Testing (This Week)
1. Install Strands: `pip install strands-agents`
2. Create `agents/recommendation_agent.py` with tools
3. Test locally with real data
4. Validate output matches our current system

### Phase 2: Lambda Deployment (Next Week)
1. Package agent + dependencies as Lambda layer
2. Upload ML models to S3
3. Create Lambda function
4. Test with EventBridge trigger

### Phase 3: Multi-Agent System (Week 3)
1. Add Risk Agent (validates recommendations)
2. Add Tracking Agent (monitors positions)
3. Add Monitoring Agent (sends alerts)
4. Connect via Strands multi-agent patterns

---

## Cost Estimate

### Per Recommendation
- **Model calls:** ~3-5 calls (tool selection + execution)
- **Claude Haiku:** $0.25 per 1M input tokens, $1.25 per 1M output
- **Average tokens:** ~2K input, ~1K output per call
- **Cost per recommendation:** ~$0.005 (half a cent)

### Monthly Cost (Daily Trading)
- **Trading days:** 21 per month
- **Recommendations:** 21 × $0.005 = $0.105
- **Lambda:** ~$0.20 (free tier covers most)
- **Total:** ~$0.30/month for agent orchestration ✅

**Compare to:** Building custom orchestration = weeks of dev time

---

## Summary

### What I Understand

1. **Strands is a tool orchestration framework** - It uses LLMs to decide which tools to call and in what order
2. **Tools are just Python functions** - Add `@tool` decorator and docstring
3. **Agent = Model + Tools + Instructions** - Simple, clean API
4. **Our code fits perfectly** - Wrap existing modules as tools
5. **Production ready** - Supports Lambda, async, streaming, multi-agent

### How We'll Use It

1. **Wrap our existing code as tools:**
   - FeatureExtractor → `extract_features()` tool
   - ML Model → `predict_strategy()` tool
   - ParameterGenerator → `generate_parameters()` tool

2. **Let Strands orchestrate:**
   - Agent decides when to call each tool
   - Handles errors and retries
   - Formats output

3. **Deploy serverless:**
   - Lambda function with agent
   - EventBridge triggers daily
   - S3 stores models
   - DynamoDB stores results

### Why This Works

- ✅ **No rewriting** - Our code works as-is
- ✅ **Simple** - Just add decorators
- ✅ **Cheap** - $0.005 per recommendation
- ✅ **Scalable** - Serverless architecture
- ✅ **Maintainable** - Clear separation of concerns

Ready to start implementation!

