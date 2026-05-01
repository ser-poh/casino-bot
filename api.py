from fastapi import FastAPI, HTTPException
from database.db import get_balance, get_inventory, get_top_users

app = FastAPI()

@app.get("/user/{user_id}")
async def get_user_data(user_id: int):
    balance = await get_balance(user_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    items = await get_inventory(user_id)
    return {
        "balance": balance,
        "inventory": [dict(i) for i in items]
    }

@app.get("/top")
async def top_users():
    users = await get_top_users()
    return [dict(u) for u in users]