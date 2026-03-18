import requests
import json
import time
from datetime import datetime, timedelta
from utils.memory_store import memory_store


def normalize_filters(obj):
    """
    Converts UI filter structure into Helpshift API format
    """
    if not isinstance(obj, dict):
        return obj

    result = {}

    for op in ("and", "or", "nor"):
        items = obj.get(op)
        if not items:
            continue

        values = []
        exists = None

        for it in items:
            if isinstance(it, dict):
                values.append(it["val"])
                exists = it.get("exists", "true")
            else:
                values.append(it)

        if values:
            result[op] = values
            if exists:
                result["exists"] = exists

    return result


def fetch_issues(api_key, domain, params):
    """
    Fetch issues from Helpshift API with automatic rate-limit handling.
    - Removes empty params
    - Serializes dict/list params to JSON
    - Uses Helpshift rate-limit headers to avoid 429
    - Retries automatically if rate-limited
    """

    base_url = f"https://api.helpshift.com/v1/{domain}/issues"


    filtered_params = {}

    use_paging = "page" in params or "page-size" in params

    for k, v in params.items():
        if v in (None, "", {}, []):
            continue

        if k in ("tags", "languages","notes","feedback-comment"):
            filtered_params[k] = json.dumps(normalize_filters(v))

        elif k == "custom_fields":
            filtered_params[k] = json.dumps(v)   

        elif k == "feedback-rating":
            filtered_params[k] = json.dumps(v)

        elif k == "ids[issue]":
            ids = v.get("or", []) if isinstance(v, dict) else v
            ids = [int(x) for x in ids if str(x).isdigit()]
            if ids:
                filtered_params["ids"] = json.dumps(ids)
                use_paging = True 

        elif k == "state":
            filtered_params[k] = ",".join(v)

        elif k in ("end-user-ids"):
                filtered_params[k] = json.dumps(v)

        elif k in ("includes","excludes", "app-ids", "queue_ids", "platform-types","issue_modes","author_emails", "assignee_emails"):
            filtered_params[k] = json.dumps(v)

        else:
            filtered_params[k] = v





    print(f"Fetching issues with params: {filtered_params}")

    max_retries = 5
    retry_count = 0

    while True:
        try:
            response = requests.get(
                base_url,
                params=filtered_params,
                auth=(api_key, "")
            )
            print("url called: ", response.url)
            if response.status_code == 429:

                retry_after = int(response.headers.get("X-Rate-Limit-Reset", 30))
                print(f"[429] Rate limit exceeded. Retrying in {retry_after} seconds...")
                time.sleep(retry_after)
                retry_count = 0  # Reset on successful backoff
                continue

            # Retry on 5xx server errors (502, 503, 504, etc.)
            if 500 <= response.status_code < 600:
                retry_count += 1
                if retry_count > max_retries:
                    print(f"[{response.status_code}] Max retries ({max_retries}) exceeded. Giving up.")
                    response.raise_for_status()
                backoff = min(2 ** retry_count, 60)  # Exponential backoff capped at 60s
                print(f"[{response.status_code}] Server error. Retrying in {backoff}s... (attempt {retry_count}/{max_retries})")
                time.sleep(backoff)
                continue

            response.raise_for_status()

            remaining = int(response.headers.get("X-Rate-Limit-Remaining", "999999"))
            

            reset_at = int(response.headers.get("X-Rate-Limit-Reset", "0")) / 1000  # ms → seconds
            now = time.time()
            sleep_for = max(0, reset_at - now)

            SAFETY_THRESHOLD = 300
            if remaining < SAFETY_THRESHOLD:
                print(f"[Rate Limit Warning] Sleeping {int(sleep_for)}s until reset…")
                # Notify frontend that we're waiting
                wait_until_timestamp = now + sleep_for
                memory_store.set_progress(status="rate-limited", wait_until=int(wait_until_timestamp))
                time.sleep(sleep_for)
                # Resume fetching
                memory_store.set_progress(status="fetching", wait_until=None)

            retry_count = 0  # Reset on success
            return response.json()

        except requests.HTTPError as e:
            print("HTTP error fetching issues:", e)
            raise

        except Exception as e:
            print("Unexpected error fetching issues:", e)
            raise


def fetch_apps(domain, api_key):
    
    """Fetch apps from Helpshift for the given domain."""
    url = f"https://api.helpshift.com/v1/{domain}/apps"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    print("Fetched Apps:", data)
    return data


def fetch_queues(domain, api_key):
    
    """Fetch queue from Helpshift for the given domain."""
    url = f"https://api.helpshift.com/v1/{domain}/queues"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    print("Fetched Queues:", data)
    return data


