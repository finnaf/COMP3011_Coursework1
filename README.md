# Running the Server
## Locally
Install the dependencies and run the server on the local machine with
```
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Through Render
This coursework is using the free tier of Render. The instance spins down after 15 minutes of inactivity, so allow 1 minute if no request has been made recently.
```
https://comp3011-coursework1-vdc3.onrender.com/outflows/?watercourse=River%20Tove
```