# ETRMS WebSocket API Examples

This document provides examples of how to use the Enhanced Trading Risk Management System (ETRMS) WebSocket API in different programming languages.

## Python Examples

### Setting Up WebSocket Connection

```python
import asyncio
import json
import websockets

async def connect_to_ws(endpoint):
    """Connect to a WebSocket endpoint and handle messages"""
    uri = f"ws://localhost:8000/api/v1/ws/{endpoint}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {endpoint} WebSocket")
            
            # Send an initial message to keep the connection alive
            await websocket.send("subscribe")
            
            # Continuously listen for messages
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"Received {endpoint} update:", data)
                    
                    # Process the data as needed
                    # Example: Update UI, trigger alerts, etc.
                    
                    # Send a message periodically to keep the connection alive
                    await asyncio.sleep(30)
                    await websocket.send("ping")
                    
                except websockets.exceptions.ConnectionClosed:
                    print(f"Connection to {endpoint} WebSocket closed")
                    break
    except Exception as e:
        print(f"Error connecting to {endpoint} WebSocket: {e}")

# Example usage
async def main():
    # Create tasks for each WebSocket endpoint
    positions_task = asyncio.create_task(connect_to_ws("positions"))
    accounts_task = asyncio.create_task(connect_to_ws("accounts"))
    risk_metrics_task = asyncio.create_task(connect_to_ws("risk-metrics"))
    alerts_task = asyncio.create_task(connect_to_ws("alerts"))
    
    # Wait for all tasks to complete
    await asyncio.gather(
        positions_task,
        accounts_task,
        risk_metrics_task,
        alerts_task
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Handling Real-time Alerts

```python
import asyncio
import json
import websockets
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alerts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("etrms_alerts")

async def monitor_alerts():
    """Connect to the alerts WebSocket and handle circuit breaker alerts"""
    uri = "ws://localhost:8000/api/v1/ws/alerts"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to alerts WebSocket")
            
            # Send an initial message to keep the connection alive
            await websocket.send("subscribe")
            
            # Continuously listen for alert messages
            while True:
                try:
                    message = await websocket.recv()
                    alert = json.loads(message)
                    
                    timestamp = datetime.fromtimestamp(alert.get("triggered_at", 0))
                    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Log the alert
                    logger.warning(
                        f"ALERT at {formatted_time}: {alert.get('description', 'Unknown alert')} "
                        f"for {alert.get('symbol', 'unknown')} on {alert.get('exchange', 'unknown')}"
                    )
                    
                    # Process the alert as needed
                    # Example: Send email/SMS notification, execute additional actions, etc.
                    if alert.get("type") == "circuit_breaker":
                        await handle_circuit_breaker(alert)
                    
                    # Send a message periodically to keep the connection alive
                    await asyncio.sleep(30)
                    await websocket.send("ping")
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.error("Connection to alerts WebSocket closed")
                    break
                except json.JSONDecodeError:
                    logger.error("Received invalid JSON from alerts WebSocket")
                except Exception as e:
                    logger.error(f"Error handling alert: {e}")
    except Exception as e:
        logger.error(f"Error connecting to alerts WebSocket: {e}")
        # Implement reconnection logic here

async def handle_circuit_breaker(alert):
    """Handle a circuit breaker alert"""
    condition_name = alert.get("condition_name", "unknown")
    exchange = alert.get("exchange", "unknown")
    symbol = alert.get("symbol", "unknown")
    context = alert.get("context", {})
    
    logger.info(f"Circuit breaker '{condition_name}' triggered for {symbol} on {exchange}")
    logger.info(f"Context: {json.dumps(context, indent=2)}")
    
    # Example: Perform additional actions based on the circuit breaker type
    if "max_drawdown" in condition_name.lower():
        logger.warning(f"Max drawdown exceeded for {symbol}: {context.get('current_drawdown', 'N/A')}%")
        # Additional actions: Update dashboard, send urgent notification, etc.

if __name__ == "__main__":
    asyncio.run(monitor_alerts())
