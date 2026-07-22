# SOKOL-TRADER AUDIT REPORT — /radar Bug Investigation

## Executive Summary
Investigated why `/radar` command returns fixed prices instead of real-time data from T-Invest API.

## Investigation Results

### ✅ What Was Checked

1. **Hardcoded Price Values** - Searched for specific values (250.50, 160.25, 3800.00, 6500.00, 550.00)
   - **Result**: NOT FOUND in codebase
   - Only match was in `install_deps.ps1` (unrelated comment about fallback client)

2. **Stubs/Mocks/Fallbacks** - Searched for default_price, mock_price, stub, fallback, cached_price
   - **Result**: NOT FOUND
   - No hardcoded fallback mechanisms

3. **_build_radar_text() Function** (telegram_bot.py lines 90-115)
   - **Result**: CODE LOOKS CORRECT
   - Properly calls `client.get_current_price(ticker)` for each ticker
   - Handles errors gracefully (shows "Н/Д" on error)
   - No hardcoded values

4. **get_current_price() Function** (tinkoff_client.py lines 154-174)
   - **Result**: CODE LOOKS CORRECT
   - Makes real API call to Tinkoff GetLastPrices endpoint
   - Returns 0.0 on error (not hardcoded prices)
   - No stub data

5. **REST Fallback Client**
   - **Result**: NOT FOUND
   - No `tinkoff_client_rest.py` exists

6. **Database (sokol_lab.db)**
   - **Result**: Only 'signals' table exists
   - No price storage tables

7. **Cache Files**
   - **Result**: No .cache, .pkl, or price-related files found
   - No persistent price storage

8. **FIGI Cache** (tinkoff_client.py)
   - **Result**: In-memory only, per-instance
   - Cleared when new TinkoffClient() is created
   - Each `/radar` call creates new client with empty cache

9. **Proxy Configuration**
   - **Result**: SOCKS5 proxy configured in telegram_bot.py line 25
   - Could potentially cache responses, but unlikely to return fixed values

10. **Deployment**
    - **Result**: Docker-based deployment
    - Docker not running on local machine

## Root Cause Analysis

### Most Likely Causes

1. **TINKOFF_MODE = sandbox**
   - Config shows default is "sandbox" mode
   - Sandbox API may return static/test data instead of real market prices
   - **Action Required**: Check `.env` file and set `TINKOFF_MODE=production`

2. **Proxy Caching**
   - SOCKS5 proxy at `138.219.75.204:9119` might be caching API responses
   - **Action Required**: Test without proxy or use different proxy

3. **Server-Side Old Code**
   - If bot is deployed on server, it might be running old code version
   - **Action Required**: Rebuild and redeploy Docker container

4. **T-Invest API Rate Limiting/Caching**
   - API might be returning cached data due to rate limits
   - **Action Required**: Check API response headers and logs

## Recommended Actions

### Immediate (High Priority)
1. Check `.env` file for `TINKOFF_MODE` setting
2. If set to "sandbox", change to "production" and restart
3. Check if bot is deployed and rebuild Docker container:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

### Secondary (Medium Priority)
1. Test API directly without proxy
2. Add logging to `get_current_price()` to see actual API responses
3. Check server logs for radar-related errors

### Code Improvements (Low Priority)
1. Add cache-busting headers to API requests
2. Add price timestamp validation
3. Add fallback to different data source if API returns stale data

## Conclusion

**No hardcoded prices found in codebase.** The issue is likely:
- Configuration (sandbox mode)
- Proxy caching
- Server running old code
- API-level caching

The code itself is correct and should return real-time prices when properly configured.
