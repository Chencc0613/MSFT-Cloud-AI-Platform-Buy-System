# MSFT Cloud + AI Platform Buy System

Streamlit mobile-first app for a MSFT-only buy/hold decision framework.

## Files

- `streamlit_app.py` — Streamlit UI
- `msft_cloud_ai_buy_system.py` — core model
- `requirements.txt` — deployment dependencies
- `.streamlit/config.toml` — dark mobile-friendly theme

## Local run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Streamlit Community Cloud

1. Upload all files to a GitHub repo.
2. App entry file: `streamlit_app.py`
3. Recommended Python version: 3.11 or 3.12.
4. No `pandas_datareader` / no FRED dependency. Macro uses yfinance market proxies only.

## Manual inputs after earnings

Update in the sidebar:

- Azure Growth YoY %
- Cloud Guidance Surprise %
- Copilot Monetization score
- AI CapEx Efficiency score
- Enterprise Durability score
- Cloud Margin score
- Platform Risk score
- Gaming / PC score

The system is advisory only and never sends orders.
