from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/products", tags=["recipes"])

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "recipes.json"


class RecipeBase(BaseModel):
    name: str
    category: str
    cook_time: int
    difficulty: str
    ingredients: List[str]


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(RecipeBase):
    pass


def _load_recipes() -> List[dict]:
    import json

    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def _save_recipes(recipes: List[dict]) -> None:
    import json

    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)


def _next_id(recipes: List[dict]) -> int:
    if not recipes:
        return 1
    return max(item["id"] for item in recipes) + 1


def _apply_sort(recipes: List[dict], sorting: Optional[str]) -> List[dict]:
    if sorting not in ("asc", "desc"):
        return recipes
    reverse = sorting == "desc"
    return sorted(recipes, key=lambda item: item["name"].casefold(), reverse=reverse)


@router.get("/")
async def get_recipes(sorting: Optional[str] = Query(None, pattern="^(asc|desc)$")):
    recipes = _load_recipes()
    recipes = _apply_sort(recipes, sorting)
    return {
        "recipes": recipes,
        "total": len(recipes)
    }


@router.get("/search")
async def search_by_category(category: str, sorting: Optional[str] = Query(None, pattern="^(asc|desc)$")):
    recipes = _load_recipes()
    filtered = [item for item in recipes if item["category"].casefold() == category.casefold()]
    filtered = _apply_sort(filtered, sorting)
    return {
        "recipes": filtered,
        "total": len(filtered)
    }


@router.post("/", status_code=201)
async def create_recipe(payload: RecipeCreate):
    recipes = _load_recipes()
    new_item = payload.dict()
    new_item["id"] = _next_id(recipes)
    recipes.append(new_item)
    _save_recipes(recipes)
    return new_item


@router.put("/{recipe_id}")
async def update_recipe(recipe_id: int, payload: RecipeUpdate):
    recipes = _load_recipes()
    for item in recipes:
        if item["id"] == recipe_id:
            item.update(payload.dict())
            _save_recipes(recipes)
            return item
    raise HTTPException(status_code=404, detail="Recipe not found")


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: int):
    recipes = _load_recipes()
    for index, item in enumerate(recipes):
        if item["id"] == recipe_id:
            deleted = recipes.pop(index)
            _save_recipes(recipes)
            return deleted
    raise HTTPException(status_code=404, detail="Recipe not found")
