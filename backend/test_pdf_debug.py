#!/usr/bin/env python3
"""
PDF Generation Debug Protocol
Tests the entire PDF generation pipeline step by step
"""
import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
from io import BytesIO
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.services.map_service import MapService
from app.services.pdf_generator import PDFGenerator

# Test configuration
TEST_LAT = 51.8133  # Grote Kerk Dordrecht
TEST_LNG = 4.6601
OUTPUT_DIR = Path("output/debug")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Test pages with different layers
TEST_PAGES = [
    {"layer_id": "top10nl", "title": "TOP10NL", "scale": 2500},
    {"layer_id": "luchtfoto-actueel", "title": "Luchtfoto", "scale": 2500},
    {"layer_id": "kadastrale-kaart", "title": "Kadaster", "scale": 1000},
    {"layer_id": "bag-panden", "title": "BAG Panden", "scale": 1000},
    {"layer_id": "bestemmingsplan", "title": "Bestemmingsplan", "scale": 2500},
    {"layer_id": "ahn-dsm", "title": "AHN Hoogte", "scale": 1000},
    {"layer_id": "bodemkaart", "title": "Bodem", "scale": 5000},
]


async def test_step1_wms_direct():
    """Step 1: Test WMS services directly with httpx"""
    print("\n" + "=" * 80)
    print("STEP 1: Direct WMS Testing")
    print("=" * 80)

    results = []

    # Test bbox in RD coordinates (around Dordrecht)
    bbox = "108500,423500,109500,424500"

    async with httpx.AsyncClient(timeout=30.0) as client:
        test_configs = [
            ("top10nl", "https://service.pdok.nl/brt/top10nl/wms/v1_0", "top10nl"),
            ("luchtfoto", "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0", "Actueel_orthoHR"),
            ("kadaster", "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0", "Perceel"),
            ("bag", "https://service.pdok.nl/lv/bag/wms/v2_0", "pand"),
            ("ahn", "https://service.pdok.nl/rws/ahn/wms/v1_0", "dsm_05m"),
        ]

        for name, url, layer in test_configs:
            params = {
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:28992",
                "BBOX": bbox,
                "WIDTH": 800,
                "HEIGHT": 800,
                "FORMAT": "image/png",
                "TRANSPARENT": "true",
                "STYLES": ""
            }

            try:
                response = await client.get(url, params=params)
                content_type = response.headers.get("content-type", "")

                if response.status_code == 200 and "image" in content_type:
                    # Save the image
                    img_path = OUTPUT_DIR / f"step1_{name}.png"
                    with open(img_path, "wb") as f:
                        f.write(response.content)

                    status = f"OK - {len(response.content)} bytes -> {img_path}"
                    results.append((name, "OK", img_path))
                else:
                    status = f"ERROR - {response.status_code} - {content_type}"
                    results.append((name, "ERROR", response.text[:200]))

            except Exception as e:
                status = f"EXCEPTION - {type(e).__name__}: {e}"
                results.append((name, "EXCEPTION", str(e)))

            print(f"  {name}: {status}")

    return results


async def test_step2_map_service():
    """Step 2: Test MapService class"""
    print("\n" + "=" * 80)
    print("STEP 2: MapService Testing")
    print("=" * 80)

    map_service = MapService()
    results = []

    for page in TEST_PAGES:
        layer_id = page["layer_id"]
        print(f"\n  Testing layer: {layer_id}")

        try:
            image_bytes = await map_service.get_map_image(
                layer_id=layer_id,
                lat=TEST_LAT,
                lng=TEST_LNG,
                scale=page["scale"],
                width=1600,
                height=1131
            )

            if image_bytes:
                # Verify it's a valid image
                img = Image.open(BytesIO(image_bytes))
                img_path = OUTPUT_DIR / f"step2_{layer_id}.png"
                img.save(img_path)
                print(f"    OK - {len(image_bytes)} bytes, size={img.size} -> {img_path}")
                results.append((layer_id, "OK", img_path, len(image_bytes)))
            else:
                print(f"    ERROR - get_map_image returned None")
                results.append((layer_id, "ERROR", "None returned", 0))

        except Exception as e:
            print(f"    EXCEPTION - {type(e).__name__}: {e}")
            results.append((layer_id, "EXCEPTION", str(e), 0))

    await map_service.close()
    return results


