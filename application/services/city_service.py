from typing import Dict, Any, List, Optional
from .base import BaseService


class CityServiceAPI(BaseService):
    async def get(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all cities with pagination"""
        return await self._request(
            "GET",
            f"/cities/?page={page}&page_size={page_size}"
        )

    async def get_all_cities(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all cities with pagination"""
        return await self._request(
            "GET",
            f"/cities/?page={page}&page_size={page_size}"
        )

    async def get_title_category(self, lang: str = "uz") -> List[List[str]]:
        """Get allowed cities with translations"""
        result = await self.get()
        cities = []
        for city in result["results"]:
            if city["is_allowed"] and city["subcategory"] is None:
                cities.append([city['title'], city["translate"][lang]])
        return cities

    async def get_translate(self, city_name: str, lang: str) -> Optional[str]:
        """Get translation for a specific city"""
        result = await self.get()
        for city in result["results"]:
            if city["is_allowed"] and city["title"] == city_name:
                return city["translate"][lang]
        return None

    async def check_location_in_allowed_city(
            self,
            latitude: float,
            longitude: float,
            max_distance_km: float = 10.0
    ) -> Dict[str, Any]:
        """
        Check if coordinates are within any ALLOWED city area

        Returns:
            {
                "success": True/False,
                "city_name": "Tashkent",  # agar topilsa
                "city_data": {...},       # shahar ma'lumotlari
                "error": "error_type",    # agar xato bo'lsa
                "message": "Description"
            }
        """
        try:
            # 1. Check location using the API endpoint
            location_result = await self._request(
                "POST",
                "/cities/check-location/",
                json={
                    "latitude": latitude,
                    "longitude": longitude,
                    "max_distance_km": max_distance_km
                }
            )

            # 2. Check if location is in a city and the city is allowed
            if location_result.get("is_in_city", False):
                city_data = location_result.get("city", {})
                city_name = city_data.get("title")

                if city_name:
                    # Verify that the city exists and is allowed in our database
                    city_exists = await self._check_city_exists_and_allowed(city_name)

                    if city_exists:
                        return {
                            "success": True,
                            "city_name": city_name,
                            "city_data": city_data,
                            "distance_km": location_result.get("distance_km"),
                            "address_info": location_result.get("address_info", {}),
                            "message": f"Location is within {city_name} city area"
                        }
                    else:
                        return {
                            "success": False,
                            "error": "city_not_allowed",
                            "city_name": city_name,
                            "message": f"City '{city_name}' is not allowed in our system",
                            "details": location_result
                        }

            # 3. Location not in any city, check nearest city
            elif location_result.get("city"):
                nearest_city = location_result.get("city", {})
                city_name = nearest_city.get("title")

                if city_name and await self._check_city_exists_and_allowed(city_name):
                    return {
                        "success": False,
                        "error": "outside_city_limits",
                        "nearest_city": city_name,
                        "distance_km": location_result.get("distance_km"),
                        "message": f"Location is outside city limits. Nearest allowed city: {city_name} ({location_result.get('distance_km', 0):.1f} km away)"
                    }

            # 4. No cities found
            return {
                "success": False,
                "error": "no_city_found",
                "message": "No allowed cities found near this location",
                "details": location_result
            }

        except Exception as e:
            return {
                "success": False,
                "error": "location_check_failed",
                "message": f"Location check failed: {str(e)}"
            }

    async def _check_city_exists_and_allowed(self, city_name: str) -> bool:
        """Check if city exists and is allowed in our database"""
        try:
            # Search for the city in our database
            cities = await self._request("GET", f"/cities/search-by-name/?name={city_name}")

            if isinstance(cities, list):
                for city in cities:
                    if (city.get("city", {}).get("title", "").lower() == city_name.lower() and
                            city.get("city", {}).get("is_allowed", False)):
                        return True

            # Alternative: get all cities and check
            all_cities = await self.get_all_cities()
            for city in all_cities.get("results", []):
                if city.get("title", "").lower() == city_name.lower() and city.get("is_allowed", False):
                    return True

            return False

        except Exception:
            return False

    async def validate_city_for_location(
            self,
            latitude: float,
            longitude: float,
            expected_city: str = None
    ) -> Dict[str, Any]:
        """
        Validate location against a specific city or find which city it belongs to

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            expected_city: Optional expected city name to validate against

        Returns:
            Validation result with city information
        """
        # First check if location is in any allowed city
        location_check = await self.check_location_in_allowed_city(latitude, longitude)

        if location_check["success"]:
            found_city = location_check["city_name"]

            # If expected city is provided, check if it matches
            if expected_city:
                if found_city.lower() == expected_city.lower():
                    return {
                        "success": True,
                        "valid": True,
                        "city_name": found_city,
                        "message": f"Location successfully validated for {expected_city}",
                        "match_type": "exact"
                    }
                else:
                    return {
                        "success": True,
                        "valid": False,
                        "expected_city": expected_city,
                        "found_city": found_city,
                        "message": f"Location belongs to {found_city}, not {expected_city}",
                        "match_type": "mismatch"
                    }

            # No expected city provided, just return the found city
            return {
                "success": True,
                "valid": True,
                "city_name": found_city,
                "message": f"Location belongs to {found_city}",
                "match_type": "found"
            }

        else:
            # Location not in any allowed city
            if expected_city:
                return {
                    "success": False,
                    "valid": False,
                    "expected_city": expected_city,
                    "message": f"Location is not within {expected_city} or any other allowed city area",
                    "error": location_check.get("error"),
                    "details": location_check
                }
            else:
                return {
                    "success": False,
                    "valid": False,
                    "message": "Location is not within any allowed city area",
                    "error": location_check.get("error"),
                    "details": location_check
                }

    async def is_city_allowed(self, city_name: str) -> bool:
        """Check if a city is allowed in our system"""
        result = await self.get()
        for city in result["results"]:
            if city["title"].lower() == city_name.lower():
                return city["is_allowed"]
        return False

    async def get_city_by_id(self, city_id: int) -> Dict[str, Any]:
        """Get specific city by ID"""
        return await self._request("GET", f"/cities/{city_id}/")

    async def search_cities(self, search_query: str, lang: str = "uz") -> List[Dict[str, Any]]:
        """Search cities by name"""
        result = await self.get()
        matching_cities = []
        for city in result["results"]:
            if (search_query.lower() in city["title"].lower() or
                    search_query.lower() in city["translate"][lang].lower()):
                matching_cities.append({
                    "id": city["id"],
                    "title": city["title"],
                    "translated_title": city["translate"][lang],
                    "is_allowed": city["is_allowed"],
                    "subcategory": city["subcategory"]
                })
        return matching_cities

    async def get_allowed_cities(self, lang: str = "uz") -> List[Dict[str, Any]]:
        """Get only allowed cities"""
        result = await self.get()
        allowed_cities = []
        for city in result["results"]:
            if city["is_allowed"]:
                allowed_cities.append({
                    "id": city["id"],
                    "title": city["title"],
                    "translated_title": city["translate"][lang],
                    "subcategory": city["subcategory"]
                })
        return allowed_cities


    async def get_cities_by_subcategory(self, subcategory: str, lang: str = "uz") -> List[Dict[str, Any]]:
        """Get cities by subcategory"""
        result = await self.get()
        subcategory_cities = []
        for city in result["results"]:
            if city["subcategory"] == subcategory and city["is_allowed"]:
                subcategory_cities.append({
                    "id": city["id"],
                    "title": city["title"],
                    "translated_title": city["translate"][lang]
                })
        return subcategory_cities

    async def check_location(self, latitude: float, longitude: float, max_distance_km: float = 10.0) -> Dict[str, Any]:
        """Check if coordinates are within any city area"""
        return await self._request(
            "POST", 
            "/cities/check-location/", 
            json={
                "latitude": latitude,
                "longitude": longitude,
                "max_distance_km": max_distance_km
            }
        )

    async def validate_city_location(self, city_name: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Validate if city name matches coordinates"""
        return await self._request(
            "POST", 
            "/cities/validate-city-location/", 
            json={
                "city_name": city_name,
                "latitude": latitude,
                "longitude": longitude
            }
        )

    async def get_nearby_cities(self, latitude: float, longitude: float, max_distance_km: float = 50.0) -> List[Dict[str, Any]]:
        """Get cities near specified location"""
        return await self._request(
            "POST",
            "/cities/nearby-cities/",
            json={
                "latitude": latitude,
                "longitude": longitude,
                "max_distance_km": max_distance_km
            }
        )

    async def get_city_location_info(self, city_id: int) -> Dict[str, Any]:
        """Get location info for a specific city"""
        return await self._request("GET", f"/cities/{city_id}/location-info/")

    async def search_cities_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Search cities by name and get coordinates"""
        return await self._request("GET", f"/cities/search-by-name/?name={name}")

    async def bulk_get_translations(self, city_names: List[str], lang: str = "uz") -> Dict[str, str]:
        """Get translations for multiple cities at once"""
        result = await self.get()
        translations = {}
        for city in result["results"]:
            if city["is_allowed"] and city["title"] in city_names:
                translations[city["title"]] = city["translate"][lang]
        return translations

    async def get_city_coordinates(self, city_name: str) -> Optional[Dict[str, float]]:
        """Get coordinates for a specific city"""
        result = await self.get()
        for city in result["results"]:
            if city["title"] == city_name and city["is_allowed"]:
                return {
                    "latitude": city["latitude"],
                    "longitude": city["longitude"]
                }
        return None