def datechunk(start_ms, end_ms, granularity_days=7):
    """
    Splits a date range [start_ms, end_ms] into smaller chunks.
    
    Args:
        start_ms: Start timestamp in milliseconds (unix time)
        end_ms: End timestamp in milliseconds (unix time)
        granularity_days: Size of each chunk in days (default 7)
    
    Returns:
        (sdate_list, edate_list): Two parallel lists of chunk boundaries in milliseconds
    
    Example:
        sdate, edate = datechunk(1512345000000, 1512355000000, 7)
        # sdate = [1512345000000, ...]
        # edate = [..., 1512355000000]
    """
    sdate = []
    edate = []
    
    current_start = start_ms
    
    while current_start < end_ms:
        sdate.append(current_start)
        # Add granularity_days worth of milliseconds
        chunk_end = current_start + (granularity_days * 24 * 60 * 60 * 1000)
        # Cap at end_ms
        chunk_end = min(chunk_end, end_ms)
        edate.append(chunk_end)
        current_start = chunk_end
    
    return sdate, edate


def paginated_fetch(api_key, domain, api_params, total_pages, all_issues, progress_callback=None):
    """
    Fetch paginated results for a given api_params set.
    Iterates from page 1 to total_pages, appending issues to all_issues.
    
    Args:
        api_key: Helpshift API key
        domain: Helpshift domain
        api_params: Base API parameters (will be modified with page numbers)
        total_pages: Total number of pages to fetch
        all_issues: List to append fetched issues into
        progress_callback: Optional callable to update progress. Called as progress_callback(fetched_count)
    
    Raises:
        Exception: If fetch_issues fails
    """
    for page in range(1, total_pages + 1):
        api_params["page"] = page
        response = fetch_issues(api_key, domain, api_params)
        issues = response.get("issues", [])
        
        if issues:
            all_issues.extend(issues)
            print(f"Fetched page {page}/{total_pages}: {len(issues)} issues")
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback(len(all_issues))
        else:
            print(f"Page {page} returned no issues, stopping")
            break


def fetch_issues_with_chunking(api_key, domain, api_params, all_issues, 
                               start_ts_ms, end_ts_ms, threshold_pages=50, granularity_days=7, progress_callback=None):
    """
    Smart issue fetching with automatic date-range chunking for large result sets.
    
    - Fetches initial request to check total pages
    - If total_pages <= threshold_pages: fetches all pages normally
    - If total_pages > threshold_pages: splits date range into chunks and fetches each
    
    Args:
        api_key: Helpshift API key
        domain: Helpshift domain
        api_params: Base API parameters (created-since/created-until will be added)
        all_issues: List to append fetched issues into
        start_ts_ms: Start timestamp in milliseconds
        end_ts_ms: End timestamp in milliseconds
        threshold_pages: Page count threshold above which to chunk (default 50)
        granularity_days: Chunk size in days when splitting (default 7)
        progress_callback: Optional callable to update progress. Called as progress_callback(fetched_count)
    
    Returns:
        None (modifies all_issues in-place)
    
    Raises:
        Exception: If any fetch fails (propagates from fetch_issues)
    """
    params = api_params.copy()
    params["created-since"] = start_ts_ms
    params["created-until"] = end_ts_ms
    
    # Check initial page count
    print(f"[Chunking] Checking page count for range {start_ts_ms}–{end_ts_ms}")
    response = fetch_issues(api_key, domain, params)
    total_pages = int(response.get("total-pages", 1))
    print(f"[Chunking] Total pages: {total_pages} (threshold: {threshold_pages})")
    
    if total_pages > threshold_pages:
        # Split into chunks
        print(f"[Chunking] Large range detected ({total_pages} pages). Splitting into {granularity_days}-day chunks...")
        sdate, edate = datechunk(start_ts_ms, end_ts_ms, granularity_days)
        
        for i, (chunk_start, chunk_end) in enumerate(zip(sdate, edate)):
            print(f"[Chunking] Processing chunk {i+1}/{len(sdate)}: {chunk_start}–{chunk_end}")
            params_chunk = api_params.copy()
            params_chunk["created-since"] = chunk_start
            params_chunk["created-until"] = chunk_end
            
            response_chunk = fetch_issues(api_key, domain, params_chunk)
            chunk_total_pages = int(response_chunk.get("total-pages", 1))
            paginated_fetch(api_key, domain, params_chunk, chunk_total_pages, all_issues, progress_callback)
    else:
        # Fetch normally
        print(f"[Chunking] Small range ({total_pages} pages). Fetching normally.")
        paginated_fetch(api_key, domain, params, total_pages, all_issues, progress_callback)














        