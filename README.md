# Dependencies
Dependencies are listed in `requirements.txt`. To install with pip:
```
pip install -r requirements.txt
```

# Running the Server
## Locally
After installing all required dependencies, run the server with
```
uvicorn app.main:app --reload
```

## Through Render
This coursework is using the free tier of Render. The instance spins down after 15 minutes of inactivity, so allow 1 minute if no request has been made recently.
```
https://comp3011-coursework1-vdc3.onrender.com/
```

# Testing
From the root of the project run
```
pytest test_api.py -v
```