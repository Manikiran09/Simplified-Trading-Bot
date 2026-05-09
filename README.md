# Simplified Trading Bot

A small Python application for placing orders on the Binance Futures Testnet (USDT-M).

## Features

- MARKET, LIMIT, and STOP_LIMIT orders
- BUY and SELL sides
- Command-line and interactive usage
- Input validation with friendly error messages
- Logging to file and console
- Clean separation between CLI, order logic, validation, and API client code

## Project Structure

```text
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── orders.py
│   ├── validators.py
│   └── logging_config.py
├── cli.py
└── requirements.txt
```

## Requirements

- Python 3.8+
- A Binance Futures Testnet account
- Binance Futures Testnet API key and secret

Testnet base URL used by the app:

```text
https://testnet.binancefuture.com
```

## Setup

1. Clone the repository:

```bash
git clone https://github.com/Manikiran09/Simplified-Trading-Bot.git
cd Simplified-Trading-Bot
```

2. Change into the project directory:

```bash
cd trading_bot
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set your Binance testnet credentials:

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

## Usage

### Market Order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Limit Order

```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 1 --price 2500
```

### Stop-Limit Order

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.001 --price 47000 --stop-price 46500
```

### Interactive Mode

Interactive mode guides you through prompts and menus:

```bash
python cli.py --interactive
```

You can also mix flags with prompts. If a required value is missing, the CLI will ask for it.

## Command-Line Options

- `--symbol` Trading pair such as `BTCUSDT`
- `--side` `BUY` or `SELL`
- `--type` `MARKET`, `LIMIT`, or `STOP_LIMIT`
- `--quantity` Order quantity
- `--price` Required for `LIMIT` and `STOP_LIMIT`
- `--stop-price` Required for `STOP_LIMIT`
- `--interactive` Enable guided prompts and menus
- `--api-key` Provide API key directly
- `--api-secret` Provide API secret directly
- `--log-level` `DEBUG`, `INFO`, `WARNING`, or `ERROR`
- `--log-dir` Directory for log files

## Output

The CLI prints:

- An order request summary
- API response details when the order is placed
- A success or failure message

## Logging

Log files are created in the `logs/` directory. Each run can create a timestamped log file with request, response, and error details.

Example log entries:

```text
2026-05-09 01:21:58 - INFO - Order parameters validated: BTCUSDT BUY MARKET 0.00100000
2026-05-09 01:21:58 - INFO - Placing BUY MARKET order: BTCUSDT x 0.00100000
```

## Validation Rules

- Symbols must be USDT-quoted pairs like `BTCUSDT`
- Quantity must be a valid positive number
- Price must be a valid positive number when required
- Stop-limit orders require both `price` and `stop-price`

If you enter malformed numeric values such as `0.001]`, the CLI will reject them with a validation error instead of crashing.

## Example API Usage

You can also use the library directly:

```python
from trading_bot.bot.client import BinanceClient
from trading_bot.bot.orders import OrderManager

client = BinanceClient(api_key, api_secret)
manager = OrderManager(client)

response = manager.place_market_order("BTCUSDT", "BUY", "0.001")
print(response["orderId"])
```

## Troubleshooting

### Quantity validation error

If you see:

```text
Quantity must be a valid number
```

make sure the value contains only a plain number, for example `0.001`.

### Credentials not found

Set `BINANCE_API_KEY` and `BINANCE_API_SECRET`, or pass `--api-key` and `--api-secret`.

### API-key format invalid

If Binance returns `API Error -2014: API-key format invalid`, the key is usually copied incorrectly or includes extra spaces/newlines.

Check:

- You are using Futures Testnet credentials, not mainnet credentials
- The key was copied exactly from Binance without extra whitespace
- `BINANCE_API_KEY` and `BINANCE_API_SECRET` are both set correctly

If needed, re-paste the credentials into your shell and try again.

### Order rejected by Binance

Check:

- Symbol exists on Futures Testnet
- Quantity and price are within acceptable ranges
- The stop price and limit price are valid for the chosen order type

## Notes

```
2024-05-15 14:30:22 - trading_bot - INFO - __init__:25 - BinanceClient initialized with Testnet
2024-05-15 14:30:23 - trading_bot - DEBUG - client:120 - API Request: POST /fapi/v1/order | Params: {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '0.001', 'timestamp': 1715783423556, 'signature': 'abc123...'}
2024-05-15 14:30:24 - trading_bot - INFO - client:160 - Order placed successfully: 12345
2024-05-15 14:30:24 - trading_bot - INFO - orders:75 - Placing BUY MARKET order: BTCUSDT x 0.001
```

### Sample Limit Order Log
```
2024-05-15 14:35:10 - trading_bot - INFO - validators:140 - Order parameters validated: ETHUSDT BUY LIMIT 1 @2500.00
2024-05-15 14:35:11 - trading_bot - DEBUG - client:120 - API Request: POST /fapi/v1/order | Params: {...}
2024-05-15 14:35:12 - trading_bot - INFO - client:160 - Order placed successfully: 12346
```

---

## Troubleshooting

### "API Key and Secret required"
Make sure you've exported the environment variables or provided them as arguments:
```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

If you pasted a real key or secret into a file, rotate it in Binance Testnet and replace it with placeholders immediately.

### "Connection error"
- Check your internet connection
- Verify the Testnet URL is accessible: `https://testnet.binancefuture.com`
- Check firewall/proxy settings

### "Order placed but not executed"
- For MARKET orders: Order should execute immediately
- For LIMIT orders: Price may not match current market price; check order status
- See logs for order details

### "Invalid symbol"
- Ensure symbol ends with USDT (e.g., BTCUSDT, not BTC)
- Verify the pair exists on Binance Futures Testnet
- Check pair name spelling

---

## Future Enhancements

Potential features for future versions:
- [ ] Add Stop-Limit order type
- [ ] Add OCO (One-Cancels-Other) orders
- [ ] Add TWAP (Time-Weighted Average Price) orders
- [ ] Add Grid trading strategy
- [ ] Web-based UI for order placement
- [ ] Real-time order monitoring dashboard
- [ ] Backtest engine
- [ ] Advanced risk management

---

## Support & Contributions

For issues or suggestions:
1. Check logs in `logs/` directory for detailed error information
2. Enable DEBUG logging for more verbose output
3. Review Binance API documentation: https://binance-docs.github.io/apidocs/futures/en/

---

## License

This project is open source and available under the MIT License.

---

## Disclaimer

⚠️ **TESTNET ONLY**: This application connects to Binance Futures Testnet for testing purposes. Do not use with real trading accounts or real funds without thorough testing and validation.

Always perform adequate testing before deploying to production. Trading involves risk, and you may lose money. Test thoroughly and use appropriate risk management.

---

**Happy Trading! 🚀**
