from typing import Dict, Any, List
from aiohttp import ClientSession

USER_AGENT = "RideNowBot/1.0 (admin@ridenow.uz)"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"


def parse_address(data: Dict[str, Any]) -> Dict[str, Any]:
    address = data.get("address", {})
    mahalla = (
            address.get("neighbourhood")
            or address.get("suburb")
            or address.get("quarter")
            or address.get("residential")
    )
    shahar_tuman = (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("county")
            or address.get("district")
    )
    viloyat = (
            address.get("state")
            or address.get("region")
            or address.get("province")
    )

    parts = [p for p in [mahalla, shahar_tuman, viloyat] if p]
    full_address = ", ".join(parts) or data.get("display_name", "Noma'lum manzil")

    return {
        "source": "nominatim",
        "display_name": data.get("display_name", ""),
        "mahalla": mahalla,
        "shahar_tuman": shahar_tuman,
        "viloyat": viloyat,
        "full_address": full_address,
        "raw": data,
    }


async def aget_place_from_coords(lat: float, lon: float) -> Dict[str, Any]:
    """
    Koordinatalar orqali manzil ma'lumotlarini olish
    """
    key = f"rev:{lat:.6f}:{lon:.6f}"

    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "addressdetails": 1,
        "zoom": 18,
        "accept-language": "uz",
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        async with ClientSession() as session:
            async with session.get(NOMINATIM_REVERSE, params=params, headers=headers, timeout=10) as resp:
                data = await resp.json()
                result = parse_address(data)
                # Koordinatalarni qo'shamiz
                result.update({
                    "lat": lat,
                    "lon": lon
                })
                return result
    except Exception as e:
        return {
            "source": "error",
            "display_name": f"Location at {lat:.6f}, {lon:.6f}",
            "mahalla": None,
            "shahar_tuman": None,
            "viloyat": None,
            "full_address": f"Koordinatalar: {lat:.6f}, {lon:.6f}",
            "lat": lat,
            "lon": lon,
            "raw": {},
            "error": str(e)
        }


async def aget_coords_from_place(place_name: str, country_codes: str = "uz", limit: int = 1) -> List[
    Dict[str, Any]]:
    """
    Shahar/tuman nomi orqali koordinatalarni olish

    Args:
        place_name: Shahar/tuman nomi (masalan: "Toshkent", "Samarqand")
        country_codes: Qidirish davlat kodlari (masalan: ["uz", "kz"])
        limit: Natijalar soni

    Returns:
        Koordinata va ma'lumotlar ro'yxati
    """
    params = {
        "q": place_name,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": limit,
        "accept-language": "uz",
    }

    # Davlat kodlarini qo'shish
    if country_codes:
        params["countrycodes"] = country_codes

    headers = {"User-Agent": USER_AGENT}

    try:
        async with ClientSession() as session:
            async with session.get(NOMINATIM_SEARCH, params=params, headers=headers, timeout=10) as resp:
                data = await resp.json()

                results = []
                for item in data:
                    result = parse_address(item)
                    result.update({
                        "lat": float(item.get("lat", 0)),
                        "lon": float(item.get("lon", 0)),
                        "importance": float(item.get("importance", 0)),
                        "place_id": item.get("place_id"),
                        "type": item.get("type"),
                        "category": item.get("category")
                    })
                    results.append(result)

                # Importance bo'yicha saralash (yuqori importance birinchi)
                results.sort(key=lambda x: x.get("importance", 0), reverse=True)
                return results

    except Exception as e:
        return [{
            "source": "error",
            "display_name": place_name,
            "mahalla": None,
            "shahar_tuman": None,
            "viloyat": None,
            "full_address": place_name,
            "lat": None,
            "lon": None,
            "error": str(e)
        }]


