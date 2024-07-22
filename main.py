from fastapi import FastAPI, Form
from starlette.responses import HTMLResponse
from starlette.requests import Request
from starlette.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/result", response_class=HTMLResponse)
async def submit_form(request: Request, name: str = Form(...), departure: str = Form(...),
                      destination: str = Form(...)):
    print(f"Name: {name}")
    print(f"departure: {departure}")
    print(f"destination: {destination}")
    
    return "Data received. Check terminal for output."
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