```

## JavaScript Examples

### Browser-based WebSocket Client

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETRMS WebSocket Example</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { display: flex; flex-wrap: wrap; }
        .box { 
            flex: 1; 
            min-width: 300px; 
            margin: 10px; 
            padding: 15px; 
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .connected { color: green; }
        .disconnected { color: red; }
        pre { background: #f5f5f5; padding: 10px; overflow: auto; }
    </style>
</head>
<body>
    <h1>ETRMS WebSocket Monitor</h1>
    
    <div class="container">
        <div class="box" id="positions-box">
            <h2>Positions</h2>
            <p>Status: <span id="positions-status" class="disconnected">Disconnected</span></p>
            <pre id="positions-data">No data</pre>
        </div>
        
        <div class="box" id="accounts-box">
            <h2>Accounts</h2>
            <p>Status: <span id="accounts-status" class="disconnected">Disconnected</span></p>
            <pre id="accounts-data">No data</pre>
        </div>
        
        <div class="box" id="risk-metrics-box">
            <h2>Risk Metrics</h2>
            <p>Status: <span id="risk-metrics-status" class="disconnected">Disconnected</span></p>
            <pre id="risk-metrics-data">No data</pre>
        </div>
        
        <div class="box" id="alerts-box">
            <h2>Alerts</h2>
            <p>Status: <span id="alerts-status" class="disconnected">Disconnected</span></p>
            <pre id="alerts-data">No data</pre>
            <div id="alerts-list"></div>
        </div>
    </div>
    
    <script>
        // Base URL for WebSocket connections
        const baseUrl = 'ws://localhost:8000/api/v1/ws';
        
        // WebSocket connections
        let websockets = {};
        
        // Function to setup a WebSocket connection
        function setupWebSocket(endpoint) {
            const statusElement = document.getElementById(`${endpoint}-status`);
            const dataElement = document.getElementById(`${endpoint}-data`);
            
            const ws = new WebSocket(`${baseUrl}/${endpoint}`);
            
            ws.onopen = () => {
                console.log(`Connected to ${endpoint} WebSocket`);
                statusElement.textContent = 'Connected';
                statusElement.className = 'connected';
                ws.send('subscribe');
                
                // Setup ping interval to keep connection alive
                websockets[endpoint].pingInterval = setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send('ping');
                    }
                }, 30000);
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log(`Received ${endpoint} update:`, data);
                    
                    // Update the data display
                    dataElement.textContent = JSON.stringify(data, null, 2);
                    
                    // Handle specific data types
                    if (endpoint === 'alerts') {
                        handleAlert(data);
                    }
                } catch (e) {
                    console.error(`Error parsing ${endpoint} data:`, e);
                }
            };
            
            ws.onclose = () => {
                console.log(`Disconnected from ${endpoint} WebSocket`);
                statusElement.textContent = 'Disconnected';
                statusElement.className = 'disconnected';
                
                clearInterval(websockets[endpoint].pingInterval);
                
                // Try to reconnect after a delay
                setTimeout(() => {
                    console.log(`Attempting to reconnect to ${endpoint}...`);
                    setupWebSocket(endpoint);
                }, 5000);
            };
            
            ws.onerror = (error) => {
                console.error(`Error with ${endpoint} WebSocket:`, error);
            };
            
            return ws;
        }
        
        // Function to handle alerts
        function handleAlert(alert) {
            const alertsList = document.getElementById('alerts-list');
            
            // Create alert element
            const alertElement = document.createElement('div');
            alertElement.style.marginBottom = '10px';
            alertElement.style.padding = '10px';
            alertElement.style.border = '1px solid #ffa500';
            alertElement.style.borderRadius = '5px';
            alertElement.style.backgroundColor = '#fff3e0';
            
            // Format timestamp
            const timestamp = new Date(alert.triggered_at * 1000);
            const formattedTime = timestamp.toLocaleString();
            
            // Create alert content
            alertElement.innerHTML = `
                <strong>${formattedTime}</strong>: ${alert.description}<br>
                <strong>Exchange:</strong> ${alert.exchange} | 
                <strong>Symbol:</strong> ${alert.symbol}<br>
                <strong>Action:</strong> ${alert.action_result || 'No action taken'}
            `;
            
            // Add alert to the list (at the top)
            alertsList.insertBefore(alertElement, alertsList.firstChild);
            
            // Limit the number of displayed alerts
            if (alertsList.children.length > 10) {
                alertsList.removeChild(alertsList.lastChild);
            }
        }
        
        // Initialize WebSocket connections
        document.addEventListener('DOMContentLoaded', () => {
            const endpoints = ['positions', 'accounts', 'risk-metrics', 'alerts'];
            
            endpoints.forEach(endpoint => {
                websockets[endpoint] = {
                    connection: setupWebSocket(endpoint),
                    pingInterval: null
                };
            });
        });
    </script>
</body>
</html>
```

