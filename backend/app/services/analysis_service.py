"""
Analysis Service - Fetch statistics and analysis data for locations
Uses CBS, BAG, and other Dutch open data sources
"""
import httpx
from typing import Optional, Dict, List
import math


class AnalysisService:
    """Service for fetching location statistics and analysis data"""

    # CBS WFS endpoint (2024 version)
    CBS_WFS_URL = "https://service.pdok.nl/cbs/wijkenbuurten/2024/wfs/v1_0"

    # BAG WFS endpoint
    BAG_WFS_URL = "https://service.pdok.nl/lv/bag/wfs/v2_0"

    # BRK Kadaster endpoint
    KADASTER_WFS_URL = "https://service.pdok.nl/kadaster/kadastralekaart/wfs/v5_0"

    def __init__(self):
        self.client = None

    async def _get_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client

    def wgs84_to_rd(self, lat: float, lng: float) -> tuple:
        """Convert WGS84 to RD coordinates"""
        ref_lat = 52.15517440
        ref_lng = 5.38720621
        ref_x = 155000
        ref_y = 463000

        # Polynomial coefficients
        Rp = [
            [0, 1, 190094.945], [1, 1, -11832.228], [2, 1, -114.221],
            [0, 3, -32.391], [1, 0, -0.705], [3, 1, -2.340],
            [1, 3, -0.608], [0, 2, -0.008], [2, 3, 0.148]
        ]
        Rq = [
            [1, 0, 309056.544], [0, 2, 3638.893], [2, 0, 73.077],
            [1, 2, -157.984], [3, 0, 59.788], [0, 1, 0.433],
            [2, 2, -6.439], [1, 1, -0.032], [0, 4, 0.092], [1, 4, -0.054]
        ]

        dPhi = 0.36 * (lat - ref_lat)
        dLam = 0.36 * (lng - ref_lng)

        x = sum(coef * (dPhi ** p) * (dLam ** q) for p, q, coef in Rp)
        y = sum(coef * (dPhi ** p) * (dLam ** q) for p, q, coef in Rq)

        return (ref_x + x, ref_y + y)

    async def get_location_analysis(
        self,
        lat: float,
        lng: float,
        radius: float = 500
    ) -> Dict:
        """
        Get comprehensive analysis data for a location

        Args:
            lat: Latitude (WGS84)
            lng: Longitude (WGS84)
            radius: Search radius in meters

        Returns:
            Dictionary with analysis data
        """
        rd_x, rd_y = self.wgs84_to_rd(lat, lng)

        # Calculate bounding box
        bbox = (
            rd_x - radius,
            rd_y - radius,
            rd_x + radius,
            rd_y + radius
        )

        # Fetch data from multiple sources in parallel
        results = {
            "location": {
                "lat": lat,
                "lng": lng,
                "rd_x": rd_x,
                "rd_y": rd_y,
                "radius": radius
            },
            "buildings": await self._get_building_stats(bbox),
            "parcels": await self._get_parcel_stats(bbox),
            "neighborhood": await self._get_neighborhood_stats(lat, lng),
            "summary": {}
        }

        # Generate summary
        results["summary"] = self._generate_summary(results)

        return results

    async def _get_building_stats(self, bbox: tuple) -> Dict:
        """Get building statistics from BAG"""
        client = await self._get_client()

        try:
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": "bag:pand",
                "outputFormat": "application/json",
                "srsName": "EPSG:28992",
                "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:28992"
            }

            response = await client.get(self.BAG_WFS_URL, params=params)

            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])

                # Analyze buildings
                building_count = len(features)
                building_years = []
                building_statuses = {}

                for feature in features:
                    props = feature.get("properties", {})

                    # Get building year
                    year = props.get("bouwjaar")
                    if year and str(year).isdigit():
                        building_years.append(int(year))

                    # Count statuses
                    status = props.get("status", "Onbekend")
                    building_statuses[status] = building_statuses.get(status, 0) + 1

                # Calculate statistics
                avg_year = sum(building_years) / len(building_years) if building_years else None
                oldest = min(building_years) if building_years else None
                newest = max(building_years) if building_years else None

                # Age distribution
                age_distribution = {"voor_1900": 0, "1900_1945": 0, "1945_1975": 0, "1975_2000": 0, "na_2000": 0}
                for year in building_years:
                    if year < 1900:
                        age_distribution["voor_1900"] += 1
                    elif year < 1945:
                        age_distribution["1900_1945"] += 1
                    elif year < 1975:
                        age_distribution["1945_1975"] += 1
                    elif year < 2000:
                        age_distribution["1975_2000"] += 1
                    else:
                        age_distribution["na_2000"] += 1

                return {
                    "count": building_count,
                    "average_year": round(avg_year) if avg_year else None,
                    "oldest_building": oldest,
                    "newest_building": newest,
                    "age_distribution": age_distribution,
                    "status_distribution": building_statuses
                }

            return {"count": 0, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"[Analysis] Error fetching building stats: {e}")
            return {"count": 0, "error": str(e)}

    async def _get_parcel_stats(self, bbox: tuple) -> Dict:
        """Get parcel statistics from Kadaster"""
        client = await self._get_client()

        try:
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": "kadastralekaart:Perceel",
                "outputFormat": "application/json",
                "srsName": "EPSG:28992",
                "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:28992"
            }

            response = await client.get(self.KADASTER_WFS_URL, params=params)

            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])

                parcel_count = len(features)
                total_area = 0
                parcels_by_municipality = {}

                for feature in features:
                    props = feature.get("properties", {})
                    geometry = feature.get("geometry", {})

                    # Get area (approximate from bbox if not provided)
                    area = props.get("oppervlakte", 0)
                    if area:
                        total_area += area

                    # Count by municipality
                    gemeente = props.get("kadastraleGemeenteCode", "Onbekend")
                    parcels_by_municipality[gemeente] = parcels_by_municipality.get(gemeente, 0) + 1

                return {
                    "count": parcel_count,
                    "total_area_m2": total_area,
                    "total_area_ha": round(total_area / 10000, 2) if total_area else 0,
                    "by_municipality": parcels_by_municipality
                }

            return {"count": 0, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"[Analysis] Error fetching parcel stats: {e}")
            return {"count": 0, "error": str(e)}

    async def _get_neighborhood_stats(self, lat: float, lng: float) -> Dict:
        """Get neighborhood statistics from CBS"""
        client = await self._get_client()
        rd_x, rd_y = self.wgs84_to_rd(lat, lng)

        try:
            # Find the neighborhood (buurt) containing this point
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": "wijkenbuurten:buurten",
                "outputFormat": "application/json",
                "srsName": "EPSG:28992",
                "bbox": f"{rd_x-100},{rd_y-100},{rd_x+100},{rd_y+100},EPSG:28992",
                "count": "1"
            }

            response = await client.get(self.CBS_WFS_URL, params=params)

            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])

                if features:
                    props = features[0].get("properties", {})

                    # Helper to clean CBS null values (-99995, -99997)
                    def clean_val(val):
                        if val is None or val in [-99995, -99997, -99995.0, -99997.0]:
                            return None
                        return val

                    return {
                        "buurt_code": props.get("buurtcode", "-"),
                        "buurt_naam": props.get("buurtnaam", "-"),
                        "wijk_code": props.get("wijkcode", "-"),
                        "gemeente_naam": props.get("gemeentenaam", "-"),
                        "gemeente_code": props.get("gemeentecode", "-"),
                        "inwoners": clean_val(props.get("aantalInwoners")),
                        "huishoudens": clean_val(props.get("aantalHuishoudens")),
                        "woningen": clean_val(props.get("woningvoorraad")),
                        "oppervlakte_ha": clean_val(props.get("oppervlakteLandInHa")),
                        "stedelijkheid": clean_val(props.get("stedelijkheidAdressenPerKm2")),
                        "bevolkingsdichtheid": clean_val(props.get("bevolkingsdichtheidInwonersPerKm2")),
                        "gem_woningwaarde": clean_val(props.get("gemiddeldeWoningwaarde")),
                        "koopwoningen_pct": clean_val(props.get("percentageKoopwoningen")),
                        "huurwoningen_pct": clean_val(props.get("percentageHuurwoningen")),
                        "gem_inkomen": clean_val(props.get("gemiddeldInkomenPerInwoner")),
                    }

            return {"error": "Geen buurt gevonden"}

        except Exception as e:
            print(f"[Analysis] Error fetching neighborhood stats: {e}")
            return {"error": str(e)}

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate a summary of the analysis"""
        buildings = results.get("buildings", {})
        parcels = results.get("parcels", {})
        neighborhood = results.get("neighborhood", {})

        summary = {
            "totaal_panden": buildings.get("count", 0),
            "totaal_percelen": parcels.get("count", 0),
            "gemiddeld_bouwjaar": buildings.get("average_year"),
            "oudste_pand": buildings.get("oldest_building"),
            "nieuwste_pand": buildings.get("newest_building"),
            "buurt": neighborhood.get("buurt_naam", "-"),
            "gemeente": neighborhood.get("gemeente_naam", "-"),
            "inwoners_buurt": neighborhood.get("inwoners"),
            "woningen_buurt": neighborhood.get("woningen"),
            "gem_woningwaarde": neighborhood.get("gem_woningwaarde"),
            "gem_inkomen": neighborhood.get("gem_inkomen"),
        }

        # Generate text summary
        text_parts = []

        if buildings.get("count"):
            text_parts.append(f"{buildings['count']} panden gevonden")
            if buildings.get("average_year"):
                text_parts.append(f"gemiddeld bouwjaar {buildings['average_year']}")

        if parcels.get("count"):
            text_parts.append(f"{parcels['count']} kadastrale percelen")
            if parcels.get("total_area_ha"):
                text_parts.append(f"totaal {parcels['total_area_ha']} ha")

        if neighborhood.get("buurt_naam") and neighborhood.get("buurt_naam") != "-":
            text_parts.append(f"in buurt {neighborhood['buurt_naam']}")

        summary["beschrijving"] = ", ".join(text_parts) if text_parts else "Geen data beschikbaar"

        return summary

    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None


async def get_location_analysis(lat: float, lng: float, radius: float = 500) -> Dict:
    """
    Convenience function to get location analysis

    Args:
        lat: Latitude (WGS84)
        lng: Longitude (WGS84)
        radius: Search radius in meters

    Returns:
        Dictionary with comprehensive analysis data
    """
    service = AnalysisService()
    try:
        return await service.get_location_analysis(lat, lng, radius)
    finally:
        await service.close()
