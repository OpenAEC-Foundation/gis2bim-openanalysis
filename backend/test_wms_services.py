#!/usr/bin/env python3
"""
WMS Services Test Protocol
Tests all configured WMS layers and reports their status
"""
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Test location: Grote Kerk Dordrecht (EPSG:28992 coordinates)
TEST_BBOX = "109000,424000,110000,425000"  # Around Dordrecht center
TEST_WIDTH = 800
TEST_HEIGHT = 800

# All WMS layer configurations - must match map_service.py
LAYERS: Dict[str, dict] = {
    # === BASISKAARTEN ===
    "top10nl": {
        "type": "WMS",
        "url": "https://service.pdok.nl/brt/top10nl/wms/v1_0",
        "layer": "top10nl",
    },

    # === KADASTER & BAG ===
    "kadastrale-kaart": {
        "type": "WMS",
        "url": "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0",
        "layer": "Perceel",
    },
    "bag-panden": {
        "type": "WMS",
        "url": "https://service.pdok.nl/lv/bag/wms/v2_0",
        "layer": "pand",
    },
    "bgt-gebouwen": {
        "type": "WMS",
        "url": "https://service.pdok.nl/lv/bgt/wms/v1_0",
        "layer": "pand",
    },

    # === LUCHTFOTO'S ===
    "luchtfoto-actueel": {
        "type": "WMS",
        "url": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
        "layer": "Actueel_orthoHR",
    },
    "luchtfoto-2023": {
        "type": "WMS",
        "url": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
        "layer": "2023_orthoHR",
    },
    "luchtfoto-2022": {
        "type": "WMS",
        "url": "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
        "layer": "2022_orthoHR",
    },

    # === HOOGTE (AHN) ===
    "ahn-dsm": {
        "type": "WMS",
        "url": "https://service.pdok.nl/rws/ahn/wms/v1_0",
        "layer": "dsm_05m",
    },
    "ahn-dtm": {
        "type": "WMS",
        "url": "https://service.pdok.nl/rws/ahn/wms/v1_0",
        "layer": "dtm_05m",
    },

    # === RUIMTELIJKE PLANNEN ===
    "bestemmingsplan": {
        "type": "WMS",
        "url": "https://service.pdok.nl/kadaster/plu/wms/v1_0",
        "layer": "enkelbestemming",
    },
    "dubbelbestemming": {
        "type": "WMS",
        "url": "https://service.pdok.nl/kadaster/plu/wms/v1_0",
        "layer": "dubbelbestemming",
    },
    "bouwvlak": {
        "type": "WMS",
        "url": "https://service.pdok.nl/kadaster/plu/wms/v1_0",
        "layer": "bouwvlak",
    },

    # === BODEM ===
    "bodemkaart": {
        "type": "WMS",
        "url": "https://service.pdok.nl/bzk/bro-bodemkaart/wms/v1_0",
        "layer": "soilarea",
    },

    # === BESTUURLIJKE GRENZEN ===
    "gemeentegrenzen": {
        "type": "WMS",
        "url": "https://service.pdok.nl/kadaster/bestuurlijkegebieden/wms/v1_0",
        "layer": "Gemeentegebied",
    },
    "provinciegrenzen": {
        "type": "WMS",
        "url": "https://service.pdok.nl/kadaster/bestuurlijkegebieden/wms/v1_0",
        "layer": "Provinciegebied",
    },

    # === NATUUR ===
    "natura2000": {
        "type": "WMS",
        "url": "https://service.pdok.nl/rvo/natura2000/wms/v1_0",
        "layer": "natura2000",
    },

    # === CULTUURHISTORIE ===
    "rijksmonumenten": {
        "type": "WMS",
        "url": "https://service.pdok.nl/rce/rijksmonumenten/wms/v1_0",
        "layer": "rijksmonumenten_punt",
    },

    # === CBS STATISTIEK ===
    "cbs-buurten": {
        "type": "WMS",
        "url": "https://service.pdok.nl/cbs/wijkenbuurten/wms/v1_0",
        "layer": "cbs_buurten_2023",
    },
    "cbs-wijken": {
        "type": "WMS",
        "url": "https://service.pdok.nl/cbs/wijkenbuurten/wms/v1_0",
        "layer": "cbs_wijken_2023",
    },
}


