# API Enhancements - Completed

## Summary

Successfully implemented comprehensive API enhancements for the New Homes Lead Tracker application, focusing on input validation, pagination, search, filtering, and sorting capabilities.

## Changes Implemented

### 1. Input Validation & Sanitization ✅

#### New Validation Enums
- `UserRole`: Validates user roles (super_admin, admin, user)
- `PurchaseTimeline`: Validates purchase timeline values
- `PriceRange`: Validates price range values
- `SortField`: Validates sortable fields
- `SortOrder`: Validates sort order (asc, desc)

#### Helper Functions
- `validate_phone_number()`: Normalizes and validates phone numbers (removes non-digits, ensures 10+ digits)
- `sanitize_string()`: Strips whitespace and enforces maximum length limits

#### Updated Pydantic Models

**UserCreate**:
- Username: 3-50 chars, alphanumeric + underscore/hyphen only, auto-lowercase
- Password: Min 8 chars, must contain letter and number
- Email: EmailStr validation
- Role: Enum-based validation
- Agent ID: Must be > 0

**UserUpdate**:
- Same password validation as UserCreate (when provided)
- Optional field validation
- Role: Enum-based validation

**VisitorCreate**:
- Buyer name: 2-255 chars, sanitized
- Buyer phone: 10-20 chars, normalized (digits only)
- Email: EmailStr validation
- Purchase timeline: Enum-based validation
- Price range: Enum-based validation
- All text fields: Max length enforcement with sanitization
- Notes: Max 2000 chars
- Agent ID: Must be > 0

**NoteCreate**:
- Visitor ID & Agent ID: Must be > 0
- Note: 1-2000 chars, sanitized

**AgentCreate**:
- Name: 2-255 chars, sanitized
- CINC ID: 1-50 chars
- Site: 1-100 chars, sanitized
- Phone: Normalized validation

### 2. Enhanced /visitors Endpoint ✅

#### Pagination
- `page`: Page number (starts at 1, validated)
- `page_size`: Items per page (1-100, default 50)
- Response includes:
  - `total`: Total number of matching records
  - `page`: Current page
  - `page_size`: Items per page
  - `total_pages`: Total available pages

#### Search
- `search`: Free-text search across:
  - Buyer name (LIKE)
  - Buyer phone (LIKE)
  - Buyer email (LIKE)

#### Filters
- `site`: Filter by specific site/community
- `date_from`: Filter by creation date (inclusive, ISO format)
- `date_to`: Filter by creation date (inclusive, ISO format)
- `purchase_timeline`: Filter by purchase timeline (enum values)
- `price_range`: Filter by price range (enum values)
- `cinc_synced`: Filter by CINC sync status (true/false)

#### Sorting
- `sort_by`: Sort field (created_at, buyer_name, site, updated_at)
- `sort_order`: Sort direction (asc, desc)
- Default: Sort by created_at DESC (newest first)

#### Authorization
- Users: Only see visitors where `capturing_agent_id` matches their `agent_id`
- Admins/Super Admins: See all visitors
- All filters respect role-based access control

### 3. Bug Fixes ✅

#### Fixed Deprecated datetime.utcnow()
- Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`
- Updated in `create_access_token()` function
- Now compatible with Python 3.12+

## API Usage Examples

### Basic Pagination
```bash
GET /visitors?page=1&page_size=25
```

### Search for Specific Lead
```bash
GET /visitors?search=john&page=1
```

### Filter by Site and Date Range
```bash
GET /visitors?site=Cedar%20Creek&date_from=2025-01-01&date_to=2025-01-31
```

### Filter by Purchase Timeline and Price Range
```bash
GET /visitors?purchase_timeline=0-3%20months&price_range=$300k-$400k
```

### Sort by Buyer Name (Ascending)
```bash
GET /visitors?sort_by=buyer_name&sort_order=asc
```

### Complex Query Example
```bash
GET /visitors?site=Cedar%20Creek&search=smith&date_from=2025-01-01&purchase_timeline=0-3%20months&sort_by=created_at&sort_order=desc&page=1&page_size=50
```

### Filter by CINC Sync Status
```bash
GET /visitors?cinc_synced=false&page=1
```

## Response Format

### Visitors List Response
```json
{
  "visitors": [
    {
      "id": 1,
      "buyer_name": "John Smith",
      "buyer_phone": "5551234567",
      "buyer_email": "john@example.com",
      "purchase_timeline": "0-3 months",
      "price_range": "$300k-$400k",
      "site": "Cedar Creek",
      "agent_name": "Jane Doe",
      "created_at": "2025-01-15T10:30:00",
      "cinc_synced": true,
      ...
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 50,
  "total_pages": 4
}
```

## Validation Error Examples

### Invalid Password
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must contain at least one number",
      "type": "value_error"
    }
  ]
}
```

### Invalid Phone Number
```json
{
  "detail": [
    {
      "loc": ["body", "buyer_phone"],
      "msg": "Phone number must be at least 10 digits",
      "type": "value_error"
    }
  ]
}
```

### Invalid Purchase Timeline
```json
{
  "detail": [
    {
      "loc": ["body", "purchase_timeline"],
      "msg": "value is not a valid enumeration member; permitted: '0-3 months', '3-6 months', '6-12 months', '12+ months', 'Just browsing'",
      "type": "type_error.enum"
    }
  ]
}
```

## Performance Considerations

1. **Pagination**: Limits query results to prevent large data transfers
2. **Indexed Fields**: Queries use indexed columns (phone, email, site, created_at)
3. **Role-based Filtering**: Applied at database level for efficiency
4. **Parameter Validation**: Failed requests rejected before hitting database

## Security Improvements

1. **Input Sanitization**: All user inputs trimmed and length-limited
2. **Phone Normalization**: Strips formatting to prevent inconsistencies
3. **Enum Validation**: Restricts values to predefined sets
4. **SQL Injection Protection**: Parameterized queries with proper escaping
5. **Password Strength**: Enforced minimum complexity requirements

## Next Steps (Remaining Tasks)

### Frontend Integration
- Update JavaScript to use new pagination parameters
- Add UI controls for search, filters, and sorting
- Display pagination controls with page numbers
- Show total results count

### Additional API Enhancements
- Add visitor editing endpoint (PUT /visitors/{id})
- Add visitor deletion endpoint (DELETE /visitors/{id})
- Add bulk operations endpoint
- Add export with filters

### Testing
- Write pytest unit tests for validation
- Test pagination edge cases
- Test search and filter combinations
- Test role-based access control

## Notes

- All enum values are case-sensitive
- Phone numbers are stored as digits only (normalized)
- Usernames are converted to lowercase automatically
- Date filters use SQLite's DATE() function for day-level precision
- Search is case-insensitive (SQLite LIKE)

## Backward Compatibility

⚠️ **Breaking Changes**:
1. `/visitors` endpoint now returns different response format (includes pagination metadata)
2. `limit` and `offset` parameters replaced with `page` and `page_size`
3. Default sort changed to DESC (was DESC already, but now explicit)

**Migration Guide**:
- Replace `limit` with `page_size`
- Replace `offset` with calculated page: `page = (offset / page_size) + 1`
- Update frontend to parse new response structure
- Access visitors array via `response.visitors` instead of `response.visitors`
- Access count via `response.total` instead of `response.count`