### Node.js WebSocket Client

```javascript
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const { format } = require('util');

// Base URL for WebSocket connections
const baseUrl = 'ws://localhost:8000/api/v1/ws';

// Setup logging
const logDirectory = path.join(__dirname, 'logs');
if (!fs.existsSync(logDirectory)) {
    fs.mkdirSync(logDirectory);
}

const logFile = path.join(logDirectory, 'etrms.log');
const alertsFile = path.join(logDirectory, 'alerts.log');

// Function to log messages
function log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `${timestamp} - ${message}\n`;
    
    // Log to console
    console.log(message);
    
    // Append to log file
    fs.appendFileSync(logFile, logMessage);
}

// Function to log alerts
function logAlert(alert) {
    const timestamp = new Date().toISOString();
    const alertMessage = format(
        '%s - ALERT: %s for %s on %s - %s\n',
        timestamp,
        alert.description,
        alert.symbol,
        alert.exchange,
        alert.action_result || 'No action taken'
    );
    
    // Log to console
    console.log('\x1b[33m%s\x1b[0m', alertMessage.trim());
    
    // Append to alerts log file
    fs.appendFileSync(alertsFile, alertMessage);
}

// Function to setup a WebSocket connection
function setupWebSocket(endpoint) {
    log(`Connecting to ${endpoint} WebSocket...`);
    
    const ws = new WebSocket(`${baseUrl}/${endpoint}`);
    
    ws.on('open', () => {
        log(`Connected to ${endpoint} WebSocket`);
        ws.send('subscribe');
        
        // Setup ping interval to keep connection alive
        const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
        
        // Store ping interval
        ws.pingInterval = pingInterval;
    });
    
    ws.on('message', (data) => {
        try {
            const message = JSON.parse(data);
            
            // Handle different message types
            if (endpoint === 'alerts') {
                logAlert(message);
                handleAlert(message);
            } else {
                // Store latest data for each endpoint
                const dataPath = path.join(logDirectory, `${endpoint}-latest.json`);
                fs.writeFileSync(dataPath, JSON.stringify(message, null, 2));
                
                // Log summary of received data
                if (endpoint === 'positions') {
                    const totalValue = message.total_position_value;
                    const totalPnl = message.total_unrealized_pnl;
                    log(`Positions update - Total value: ${totalValue}, Total PnL: ${totalPnl}`);
                } else if (endpoint === 'risk-metrics') {
                    const metrics = message.risk_metrics;
                    log(`Risk metrics update - Total exposure: ${metrics.total_exposure}, Max drawdown: ${metrics.max_drawdown}%`);
                } else {
                    log(`Received ${endpoint} update`);
                }
            }
        } catch (e) {
            log(`Error parsing ${endpoint} data: ${e.message}`);
        }
    });
    
    ws.on('close', () => {
        log(`Disconnected from ${endpoint} WebSocket`);
        clearInterval(ws.pingInterval);
        
        // Try to reconnect after a delay
        setTimeout(() => {
            log(`Attempting to reconnect to ${endpoint}...`);
            setupWebSocket(endpoint);
        }, 5000);
    });
    
    ws.on('error', (error) => {
        log(`Error with ${endpoint} WebSocket: ${error.message}`);
    });
    
    return ws;
}

// Function to handle alerts
function handleAlert(alert) {
    // Example: Implement specific actions based on alert type
    if (alert.type === 'circuit_breaker') {
        // For circuit breaker alerts, you could trigger actions like:
        // - Send notifications (email, SMS, etc.)
        // - Log to a database
        // - Execute additional trading logic
        
        log(`CIRCUIT BREAKER TRIGGERED: ${alert.condition_name}`);
        
        // Example: Different actions based on condition name
        if (alert.condition_name.includes('max_drawdown')) {
            log(`Max drawdown exceeded for ${alert.symbol} - Taking emergency action`);
            // Execute emergency risk mitigation
        } else if (alert.condition_name.includes('volatility')) {
            log(`Unusual volatility detected for ${alert.symbol} - Monitoring closely`);
            // Increase monitoring frequency
        }
    }
}

// Initialize WebSocket connections
function init() {
    log('Starting ETRMS WebSocket client');
    
    const endpoints = ['positions', 'accounts', 'risk-metrics', 'alerts'];
    
    endpoints.forEach(endpoint => {
        setupWebSocket(endpoint);
    });
    
    log('ETRMS WebSocket client initialized');
}

// Start the client
init();
```