async def test_wms_layer(client: httpx.AsyncClient, layer_id: str, config: dict) -> Tuple[str, str, str, int]:
    """Test a single WMS layer and return status"""
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": config["layer"],
        "CRS": "EPSG:28992",
        "BBOX": TEST_BBOX,
        "WIDTH": TEST_WIDTH,
        "HEIGHT": TEST_HEIGHT,
        "FORMAT": "image/png",
        "TRANSPARENT": "true",
        "STYLES": ""
    }

    try:
        response = await client.get(config["url"], params=params, timeout=30.0)
        content_type = response.headers.get("content-type", "")

        if response.status_code == 200:
            if "image" in content_type:
                # Check if image has actual content (not just transparent)
                size = len(response.content)
                if size > 1000:
                    return (layer_id, "OK", f"{content_type} ({size} bytes)", size)
                else:
                    return (layer_id, "EMPTY", f"Image too small ({size} bytes)", size)
            else:
                # Likely an error message
                error_text = response.text[:200].replace('\n', ' ')
                return (layer_id, "ERROR", f"Non-image response: {error_text}", 0)
        else:
            return (layer_id, "HTTP_ERROR", f"Status {response.status_code}", 0)

    except httpx.TimeoutException:
        return (layer_id, "TIMEOUT", "Request timed out after 30s", 0)
    except Exception as e:
        return (layer_id, "EXCEPTION", f"{type(e).__name__}: {str(e)[:100]}", 0)


async def run_tests():
    """Run all WMS tests"""
    print("=" * 80)
    print(f"WMS Services Test Protocol - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"Test Location: Grote Kerk Dordrecht (BBOX: {TEST_BBOX})")
    print(f"Image Size: {TEST_WIDTH}x{TEST_HEIGHT}")
    print("=" * 80)
    print()

    results: List[Tuple[str, str, str, int]] = []

    async with httpx.AsyncClient() as client:
        # Test all layers
        for layer_id, config in LAYERS.items():
            print(f"Testing: {layer_id}...", end=" ", flush=True)
            result = await test_wms_layer(client, layer_id, config)
            results.append(result)

            status_icon = "✓" if result[1] == "OK" else "✗" if result[1] in ["ERROR", "HTTP_ERROR", "EXCEPTION"] else "○"
            print(f"{status_icon} {result[1]}")

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    ok_count = sum(1 for r in results if r[1] == "OK")
    empty_count = sum(1 for r in results if r[1] == "EMPTY")
    error_count = sum(1 for r in results if r[1] in ["ERROR", "HTTP_ERROR", "EXCEPTION", "TIMEOUT"])

    print(f"Total layers tested: {len(results)}")
    print(f"  ✓ Working (OK):     {ok_count}")
    print(f"  ○ Empty response:   {empty_count}")
    print(f"  ✗ Errors:           {error_count}")
    print()

    # Detailed results table
    print("DETAILED RESULTS:")
    print("-" * 80)
    print(f"{'Layer ID':<25} {'Status':<12} {'Details'}")
    print("-" * 80)

    for layer_id, status, details, size in sorted(results, key=lambda x: (x[1] != "OK", x[0])):
        if status == "OK":
            status_str = f"✓ {status}"
        elif status == "EMPTY":
            status_str = f"○ {status}"
        else:
            status_str = f"✗ {status}"

        print(f"{layer_id:<25} {status_str:<12} {details[:40]}")

    print("-" * 80)

    # List problematic layers
    if error_count > 0:
        print()
        print("PROBLEMATIC LAYERS (need attention):")
        for layer_id, status, details, _ in results:
            if status in ["ERROR", "HTTP_ERROR", "EXCEPTION", "TIMEOUT"]:
                config = LAYERS[layer_id]
                print(f"  - {layer_id}")
                print(f"    URL: {config['url']}")
                print(f"    Layer: {config['layer']}")
                print(f"    Error: {details}")
                print()

    print()
    return results


if __name__ == "__main__":
    results = asyncio.run(run_tests())

    # Exit with error code if there are failures
    error_count = sum(1 for r in results if r[1] in ["ERROR", "HTTP_ERROR", "EXCEPTION", "TIMEOUT"])
    sys.exit(1 if error_count > 0 else 0)
