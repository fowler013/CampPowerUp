# 📡 HTTP Status Codes Reference

> **Purpose:** Quick reference for HTTP status codes used in web development  
> **Last Updated:** March 30, 2026

---

## Overview

HTTP status codes are three-digit responses from a server indicating the result of a request.

| Range | Category | Meaning |
|-------|----------|---------|
| **1xx** | Informational | Request received, continuing process |
| **2xx** | Success | Request successfully received and processed |
| **3xx** | Redirection | Further action needed to complete request |
| **4xx** | Client Error | Request contains bad syntax or cannot be fulfilled |
| **5xx** | Server Error | Server failed to fulfill a valid request |

---

## ✅ 1xx — Informational

| Code | Name | Description |
|------|------|-------------|
| **100** | Continue | Server received request headers, client should proceed with body |
| **101** | Switching Protocols | Server is switching protocols as requested (e.g., to WebSocket) |
| **102** | Processing | Server is processing but no response yet (WebDAV) |
| **103** | Early Hints | Used to return some response headers before final response |

---

## ✅ 2xx — Success

| Code | Name | Description |
|------|------|-------------|
| **200** | OK | Standard success response |
| **201** | Created | Request succeeded and new resource was created |
| **202** | Accepted | Request accepted but not yet processed |
| **203** | Non-Authoritative Info | Response from a proxy, not the origin server |
| **204** | No Content | Success, but no content to return |
| **205** | Reset Content | Success, client should reset the document view |
| **206** | Partial Content | Partial resource returned (used for range requests/downloads) |
| **207** | Multi-Status | Multiple status codes for multiple resources (WebDAV) |
| **208** | Already Reported | Members already enumerated (WebDAV) |

### Common Usage:
```
200 OK              → GET request succeeded, here's the data
201 Created         → POST request succeeded, resource created
204 No Content      → DELETE succeeded, nothing to return
```

---

## 🔀 3xx — Redirection

| Code | Name | Description |
|------|------|-------------|
| **300** | Multiple Choices | Multiple options available for the resource |
| **301** | Moved Permanently | Resource permanently moved to new URL |
| **302** | Found | Resource temporarily at different URL |
| **303** | See Other | Response is at another URI (use GET) |
| **304** | Not Modified | Cached version is still valid |
| **305** | Use Proxy | Must access through proxy (deprecated) |
| **307** | Temporary Redirect | Same as 302 but method must not change |
| **308** | Permanent Redirect | Same as 301 but method must not change |

### Common Usage:
```
301 Moved Permanently  → Old URL, use new one forever
302 Found              → Temporary redirect (login → dashboard)
304 Not Modified       → Use your cached version
```

---

## ❌ 4xx — Client Errors

| Code | Name | Description |
|------|------|-------------|
| **400** | Bad Request | Server cannot process due to client error (malformed syntax) |
| **401** | Unauthorized | Authentication required |
| **402** | Payment Required | Reserved for future use |
| **403** | Forbidden | Server understood but refuses to authorize |
| **404** | Not Found | Resource does not exist |
| **405** | Method Not Allowed | HTTP method not supported for this resource |
| **406** | Not Acceptable | Resource doesn't match Accept headers |
| **407** | Proxy Auth Required | Must authenticate with proxy |
| **408** | Request Timeout | Client took too long to send request |
| **409** | Conflict | Request conflicts with current state (e.g., duplicate) |
| **410** | Gone | Resource permanently deleted (unlike 404) |
| **411** | Length Required | Content-Length header required |
| **412** | Precondition Failed | Precondition in headers not met |
| **413** | Payload Too Large | Request body exceeds server limits |
| **414** | URI Too Long | URL is too long |
| **415** | Unsupported Media Type | Media format not supported |
| **416** | Range Not Satisfiable | Range header cannot be satisfied |
| **417** | Expectation Failed | Expect header cannot be met |
| **418** | I'm a Teapot | April Fools' joke (RFC 2324) 🫖 |
| **421** | Misdirected Request | Request sent to wrong server |
| **422** | Unprocessable Entity | Request well-formed but semantically wrong |
| **423** | Locked | Resource is locked (WebDAV) |
| **424** | Failed Dependency | Request failed due to previous request failure |
| **425** | Too Early | Server unwilling to risk processing early data |
| **426** | Upgrade Required | Client should switch to different protocol |
| **428** | Precondition Required | Origin server requires conditional request |
| **429** | Too Many Requests | Rate limit exceeded |
| **431** | Request Header Fields Too Large | Headers too big |
| **451** | Unavailable For Legal Reasons | Blocked for legal reasons (censorship) |

### Common Usage:
```
400 Bad Request      → Invalid JSON, missing fields
401 Unauthorized     → Not logged in, need to authenticate
403 Forbidden        → Logged in but don't have permission
404 Not Found        → Page/resource doesn't exist
409 Conflict         → Trying to create duplicate resource
422 Unprocessable    → Validation errors (email format wrong, etc.)
429 Too Many Requests → Slow down, rate limited
```

---

## 💥 5xx — Server Errors

| Code | Name | Description |
|------|------|-------------|
| **500** | Internal Server Error | Generic server error |
| **501** | Not Implemented | Server doesn't support the functionality |
| **502** | Bad Gateway | Server got invalid response from upstream |
| **503** | Service Unavailable | Server temporarily overloaded or down |
| **504** | Gateway Timeout | Upstream server didn't respond in time |
| **505** | HTTP Version Not Supported | HTTP version not supported |
| **506** | Variant Also Negotiates | Server configuration error |
| **507** | Insufficient Storage | Server out of storage (WebDAV) |
| **508** | Loop Detected | Infinite loop detected (WebDAV) |
| **510** | Not Extended | Further extensions required |
| **511** | Network Auth Required | Need to authenticate to network (WiFi login) |

### Common Usage:
```
500 Internal Server Error → Something crashed, check logs
502 Bad Gateway           → Upstream server (API, database) is down
503 Service Unavailable   → Server overloaded, try again later
504 Gateway Timeout       → Upstream server too slow
```

---

## 🎮 CampPowerUp Specific Codes

For our gaming server, here's what you'll commonly see:

| Situation | Code | Meaning |
|-----------|------|---------|
| Game loads successfully | 200 | ROM served correctly |
| ROM not found | 404 | ROM file doesn't exist |
| Save file uploaded | 201 | Save created successfully |
| Not logged in | 401 | Need to authenticate |
| Rate limited | 429 | Too many requests, slow down |
| Server error | 500 | Check Docker logs |
| Docker down | 502/503 | Container not running |

---

## 🔧 Debugging Tips

### Check Status Code in Browser:
1. Open **Developer Tools** (F12)
2. Go to **Network** tab
3. Refresh the page
4. Look at **Status** column

### Check Status Code with curl:
```bash
curl -I http://localhost:8888
# Returns headers including status code

curl -w "%{http_code}" http://localhost:8888
# Returns just the status code
```

### Common Fixes:

| Code | Likely Fix |
|------|------------|
| 404 | Check file path, URL spelling |
| 500 | Check server logs: `docker logs <container>` |
| 502 | Start the container: `docker-compose up -d` |
| 503 | Wait and retry, or restart service |
| CORS error | Add CORS headers to server config |

---

## 📚 Additional Resources

- [MDN HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [HTTP Cats](https://http.cat/) — Status codes as cat pictures 🐱
- [HTTP Dogs](https://http.dog/) — Status codes as dog pictures 🐕

---

*Part of the CampPowerUp project documentation*