## Command-line Monitoring

Here's a simple Python script to monitor ETRMS WebSocket endpoints from the command-line:

```python
import asyncio
import argparse
import json
import websockets
from datetime import datetime
import os
import sys

# ANSI colors for pretty output
COLORS = {
    'reset': '\033[0m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'bold': '\033[1m'
}

# Print colored output
def cprint(message, color='reset', bold=False):
    if sys.platform == 'win32':
        # Windows doesn't support ANSI colors in cmd
        print(message)
    else:
        prefix = COLORS['bold'] if bold else ''
        print(f"{prefix}{COLORS.get(color, '')}{message}{COLORS['reset']}")

async def monitor_endpoint(endpoint, base_url, output_dir=None):
    """Monitor a specific ETRMS WebSocket endpoint"""
    uri = f"{base_url}/{endpoint}"
    
    cprint(f"Connecting to {endpoint} endpoint at {uri}...", 'blue', True)
    
    try:
        async with websockets.connect(uri) as websocket:
            cprint(f"Connected to {endpoint} WebSocket", 'green', True)
            
            # Send initial subscription message
            await websocket.send("subscribe")
            
            # Continuously listen for messages
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Print timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cprint(f"\n[{timestamp}] Received {endpoint} update:", 'cyan')
                    
                    # Handle different endpoint types
                    if endpoint == 'alerts':
                        handle_alert_output(data)
                    elif endpoint == 'positions':
                        handle_position_output(data)
                    elif endpoint == 'risk-metrics':
                        handle_risk_metrics_output(data)
                    elif endpoint == 'accounts':
                        handle_account_output(data)
                    else:
                        # Generic output for other endpoints
                        print(json.dumps(data, indent=2))
                    
                    # Save to file if output directory is specified
                    if output_dir:
                        save_to_file(data, endpoint, output_dir)
                    
                    # Keep the connection alive
                    await asyncio.sleep(30)
                    await websocket.send("ping")
                    
                except websockets.exceptions.ConnectionClosed:
                    cprint(f"Connection to {endpoint} WebSocket closed", 'red')
                    break
                
                except Exception as e:
                    cprint(f"Error processing {endpoint} message: {e}", 'red')
    
    except Exception as e:
        cprint(f"Error connecting to {endpoint} WebSocket: {e}", 'red')

def handle_alert_output(alert):
    """Format and display alert data"""
    timestamp = datetime.fromtimestamp(alert.get("triggered_at", 0))
    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    cprint(f"ALERT: {alert.get('description', 'Unknown alert')}", 'red', True)
    cprint(f"Time: {formatted_time}", 'yellow')
    cprint(f"Exchange: {alert.get('exchange', 'unknown')}", 'yellow')
    cprint(f"Symbol: {alert.get('symbol', 'unknown')}", 'yellow')
    cprint(f"Condition: {alert.get('condition_name', 'unknown')}", 'yellow')
    
    if alert.get('context'):
        cprint("Context:", 'magenta')
        for key, value in alert.get('context', {}).items():
            print(f"  {key}: {value}")
    
    if alert.get('action_result'):
        cprint(f"Action: {alert.get('action_result')}", 'magenta')

def handle_position_output(data):
    """Format and display position data"""
    cprint(f"Total Position Value: {data.get('total_position_value', 0)}", 'green')
    cprint(f"Total Unrealized PnL: {data.get('total_unrealized_pnl', 0)}", 'green')
    
    # Display positions by exchange
    if 'exchanges' in data:
        for exchange, exchange_data in data.get('exchanges', {}).items():
            cprint(f"\nExchange: {exchange}", 'blue', True)
            cprint(f"  Total Value: {exchange_data.get('total_position_value', 0)}", 'cyan')
            cprint(f"  Total PnL: {exchange_data.get('total_unrealized_pnl', 0)}", 'cyan')
            
            # List positions
            if 'positions' in exchange_data:
                cprint("  Positions:", 'white')
                for position in exchange_data.get('positions', []):
                    symbol = position.get('symbol', 'unknown')
                    size = position.get('size', 0)
                    entry_price = position.get('entry_price', 0)
                    current_price = position.get('current_price', 0)
                    pnl = position.get('unrealized_pnl', 0)
                    
                    # Determine color based on PnL
                    color = 'green' if pnl >= 0 else 'red'
                    
                    print(f"    {symbol}: Size: {size}, Entry: {entry_price}, Current: {current_price}, PnL: {COLORS[color]}{pnl}{COLORS['reset']}")

def handle_risk_metrics_output(data):
    """Format and display risk metrics data"""
    metrics = data.get('risk_metrics', {})
    
    cprint("Risk Metrics:", 'magenta', True)
    cprint(f"  Total Exposure: {metrics.get('total_exposure', 0)}", 'white')
    cprint(f"  Max Drawdown: {metrics.get('max_drawdown', 0)}%", 'white')
    cprint(f"  Total PnL: {metrics.get('total_pnl', 0)}", 'white')
    
    # Display exchange-specific metrics
    if 'exchange_metrics' in metrics:
        cprint("\nExchange Metrics:", 'blue')
        for exchange, exchange_metrics in metrics.get('exchange_metrics', {}).items():
            print(f"  {exchange}: {json.dumps(exchange_metrics)}")
    
    # Display symbol-specific metrics
    if 'symbol_metrics' in metrics:
        cprint("\nSymbol Metrics:", 'cyan')
        for symbol, symbol_metrics in metrics.get('symbol_metrics', {}).items():
            print(f"  {symbol}: {json.dumps(symbol_metrics)}")

def handle_account_output(data):
    """Format and display account data"""
    accounts = data.get('accounts', {})
    
    cprint("Account Information:", 'blue', True)
    
    for exchange, account_info in accounts.items():
        cprint(f"\nExchange: {exchange}", 'cyan', True)
        
        for key, value in account_info.items():
            print(f"  {key}: {value}")

def save_to_file(data, endpoint, output_dir):
    """Save data to a file in the specified output directory"""
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{endpoint}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Write the data to the file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Also update the latest file
    latest_filepath = os.path.join(output_dir, f"{endpoint}_latest.json")
    with open(latest_filepath, 'w') as f:
        json.dump(data, f, indent=2)

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='ETRMS WebSocket Monitor')
    parser.add_argument('endpoints', nargs='*', default=['positions', 'accounts', 'risk-metrics', 'alerts'],
                        help='WebSocket endpoints to monitor (default: all)')
    parser.add_argument('--base-url', default='ws://localhost:8000/api/v1/ws',
                        help='Base URL for WebSocket connections')
    parser.add_argument('--output-dir', help='Directory to save output files')
    
    args = parser.parse_args()
    
    # Validate endpoints
    valid_endpoints = ['positions', 'accounts', 'risk-metrics', 'alerts']
    endpoints = [ep for ep in args.endpoints if ep in valid_endpoints]
    
    if not endpoints:
        cprint("No valid endpoints specified. Valid options are: " + ", ".join(valid_endpoints), 'red')
        return
    
    cprint(f"Starting ETRMS WebSocket Monitor", 'green', True)
    cprint(f"Base URL: {args.base_url}", 'blue')
    cprint(f"Monitoring endpoints: {', '.join(endpoints)}", 'blue')
    
    if args.output_dir:
        cprint(f"Saving output to: {args.output_dir}", 'blue')
    
    # Create tasks for each endpoint
    tasks = [monitor_endpoint(endpoint, args.base_url, args.output_dir) for endpoint in endpoints]
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

To use this command-line monitor:

```bash
# Monitor all endpoints
python etrms_monitor.py

# Monitor specific endpoints
python etrms_monitor.py positions alerts

# Specify a custom WebSocket server
python etrms_monitor.py --base-url ws://your-server:8000/api/v1/ws

# Save outputs to a directory
python etrms_monitor.py --output-dir ./etrms_data
``` 