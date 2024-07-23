from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.requests import Request
from starlette.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request, 
    id: str = Form(...), 
    password: str = Form(...), 
    departure: str = Form(...),
    destination: str = Form(...), 
    min_time: str = Form(...), 
    max_time: str = Form(...), 
    best_time: str = Form(None),
    route: str = Form(...),
    adult_count: str = Form(...),
    child_count: str = Form(...),
    senior_count: str = Form(...),
    severe_disabled_count: str = Form(...),
    mild_disabled_count: str = Form(...),
    seat: str = Form(...),
    train_type: str = Form(...)
):
    context = {
        "departure": departure,
        "destination": destination,
        "min_time": min_time,
        "max_time": max_time,
        "best_time": best_time,
        "route": route,
        "adult_count": adult_count,
        "child_count": child_count,
        "senior_count": senior_count,
        "severe_disabled_count": severe_disabled_count,
        "mild_disabled_count": mild_disabled_count,
        "seat": seat,
        "train_type": train_type
    }
    
    return templates.TemplateResponse("result.html", {"request": request, **context})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
