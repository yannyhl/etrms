import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

export default function AIAssistant() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: 'Hello! I\'m your Enhanced Trading Risk Management Assistant. I can help you analyze your positions, evaluate risk, and provide trading insights. How can I assist you today?',
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Sample trading insights for demonstration
  const sampleInsights = [
    "Analyze my BTCUSDT position risk",
    "What's the optimal position size for ETHUSDT with 5% account risk?",
    "Calculate drawdown risk for my current portfolio",
    "Should I reduce my leverage on Binance positions?",
    "Suggest circuit breaker conditions for my portfolio"
  ];

  // Function to handle sending a message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // In a real implementation, this would call our AI API endpoint
      // For now, we'll simulate a response
      setTimeout(() => {
        // Simulate AI response based on user query
        let aiResponse;
        const userQuery = input.toLowerCase();
        
        if (userQuery.includes('btcusdt') && (userQuery.includes('position') || userQuery.includes('risk'))) {
          aiResponse = {
            id: messages.length + 2,
            role: 'assistant',
            content: `Based on your current BTCUSDT long position (0.75 BTC at an entry price of $40,000), I have the following risk analysis:

1. **Current Position**: Your position is currently in profit with an unrealized gain of $1,500 (+5%).

2. **Risk Assessment**:
   - Your position represents 30% of your total position value across exchanges
   - The position has a Value-at-Risk (95% confidence) of approximately $3,600 based on BTC's recent volatility
   - Current liquidation price is estimated at $35,200, giving you a 12% safety buffer

3. **Recommendation**: Your position is within reasonable risk parameters. I recommend setting a trailing stop at $41,000 to protect profits while allowing for further upside.`,
            timestamp: new Date().toISOString()
          };
        } else if (userQuery.includes('position size') && userQuery.includes('ethusdt')) {
          aiResponse = {
            id: messages.length + 2,
            role: 'assistant',
            content: `For ETHUSDT with a 5% account risk tolerance:

1. **Account Calculation**:
   - Your total account equity is $125,000
   - 5% risk equals $6,250

2. **Position Sizing**:
   - Current ETHUSDT price: $2,600
   - Recommended stop loss distance: 7% ($182)
   - Maximum position size based on 5% risk: 34.34 ETH
   - This would be a position value of approximately $89,284

3. **Current Position**: Your current position is 8 ETH, which is well below the maximum risk tolerance.

4. **Recommendation**: You can safely increase your ETHUSDT position up to 34 ETH while maintaining your 5% risk tolerance. I recommend using a scaled entry approach to average in over multiple price levels.`,
            timestamp: new Date().toISOString()
          };
        } else if (userQuery.includes('drawdown')) {
          aiResponse = {
            id: messages.length + 2,
            role: 'assistant',
            content: `I've analyzed your current portfolio's drawdown risk:

1. **Current Portfolio**:
   - Total portfolio value: $125,000
   - Current positions: BTCUSDT (long), ETHUSDT (long)
   - Unrealized P&L: +$5,000 (+4%)

2. **Historical Drawdown Analysis**:
   - Maximum historical correlation between BTC and ETH during market stress: 0.85
   - Based on 1-month VAR at 95% confidence level:
     - Potential maximum drawdown: 14.2% ($17,750)
     - Worst-case 1-day scenario: 7.8% ($9,750)

3. **Recommendations**:
   - Your current position correlation is high, consider diversifying with a negatively correlated asset
   - I recommend setting circuit breakers at 10% portfolio drawdown to trigger automatic risk reduction
   - Consider hedging a portion of your position with an options strategy to limit downside risk`,
            timestamp: new Date().toISOString()
          };
        } else if (userQuery.includes('leverage') && userQuery.includes('binance')) {
          aiResponse = {
            id: messages.length + 2,
            role: 'assistant',
            content: `I've analyzed your Binance positions for leverage optimization:

1. **Current Positions on Binance**:
   - BTCUSDT: 0.75 BTC, 5x leverage, liquidation price $35,200
   - Current volatility: 3.5% daily standard deviation

2. **Leverage Assessment**:
   - Your current effective account leverage is 3.2x
   - The optimal leverage based on the Kelly Criterion for your strategy is 2.5x
   - Current leverage puts you at risk of liquidation during a 14% market correction

3. **Recommendation**: 
   - Reduce your leverage from 5x to 3x to improve position sustainability
   - This would increase your liquidation buffer by 42%
   - Reduced leverage would still provide 75% of current return potential with significantly lower risk
   - Consider setting auto-deleveraging triggers at key technical levels`,
            timestamp: new Date().toISOString()
          };
        } else if (userQuery.includes('circuit breaker') || userQuery.includes('conditions')) {
          aiResponse = {
            id: messages.length + 2,
            role: 'assistant',
            content: `Based on your current portfolio and risk profile, here are my suggested circuit breaker conditions:

1. **Portfolio-wide Circuit Breakers**:
   - **Maximum Drawdown**: 10% portfolio drawdown → Reduce all positions by 30%
   - **Sudden Volatility Spike**: VIX > 30 or 1-hour price change > 5% → Close all leveraged positions

2. **Position-specific Circuit Breakers**:
   - **BTCUSDT Position**: 
     - Drawdown exceeding 8% from entry → Reduce position by 50%
     - Price drops below $38,500 support → Close position
   
   - **ETHUSDT Position**:
     - Drawdown exceeding 10% from entry → Reduce position by 50%
     - ETH/BTC ratio drops below 0.064 → Close position

3. **Technical Triggers**:
   - Price crosses below 20-day moving average → Reduce exposure by 25%
   - RSI below 30 → Activate dollar-cost-averaging buys

I've prepared these circuit breaker templates for you to review. Would you like me to implement any of these in the system directly?`,
            timestamp: new Date().toISOString()
          };
        } else {
          aiResponse = {
            id: messages.length + 2,
            role: 'assistant',
            content: `I'll help you with that. To provide the most accurate insights, I'd need to analyze your current positions and market conditions. 

Here are some examples of what I can help you with:
- Analyze position risk and recommend position sizes
- Calculate optimal stop-loss and take-profit levels
- Suggest risk mitigation strategies
- Evaluate portfolio drawdown risk
- Recommend circuit breaker conditions

Would you like me to analyze any specific positions or risk parameters in your portfolio?`,
            timestamp: new Date().toISOString()
          };
        }
        
        setMessages(prev => [...prev, aiResponse]);
        setIsLoading(false);
      }, 1500);
      
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      
      // Add error message
      setMessages(prev => [...prev, {
        id: messages.length + 2,
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    }
  };

  // Function to insert a sample insight into the input
  const insertSampleInsight = (insight) => {
    setInput(insight);
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <h1 className="mb-4">AI Trading Assistant</h1>
      
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto mb-4 p-4 bg-white rounded-lg shadow">
        <div className="space-y-4">
          {messages.map(message => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[75%] rounded-lg px-4 py-2 ${
                  message.role === 'user'
                    ? 'bg-primary-500 text-white'
                    : 'bg-secondary-100 text-secondary-900'
                }`}
              >
                <div className="whitespace-pre-line">{message.content}</div>
                <div className={`text-xs mt-1 ${message.role === 'user' ? 'text-primary-100' : 'text-secondary-500'}`}>
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-[75%] rounded-lg px-4 py-2 bg-secondary-100">
                <div className="flex space-x-2 items-center">
                  <div className="w-2 h-2 bg-secondary-400 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-secondary-400 rounded-full animate-pulse delay-75"></div>
                  <div className="w-2 h-2 bg-secondary-400 rounded-full animate-pulse delay-150"></div>
                  <span className="text-secondary-500">Analyzing...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      {/* Sample insights */}
      <div className="mb-4 flex flex-wrap gap-2">
        {sampleInsights.map((insight, index) => (
          <button
            key={index}
            onClick={() => insertSampleInsight(insight)}
            className="text-sm bg-secondary-100 hover:bg-secondary-200 text-secondary-800 px-3 py-1 rounded-full"
          >
            {insight}
          </button>
        ))}
      </div>
      
      {/* Input area */}
      <form onSubmit={handleSendMessage} className="flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about position risk, portfolio analysis, or trading recommendations..."
          className="input flex-1"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="btn btn-primary whitespace-nowrap disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
} 