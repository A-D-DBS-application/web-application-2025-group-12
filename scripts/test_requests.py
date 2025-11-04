# scripts/test_requests.py
from app import create_app

app = create_app()

with app.test_client() as c:
    for path in ['/', '/my-company']:
        print('\n=== GET', path)
        try:
            r = c.get(path)
            print('STATUS:', r.status_code)
            # print a short excerpt of body
            data = r.get_data(as_text=True)
            print('LENGTH', len(data))
            print(data[:1000])
        except Exception as e:
            import traceback
            traceback.print_exc()
