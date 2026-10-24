# Setup Notes

## 1. Project-level urls.py

In your Django project's main `urls.py`, include this app's routes:

```python
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('loans_app.urls')),   # <-- add this line
]
```

## 2. settings.py — MSSQL connection (if this app uses a separate DB from Yashwanth)

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'loans_app',
]

DATABASES = {
    'default': {
        'ENGINE': 'mssql',                     # requires: pip install mssql-django
        'NAME': 'YourLoanDbName',
        'USER': 'your_sql_user',
        'PASSWORD': 'your_password',
        'HOST': 'your_server_or_ip',
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}
```

Install the driver package:
```
pip install mssql-django
```

## 3. Why `managed = False`

Both models point at tables that already exist in your database (`LoanMaster`, `CollData`).
`managed = False` tells Django "don't try to create/alter/drop these tables via migrations" —
it just maps to what's already there. You won't run `makemigrations`/`migrate` for this app.

## 4. Entryno / LoanNo auto-increment

Your DDL doesn't have `IDENTITY(1,1)` on `Entryno` (or `LoanNo`), so the API currently expects
the client (React Native app) to supply these values on create. Two options going forward:

- **Recommended:** Add `IDENTITY(1,1)` to `Entryno` in SQL Server (drop/recreate the column or
  table), then remove `entryno` from the serializer's writable fields so the DB assigns it.
- **Alternative:** Keep it manual, but compute `next entryno = MAX(Entryno) + 1` server-side in
  `perform_create()` before saving — I can add this if you don't want to alter the table.

## 5. Testing the API

Once running:
- `GET  http://localhost:8000/api/loans/` — list loans
- `POST http://localhost:8000/api/loans/` — create loan (send JSON body matching LoanMaster fields)
- `GET  http://localhost:8000/api/loans/101/` — loan detail with nested collections + total_collected
- `GET  http://localhost:8000/api/loans/pending/` — pending amount report
- `POST http://localhost:8000/api/collections/` — add a collection entry (auto-recalculates PendingAmount)
- `GET  http://localhost:8000/api/collections/?loan_no=101` — collection history for one loan
- `GET  http://localhost:8000/api/collections/?coll_date=2026-07-14` — day's collection report

Test with Postman or the built-in DRF browsable API (just open the URLs in a browser while `DEBUG=True`).
