from fastapi.responses import JSONResponse

def success_response(data, message="Success", status=200):
    return JSONResponse(
        status_code=status,
        content={
            "success": True,
            "message": message,
            "data": data,
            "meta": {}
        }
    )

def error_response(message="An error occurred", status=400):
    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "message": message,
            "data": None,
            "meta": {}
        }
    )