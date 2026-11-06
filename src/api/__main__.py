import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.api.main:get_app", factory=True, host="0.0.0.0", port=8000)  # noqa: S104