async def test_step3_pdf_generator():
    """Step 3: Test PDF generation with pre-loaded images"""
    print("\n" + "=" * 80)
    print("STEP 3: PDF Generator Testing")
    print("=" * 80)

    map_service = MapService()
    pdf_generator = PDFGenerator(paper_size="A3", orientation="landscape")

    for i, page in enumerate(TEST_PAGES[:5]):  # Test first 5 pages
        layer_id = page["layer_id"]
        print(f"\n  Generating page {i+1}: {layer_id}")

        try:
            image_bytes = await map_service.get_map_image(
                layer_id=layer_id,
                lat=TEST_LAT,
                lng=TEST_LNG,
                scale=page["scale"]
            )

            if image_bytes:
                print(f"    Image: {len(image_bytes)} bytes")
            else:
                print(f"    Image: None (will use placeholder)")

            pdf_generator.add_page(
                title=page["title"],
                subtitle=f"Layer: {layer_id}",
                map_image=image_bytes,
                location={
                    "address": "Grote Kerk, Dordrecht",
                    "municipality": "Dordrecht",
                    "lat": TEST_LAT,
                    "lng": TEST_LNG
                },
                scale=page["scale"],
                page_number=i + 1,
                total_pages=5
            )
            print(f"    Page added to PDF")

        except Exception as e:
            print(f"    EXCEPTION: {type(e).__name__}: {e}")

    # Save PDF
    pdf_path = OUTPUT_DIR / f"step3_test_{datetime.now().strftime('%H%M%S')}.pdf"
    pdf_generator.save(pdf_path.name)
    print(f"\n  PDF saved to: output/{pdf_path.name}")

    await map_service.close()
    return pdf_path


async def test_step4_api_endpoint():
    """Step 4: Test the API endpoint directly"""
    print("\n" + "=" * 80)
    print("STEP 4: API Endpoint Testing")
    print("=" * 80)

    request_data = {
        "location": {
            "lat": TEST_LAT,
            "lng": TEST_LNG,
            "address": "Grote Kerk, Dordrecht",
            "municipality": "Dordrecht"
        },
        "paper_size": "A3",
        "orientation": "landscape",
        "pages": TEST_PAGES[:5]
    }

    print(f"  Request: {json.dumps(request_data, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8000/api/reports/generate-direct",
                json=request_data
            )

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "application/pdf" in content_type:
                    pdf_path = OUTPUT_DIR / f"step4_api_{datetime.now().strftime('%H%M%S')}.pdf"
                    with open(pdf_path, "wb") as f:
                        f.write(response.content)
                    print(f"  OK - PDF received: {len(response.content)} bytes -> {pdf_path}")
                    return ("OK", pdf_path)
                else:
                    print(f"  ERROR - Wrong content type: {content_type}")
                    return ("ERROR", content_type)
            else:
                print(f"  ERROR - HTTP {response.status_code}: {response.text[:500]}")
                return ("ERROR", response.text[:500])

    except Exception as e:
        print(f"  EXCEPTION - {type(e).__name__}: {e}")
        return ("EXCEPTION", str(e))


async def main():
    print("=" * 80)
    print(f"PDF GENERATION DEBUG PROTOCOL")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Location: {TEST_LAT}, {TEST_LNG} (Grote Kerk Dordrecht)")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 80)

    # Run all test steps
    step1_results = await test_step1_wms_direct()
    step2_results = await test_step2_map_service()
    step3_result = await test_step3_pdf_generator()
    step4_result = await test_step4_api_endpoint()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\nStep 1 - Direct WMS:")
    for name, status, detail in step1_results:
        print(f"  {name}: {status}")

    print("\nStep 2 - MapService:")
    for layer_id, status, detail, size in step2_results:
        print(f"  {layer_id}: {status} ({size} bytes)")

    print(f"\nStep 3 - PDF Generator: {step3_result}")
    print(f"\nStep 4 - API Endpoint: {step4_result[0]}")

    print("\n" + "=" * 80)
    print(f"Debug files saved to: {OUTPUT_DIR}")
    print("Check the PNG files to verify each layer is different.")
    print("Check the PDF files to verify pages have different content.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
