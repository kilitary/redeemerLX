"""Smoke-test the app end to end (API + UI routes)."""

from fastapi.testclient import TestClient

from main import APP_VERSION, app

print("APP_VERSION:", APP_VERSION)

with TestClient(app) as client:
    # API: list
    r = client.get("/items?limit=5")
    print("GET /items?limit=5 ->", r.status_code, len(r.json()))

    # API: filters
    r = client.get("/items?is_offer=true&limit=50")
    print("GET is_offer=true ->", r.status_code, all(i["is_offer"] for i in r.json()))
    r = client.get("/items?color=red&limit=50")
    print("GET color=red ->", r.status_code, all(i["color"] == "red" for i in r.json()))
    r = client.get("/items?sort=price&order=desc&limit=3")
    print("GET sort=price desc ->", r.status_code, [i["price"] for i in r.json()])
    r = client.get("/items?water_resistant=true&limit=50")
    print("GET water_resistant=true ->", r.status_code, all(i["water_resistant"] for i in r.json()))

    # Filter options
    r = client.get("/ui/filters/options")
    print("UI filter options ->", r.status_code, "colors:", r.json()["colors"][:3])
    r = client.get("/ui/filters/options?color=red")
    print("UI options color=red ->", r.status_code, "colors:", r.json()["colors"])

    # API: full CRUD roundtrip
    r = client.post(
        "/items",
        json={
            "name": "Refactor Test",
            "price": 42.5,
            "color": "green",
            "water_resistant": True,
            "subitems": [{"name": "Bolt", "quantity": 2}],
        },
    )
    print("POST /items ->", r.status_code, r.json().get("id"))
    item_id = r.json()["id"]
    r = client.patch(
        f"/items/{item_id}",
        json={"price": 99.0, "is_proof": True, "water_resistant": False},
    )
    print("PATCH ->", r.status_code, r.json()["price"], r.json()["is_proof"], r.json()["water_resistant"])
    r = client.post(f"/items/{item_id}/subitems", json={"name": "Pad", "quantity": 3})
    print("POST subitem ->", r.status_code, r.json().get("id"))
    sub_id = r.json()["id"]
    r = client.patch(f"/items/{item_id}/subitems/{sub_id}", json={"quantity": 7})
    print("PATCH subitem ->", r.status_code, r.json()["quantity"])
    r = client.delete(f"/items/{item_id}")
    print("DELETE item ->", r.status_code, "(expect 204)")
    r = client.get(f"/items/{item_id}")
    print("GET deleted ->", r.status_code, "(expect 404)")

    # UI routes render (use a real item id from the API)
    some_id = client.get("/items?limit=1").json()[0]["id"]
    for url in [
        "/ui",
        "/ui/items/new",
        f"/ui/items/{some_id}",
        f"/ui/items/{some_id}/edit",
    ]:
        r = client.get(url)
        print("UI", url, "->", r.status_code)

    # UI form flows: invalid input redirects with error, valid creates/updates/deletes
    # (clean up leftovers from any earlier interrupted run)
    for skip in range(0, 1000, 100):
        page = client.get(f"/items?skip={skip}&limit=150").json()
        for stale in page:
            if stale["name"] == "UI Refactor Item":
                client.delete(f"/items/{stale['id']}")
        if not page:
            break
    r = client.post(
        "/ui/items", data={"name": "", "price": "5"}, follow_redirects=False
    )
    print(
        "UI create invalid ->",
        r.status_code,
        r.headers.get("location"),
        "(expect 303 + error)",
    )
    r = client.post(
        "/ui/items",
        data={
            "name": "UI Refactor Item",
            "price": "7.5",
            "color": "green",
            "is_offer": "on",
            "water_resistant": "on",
        },
        follow_redirects=False,
    )
    print(
        "UI create valid ->", r.status_code, r.headers.get("location"), "(expect 303)"
    )
    # Find the created item (last one named "UI Refactor Item")
    created = None
    for skip in range(0, 100000, 100):
        page = client.get(f"/items?sort=id&order=desc&skip={skip}&limit=150").json()
        for i in page:
            if i.get("name") == "UI Refactor Item":
                created = i
        if not page:
            break
    assert created is not None, "created item not found"
    print("  created id:", created["id"], "offer:", created["is_offer"], "water:", created["water_resistant"])
    r = client.post(
        f"/ui/items/{created['id']}",
        data={"name": "UI Refactor Item", "price": "8.0"},
        follow_redirects=False,
    )
    print("UI update ->", r.status_code, r.headers.get("location"), "(expect 303)")
    r = client.post(
        f"/ui/items/{created['id']}/subitems",
        data={"name": "Bracket", "quantity": "4"},
        follow_redirects=False,
    )
    print(
        "UI subitem create ->", r.status_code, r.headers.get("location"), "(expect 303)"
    )
    r = client.post(
        f"/ui/items/{created['id']}/subitems",
        data={"name": "B", "quantity": "zzz"},
        follow_redirects=False,
    )
    print(
        "UI subitem invalid ->",
        r.status_code,
        r.headers.get("location"),
        "(expect 303 + error)",
    )
    r = client.post(f"/ui/items/{created['id']}/delete", follow_redirects=False)
    print("UI delete ->", r.status_code, r.headers.get("location"), "(expect 303)")
    leftover = [
        i
        for i in client.get("/items?q=UI%20Refactor").json()
        if i["name"] == "UI Refactor Item"
    ]
    print("  leftovers:", leftover, "(expect [])")
